"""Shared SSE (Server-Sent Events) line-parsing utilities.

Both sync and async variants yield the raw ``data:`` content for each SSE line,
with the ``data:`` prefix stripped and empty / comment lines skipped.

Callers are responsible for JSON-decoding the yielded strings.
"""

from __future__ import annotations

from typing import AsyncGenerator, Generator

import httpx


def iter_sse_lines(response: httpx.Response) -> Generator[str, None, None]:
    """Yield SSE data lines from a *synchronous* streaming httpx response.

    Strips the ``data:`` prefix, skips empty lines and SSE comment lines
    (those starting with ``:``) and handles buffered partial lines.
    """
    buf = ""
    for raw in response.iter_text():
        buf += raw
        while "\n" in buf:
            line, buf = buf.split("\n", 1)
            line = line.strip()
            if not line or line.startswith(":"):
                continue
            if line.startswith("data: "):
                yield line[6:]
            elif line.startswith("data:"):
                yield line[5:]
    # Flush any remaining data not terminated by a newline
    if buf.strip():
        line = buf.strip()
        if line.startswith("data: "):
            yield line[6:]
        elif line.startswith("data:"):
            yield line[5:]


async def aiter_sse_lines(response: httpx.Response) -> AsyncGenerator[str, None]:
    """Yield SSE data lines from an *async* streaming httpx response.

    Mirrors :func:`iter_sse_lines` but uses ``aiter_text()`` for async iteration.
    """
    buf = ""
    async for raw in response.aiter_text():
        buf += raw
        while "\n" in buf:
            line, buf = buf.split("\n", 1)
            line = line.strip()
            if not line or line.startswith(":"):
                continue
            if line.startswith("data: "):
                yield line[6:]
            elif line.startswith("data:"):
                yield line[5:]
    # Flush any remaining data not terminated by a newline
    if buf.strip():
        line = buf.strip()
        if line.startswith("data: "):
            yield line[6:]
        elif line.startswith("data:"):
            yield line[5:]
