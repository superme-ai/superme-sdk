"""Shared SSE / NDJSON line-parsing utilities.

Both sync and async variants yield the raw content for each event line.
For SSE streams the ``data:`` prefix is stripped; bare JSON lines (NDJSON,
i.e. lines starting with ``{``) are yielded as-is.  Empty lines and SSE
comment/meta lines (``:``, ``event:``, ``id:``, ``retry:``) are skipped.

Callers are responsible for JSON-decoding the yielded strings.
"""

from __future__ import annotations

from typing import AsyncGenerator, Generator

import httpx


def _yield_line(line: str) -> str | None:
    """Return the payload to yield for a single SSE/NDJSON line, or None to skip."""
    if not line or line.startswith(":"):
        return None
    if line.startswith("data: "):
        return line[6:]
    if line.startswith("data:"):
        return line[5:]
    if line.startswith("{"):
        return line  # bare NDJSON object
    return None


def iter_sse_lines(response: httpx.Response) -> Generator[str, None, None]:
    """Yield event payloads from a *synchronous* streaming httpx response.

    Handles both SSE (``data: {json}\\n\\n``) and NDJSON (``{json}\\n``) formats.
    """
    buf = ""
    for raw in response.iter_text():
        buf += raw
        while "\n" in buf:
            line, buf = buf.split("\n", 1)
            payload = _yield_line(line.strip())
            if payload is not None:
                yield payload
    if buf.strip():
        payload = _yield_line(buf.strip())
        if payload is not None:
            yield payload


async def aiter_sse_lines(response: httpx.Response) -> AsyncGenerator[str, None]:
    """Yield event payloads from an *async* streaming httpx response.

    Mirrors :func:`iter_sse_lines` but uses ``aiter_text()`` for async iteration.
    """
    buf = ""
    async for raw in response.aiter_text():
        buf += raw
        while "\n" in buf:
            line, buf = buf.split("\n", 1)
            payload = _yield_line(line.strip())
            if payload is not None:
                yield payload
    if buf.strip():
        payload = _yield_line(buf.strip())
        if payload is not None:
            yield payload
