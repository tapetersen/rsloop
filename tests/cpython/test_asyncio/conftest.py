"""Collection policy for the vendored asyncio tests.

``collect_ignore`` is the conscious opt-out list: files here are excluded from
collection entirely, without touching the vendored sources. Use it for tests that
exercise asyncio's *own* event-loop implementations (selector/proactor/unix/windows
loops, event-loop internals) -- those are tied to CPython's loop and aren't
meaningful against rsloop's.

Anything not listed here that still fails to import (e.g. missing ``test.support``
symbols) is turned into a visible skip by the module-collection hook in the parent
``tests/cpython/conftest.py`` -- so the run reaches the test phase and the import
error shows up as the skip reason (via ``-rs``).

Note: test_windows_events / test_windows_utils self-skip via unittest.SkipTest on
non-Windows, so they don't need listing here.
"""

collect_ignore = [
    "test_events.py",
    "test_base_events.py",
    "test_selector_events.py",
    "test_proactor_events.py",
    "test_unix_events.py",
]
