set shell := ["bash", "-euo", "pipefail", "-c"]

tls-test-certs outdir="tests/fixtures/tls":
    ./scripts/generate-test-tls-certs.sh {{outdir}}

fmt:
    uv run ruff format .
    cargo fmt --all

test: tls-test-certs
    uv run python -m unittest discover -s tests

test-frameworks:
    uv run --with uvicorn python tests/packages/uvicorn_test.py
    uv run --with fastapi --with uvicorn python tests/packages/fastapi_test.py
    uv run --with sanic python tests/packages/sanic_test.py
    uv run --with 'faststream[nats]' python tests/packages/faststream_test.py
    uv run --with litestar --with granian python tests/packages/litestar_granian_test.py
