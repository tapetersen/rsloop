from __future__ import annotations

import asyncio
import socket
from typing import Any

import rsloop
import uvicorn


async def app(scope: dict[str, Any], receive: Any, send: Any) -> None:
    if scope["type"] == "lifespan":
        while True:
            message = await receive()
            if message["type"] == "lifespan.startup":
                await send({"type": "lifespan.startup.complete"})
            elif message["type"] == "lifespan.shutdown":
                await send({"type": "lifespan.shutdown.complete"})
                return

    assert scope["type"] == "http"
    await send(
        {
            "type": "http.response.start",
            "status": 200,
            "headers": [(b"content-type", b"text/plain")],
        }
    )
    await send({"type": "http.response.body", "body": b"uvicorn-rsloop"})


def reserve_port() -> int:
    sock = socket.socket()
    try:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])
    finally:
        sock.close()


async def get(path: str, port: int) -> bytes:
    reader, writer = await asyncio.open_connection("127.0.0.1", port)
    try:
        writer.write(
            (
                f"GET {path} HTTP/1.1\r\n"
                f"Host: 127.0.0.1:{port}\r\n"
                "Connection: close\r\n\r\n"
            ).encode()
        )
        await writer.drain()
        return await reader.read()
    finally:
        writer.close()
        await writer.wait_closed()


async def wait_started(server: uvicorn.Server) -> None:
    for _ in range(100):
        if server.started:
            return
        await asyncio.sleep(0.05)
    raise RuntimeError("uvicorn server did not start")


async def main() -> None:
    port = reserve_port()
    server = uvicorn.Server(
        uvicorn.Config(
            app,
            host="127.0.0.1",
            port=port,
            loop="none",
            lifespan="on",
            log_level="warning",
            access_log=False,
        )
    )

    task = asyncio.create_task(server.serve())
    try:
        await wait_started(server)
        response = await get("/", port)
        assert b"uvicorn-rsloop" in response, response
        print("uvicorn ok")
    finally:
        server.should_exit = True
        await task


if __name__ == "__main__":
    rsloop.run(main())
