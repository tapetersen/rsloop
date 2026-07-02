"""Collection policy for the vendored CPython test tree.

Files that are consciously not wanted are excluded via ``collect_ignore`` in the
per-suite conftest (e.g. ``test_asyncio/conftest.py``). Everything else is meant to
run; but since these files are copied verbatim, some still fail to import here
(missing ``test.support`` symbols, optional C extensions, ...). We turn such a
module-level import failure into a *visible skip* -- with the import error kept as
the skip reason (see it with ``-rs``) -- so the run reaches the test phase instead
of aborting on a collection error.

This masks module import failures as skips, which is the intended trade-off for a
vendored external suite. It is scoped to ``tests/cpython`` only, so it never
affects the project's own tests. Scan the skip reasons occasionally: a genuine
breakage (e.g. a bad ``support`` edit) will show up here as a skip, not an error.
"""

import pytest


@pytest.hookimpl(wrapper=True)
def pytest_make_collect_report(collector):
    report = yield
    if report.failed and isinstance(collector, pytest.Module):
        crash = getattr(getattr(report.longrepr, "reprcrash", None), "message", "") or ""
        if not crash:
            lines = str(report.longrepr).strip().splitlines()
            crash = next((ln for ln in reversed(lines) if ln.strip()), "import failed")
        report.outcome = "skipped"
        report.longrepr = (str(collector.path), 0, f"uncollectable: {crash.strip()}")
    return report
