"""Vendored subset of CPython's ``Lib/test`` tree, run against rsloop.

The vendored files use absolute imports (``from test import support``,
``from test.support import socket_helper``, ``from test.test_asyncio import
utils``) and some even assert their own dotted name (``support`` refuses to load
unless it is called ``test.support``). But pytest imports this tree under its real
on-disk location (``cpython`` here), not ``test``.

To bridge that without a fake ``sys.modules['test']`` shim, we install a meta-path
finder that makes the ``test`` package name load *these* files: ``test`` becomes an
empty package whose search path is this directory, and every ``test.X`` is loaded
fresh from the corresponding vendored file under its real ``test.X`` name (so
self-name guards pass). Fully self-contained -- no stdlib ``test`` fall-through --
and lazy, so no eager import or teardown is needed.
"""

import importlib
import importlib.abc
import importlib.machinery
import importlib.util
import sys

_ALIAS = "test"          # the name the vendored files import from
_ROOT = list(__path__)   # this package's directory (CPython's "Lib/test")


class _TestTreeLoader(importlib.abc.Loader):
    """Loader for the synthetic ``test`` root package (empty body, real __path__)."""

    def create_module(self, spec):
        return None  # use default module creation

    def exec_module(self, module):
        pass  # body is empty; __path__ comes from the spec


class _TestTreeAliasFinder(importlib.abc.MetaPathFinder):
    """Redirect ``test`` / ``test.*`` imports onto this vendored directory."""

    def find_spec(self, fullname, path=None, target=None):
        if fullname == _ALIAS:
            spec = importlib.machinery.ModuleSpec(
                _ALIAS, _TestTreeLoader(), is_package=True
            )
            spec.submodule_search_locations = list(_ROOT)
            return spec
        if fullname.startswith(_ALIAS + "."):
            parent = importlib.import_module(fullname.rpartition(".")[0])
            return importlib.machinery.PathFinder.find_spec(
                fullname, parent.__path__
            )
        return None


if not any(isinstance(f, _TestTreeAliasFinder) for f in sys.meta_path):
    sys.meta_path.insert(0, _TestTreeAliasFinder())
