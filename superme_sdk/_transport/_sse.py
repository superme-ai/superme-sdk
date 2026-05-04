"""SSE (Server-Sent Events) line-parsing utilities.

Yields the raw ``data:`` payload for each SSE event line, stripping the
``data:`` prefix and skipping empty lines and comment/meta lines.

Used by endpoints that respond with ``text/event-stream`` (e.g. interview).
Callers are responsible for JSON-decoding the yielded strings.
"""

from __future__ import annotations

from typing import AsyncGenerator, Generator

import httpx


def iter_sse_lines(response: httpx.Response) -> Generator[str, None, None]:
    """Yield SSE data payloads from a *synchronous* streaming httpx response."""
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
    if buf.strip():
        line = buf.strip()
        if line.startswith("data: "):
            yield line[6:]
        elif line.startswith("data:"):
            yield line[5:]


async def aiter_sse_lines(response: httpx.Response) -> AsyncGenerator[str, None]:
    """Yield SSE data payloads from an *async* streaming httpx response."""
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
    if buf.strip():
        line = buf.strip()
        if line.startswith("data: "):
            yield line[6:]
        elif line.startswith("data:"):
            yield line[5:]
