# asyncio API compatibility gaps (working notes)

Findings from auditing rsloop's exposed surface against CPython's documented
`asyncio` interfaces (loop, transports, streams, server). The loop surface is
complete; the gaps are all on **returned objects**.

Each gap has a tracking test in `tests/test_compat.py`, marked
`@unittest.expectedFailure`. When a gap is fixed, remove the decorator (the test
will otherwise report an "unexpected success").

Method was verified empirically: `inspect.signature` diff of live rsloop objects
vs a CPython loop, plus the documented contracts in `../cpython/Lib/asyncio`.

## Out of scope (already intentional)

Documented limitations in `README.md` / `docs/how-it-works.md` — narrower TLS,
encrypted keys, `preexec_fn`, Unix-only APIs. None of the gaps below overlap
these, so they are real divergences, not intentional ones.

## Gaps

### 1. StreamReader.readline() / readuntil() — High

- Default-on: `RSLOOP_USE_FAST_STREAMS=1` makes `asyncio.open_connection()` /
  `start_server()` return `PyFastStreamReader`, which has only `read()` /
  `readexactly()`. `reader.readline()` raises `AttributeError`.
- Code: `src/fast_streams.rs`, `PyFastStreamReader` (see `read` ~L514,
  `readexactly` ~L518, future builders `build_read_future` ~L371,
  `build_readexactly_future` ~L393).
- Fix sketch: add `readline()` (= `readuntil(b"\n")` swallowing the
  partial-line-at-EOF case) and `readuntil(separator=b"\n")` with the CPython
  semantics in `../cpython/Lib/asyncio/streams.py:541,572`: scan the buffer for
  the separator, enforce `limit` (raise `LimitOverrunError`), raise
  `IncompleteReadError` on EOF before the separator. The Python text wrapper
  `_TextStreamReader.readuntil` in `python/rsloop/_loop_compat.py:739` is a
  reference implementation of the separator-scan loop.
- Tests: `test_stream_reader_supports_readline`,
  `test_stream_reader_supports_readuntil`.

### 2. StreamWriter.start_tls() — Medium

- `PyFastStreamWriter` has no `start_tls()` (documented since 3.11,
  `../cpython/Lib/asyncio/streams.py:386`).
- Code: `src/fast_streams.rs`, `PyFastStreamWriter` (~L820).
- Fix sketch: mirror CPython — `await loop.start_tls(transport, protocol,
  sslcontext, ...)` (the loop method already exists,
  `src/python_api.rs:2353`) and swap in the returned transport.
- Test: `test_stream_writer_supports_start_tls`.

### 3. SubprocessTransport.get_extra_info / get_protocol / set_protocol — Medium

- `PyProcessTransport` lacks these `BaseTransport` methods; `get_extra_info` in
  particular is commonly used (e.g. `get_extra_info("subprocess")`).
- Code: `src/process_transport.rs`, `PyProcessTransport` (near `get_pid` /
  `get_returncode`). Note the sibling `get_extra_info` with the right signature
  on `PyProcessPipeTransport` at L663.
- Fix sketch: add `get_extra_info(name, default=None)` and store/return the
  protocol for `get_protocol` / `set_protocol`.
- Tests: `test_subprocess_transport_supports_get_extra_info`,
  `test_subprocess_transport_supports_protocol_accessors`.

### 4. Server.close_clients() / abort_clients() — Low

- Added in Python 3.13 (`../cpython/Lib/asyncio/events.py:211,215`). rsloop's
  `Server` has `close`, `is_serving`, `get_loop`, `start_serving`,
  `serve_forever`, `wait_closed`, `sockets`, but not these two.
- Code: `src/stream_transport.rs`, `PyServer`.
- Fix sketch: track live client transports and close/abort them.
- Test: `test_server_supports_close_and_abort_clients`.

### 5. Parameter names vs docs — Cosmetic

Positional calls work; only documented *keyword* calls fail.

- `WriteTransport.writelines(list_of_data)` — rsloop names it `seq`
  (`src/stream_transport.rs` `PyStreamTransport::writelines`; also the fast
  writer in `src/fast_streams.rs`).
- `SubprocessTransport.send_signal(signal)` — rsloop names it `sig`
  (`src/process_transport.rs`).
- Fix: rename params (add `#[pyo3(signature=...)]` if needed to keep them
  positional-or-keyword under the documented name).
- Tests: `test_writelines_accepts_documented_list_of_data_keyword`,
  `test_send_signal_accepts_documented_signal_keyword`.
