"""Minimal stand-in for ``test.support.threading_helper``.

``utils.TestCase`` snapshots threads in setUp and checks for leaks in tearDown.
We keep a best-effort, non-raising version: it gives lingering threads a short
grace period to exit but never fails a test on a late-joining thread.
"""

import threading
import time


def threading_setup():
    return (threading.active_count(),)


def threading_cleanup(*original):
    original_count = original[0]
    deadline = time.monotonic() + 1.0
    while threading.active_count() > original_count and time.monotonic() < deadline:
        time.sleep(0.01)
