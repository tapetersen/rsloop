"""Minimal stand-in for ``test.support.socket_helper``.

Only the surface the vendored asyncio tests actually touch. ``utils.py`` uses
``create_unix_domain_name`` (runtime, unix-socket paths only); ``HOST`` and
``find_unused_port`` are here for networking tests that may be enabled later.
"""

import socket
import tempfile

HOST = "localhost"


def create_unix_domain_name():
    return tempfile.mktemp(prefix="test_", suffix=".sock")


def find_unused_port(family=socket.AF_INET, socktype=socket.SOCK_STREAM):
    with socket.socket(family, socktype) as sock:
        sock.bind((HOST, 0))
        return sock.getsockname()[1]
