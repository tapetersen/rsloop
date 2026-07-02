"""Minimal stand-in for ``test.support.script_helper``.

Only ``assert_python_ok`` is used by the vendored tests: run the interpreter with
the given args (and optional environment overrides), assert it exited 0, and
return ``(returncode, stdout, stderr)`` with stdout/stderr as bytes.
"""

import os
import subprocess
import sys


def assert_python_ok(*args, **env_vars):
    env = os.environ.copy()
    for key, value in env_vars.items():
        env[key] = str(value)
    proc = subprocess.run(
        [sys.executable, *args],
        capture_output=True,
        env=env,
    )
    if proc.returncode != 0:
        raise AssertionError(
            f"Python process exited with {proc.returncode}\n"
            f"{proc.stderr.decode(errors='replace')}"
        )
    return proc.returncode, proc.stdout, proc.stderr
