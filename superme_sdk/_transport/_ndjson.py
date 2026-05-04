"""NDJSON (newline-delimited JSON) line-parsing utilities.

Yields raw JSON lines from ``application/x-ndjson`` streaming responses,
skipping empty lines and comment/meta lines (those starting with ``:``) .

Used by endpoints that stream bare JSON objects with no ``data:`` prefix
(e.g. ``/mcp/chat/stream``, ``/mcp/chat/stream/group_converse``).
Callers are responsible for JSON-decoding the yielded strings.
"""

from __future__ import annotations

from typing import AsyncGenerator, Generator

import httpx


def iter_ndjson_lines(response: httpx.Response) -> Generator[str, None, None]:
    """Yield raw JSON lines from a *synchronous* streaming NDJSON response."""
    buf = ""
    for raw in response.iter_text():
        buf += raw
        while "\n" in buf:
            line, buf = buf.split("\n", 1)
            line = line.strip()
            if not line or line.startswith(":"):
                continue
            yield line
    if buf.strip():
        line = buf.strip()
        if not line.startswith(":"):
            yield line


async def aiter_ndjson_lines(response: httpx.Response) -> AsyncGenerator[str, None]:
    """Yield raw JSON lines from an *async* streaming NDJSON response."""
    buf = ""
    async for raw in response.aiter_text():
        buf += raw
        while "\n" in buf:
            line, buf = buf.split("\n", 1)
            line = line.strip()
            if not line or line.startswith(":"):
                continue
            yield line
    if buf.strip():
        line = buf.strip()
        if not line.startswith(":"):
            yield line
