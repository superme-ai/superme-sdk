"""Conversation methods — async."""

from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable
from typing import Any, Literal, Optional, overload

from ..._transport._terminals import ASK_TERMINAL
from ...streaming import PartnerStreamChunk


class AsyncConversationsMixin:
    """Async variants of :class:`~superme_sdk.services._conversations.ConversationsMixin`.

    Non-streaming calls are awaitable (``await client.ask(...)``); streaming
    calls return an async generator (``async for chunk in client.ask(..., stream=True)``).
    A streaming generator holds an open SSE connection until a terminal event —
    if you stop early (``break``), call ``aclose()`` on it (or fully drain it)
    so the connection is released promptly rather than at GC time.

    Note: unlike the sync client, async non-streaming ``ask`` is served by the
    partner endpoint and does not support ``incognito`` / ``max_tokens``.
    """

    @overload
    def ask(
        self,
        question: str,
        username: str = ...,
        *,
        conversation_id: Optional[str] = ...,
        stream: Literal[False] = ...,
    ) -> Awaitable[str]: ...

    @overload
    def ask(
        self,
        question: str,
        username: str = ...,
        *,
        conversation_id: Optional[str] = ...,
        stream: Literal[True],
    ) -> AsyncIterator[PartnerStreamChunk]: ...

    def ask(
        self,
        question: str,
        username: str = "ludo",
        *,
        conversation_id: Optional[str] = None,
        stream: bool = False,
    ) -> Awaitable[str] | AsyncIterator[PartnerStreamChunk]:
        """Ask a single question to a user's SuperMe agent (async).

        Example:
            ```python
            answer = await client.ask("What is PMF?", username="ludo")

            async for chunk in client.ask("What is PMF?", username="ludo", stream=True):
                if chunk["type"] == "content":
                    print(chunk["text"], end="", flush=True)
            ```

        Returns:
            An awaitable resolving to the answer string, or — when
            ``stream=True`` — an async generator of SSE chunk dicts (``type``:
            ``content``/``tool``/``done``/``error``). ``incognito`` /
            ``max_tokens`` are not supported on the async path.
        """
        body: dict[str, Any] = {
            "identifier": username,
            "question": question,
            "stream": stream,
        }
        if conversation_id:
            body["conversation_id"] = conversation_id
        if stream:
            return self._aiter_sse(
                self._async_partner_http,
                "POST",
                "/partner/ask",
                json=body,
                is_terminal=lambda o: o.get("type") in ASK_TERMINAL,
            )
        return self._ask_nonstream(body)

    async def _ask_nonstream(self, body: dict) -> str:
        resp = await self._async_partner_http.post("/partner/ask", json=body)
        self._check_rest_response(resp)
        data = resp.json()
        return data.get("answer", "") if isinstance(data, dict) else ""
