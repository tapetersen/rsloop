"""Minimal stand-in for ``test.support.warnings_helper``.

Only ``ignore_warnings`` is used by the vendored asyncio tests: a decorator that
suppresses warnings of the given category for the duration of the wrapped test.
"""

import functools
import warnings


def ignore_warnings(*, category):
    def decorator(test):
        @functools.wraps(test)
        def wrapper(self, *args, **kwargs):
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", category=category)
                return test(self, *args, **kwargs)
        return wrapper
    return decorator
