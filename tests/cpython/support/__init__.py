"""Minimal stand-in for CPython's ``test.support``.

The vendored asyncio tests import ``test.support`` for a handful of timeout
constants and small helpers. We deliberately keep only the surface a loop-agnostic
subset actually exercises instead of vendoring the full 3k-line module; anything
missing surfaces as a clear AttributeError/ImportError to be added on demand.
"""

import contextlib
import functools
import gc
import os
import sys
import time
import unittest

# Timeout constants (CPython defaults). Individual tests/modules override these.
SHORT_TIMEOUT = 30.0
LONG_TIMEOUT = 300.0
LOOPBACK_TIMEOUT = 2.0

# Root of the vendored "test" tree; data_file() in utils.py joins onto this.
TEST_HOME_DIR = os.path.dirname(os.path.abspath(__file__))


def gc_collect():
    """Force a full collection; needed for tests asserting object cleanup."""
    for _ in range(3):
        gc.collect()


@contextlib.contextmanager
def disable_gc():
    was_enabled = gc.isenabled()
    gc.disable()
    try:
        yield
    finally:
        if was_enabled:
            gc.enable()


def busy_retry(timeout, err_msg=None, *, error=True):
    """Yield until ``timeout`` seconds elapse; raise (or stop) when it does."""
    deadline = time.monotonic() + timeout
    while time.monotonic() <= deadline:
        yield
    if error:
        raise TimeoutError(err_msg or f"timed out after {timeout}s")


def reap_children():
    """No-op: the loop-agnostic subset never forks child processes."""


def cpython_only(test):
    """Pass-through: the test interpreter is always CPython here."""
    return test


def get_attribute(obj, name):
    """Return ``obj.name``, or skip the test if it is missing.

    On a non-debug build ``sys.gettotalrefcount`` is absent, so refcount tests
    self-skip through this rather than erroring.
    """
    try:
        return getattr(obj, name)
    except AttributeError:
        raise unittest.SkipTest(f"object {obj!r} has no attribute {name!r}")


def refcount_test(test):
    """Run a refcount-sensitive test with tracing disabled (as CPython does)."""
    @functools.wraps(test)
    def wrapper(*args, **kwargs):
        original_trace = sys.gettrace()
        sys.settrace(None)
        try:
            return test(*args, **kwargs)
        finally:
            sys.settrace(original_trace)
    return wrapper
