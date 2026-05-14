from __future__ import annotations

import asyncio
import socket

import rsloop
import uvicorn
from fastapi import FastAPI


app = FastAPI()


@app.get("/")
async def index() -> dict[str, str]:
    loop = asyncio.get_running_loop()
    return {
        "ok": "fastapi-rsloop",
        "loop": f"{type(loop).__module__}.{type(loop).__name__}",
    }


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
    raise RuntimeError("FastAPI/Uvicorn server did not start")


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
        assert b"fastapi-rsloop" in response, response
        assert b"rsloop" in response, response
        print("fastapi ok")
    finally:
        server.should_exit = True
        await task


if __name__ == "__main__":
    rsloop.run(main())
