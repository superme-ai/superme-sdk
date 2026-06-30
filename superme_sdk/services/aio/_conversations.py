"""Conversation methods — async."""

from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable
from typing import Any, Optional

_ASK_TERMINAL = {"done", "error"}
_AGENT_TERMINAL = {"turn_completed", "turn_failed", "turn_interrupted"}


class AsyncConversationsMixin:
    """Async variants of :class:`~superme_sdk.services._conversations.ConversationsMixin`.

    Non-streaming calls are awaitable (``await client.ask(...)``); streaming
    calls return an async generator (``async for chunk in client.ask(..., stream=True)``).
    A streaming generator holds an open SSE connection until a terminal event —
    if you stop early (``break``), call ``aclose()`` on it (or fully drain it)
    so the connection is released promptly rather than at GC time.
    """

    def ask(
        self,
        question: str,
        username: str = "ludo",
        *,
        conversation_id: Optional[str] = None,
        stream: bool = False,
    ) -> Awaitable[str] | AsyncIterator[dict]:
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
            ``content``/``tool``/``done``/``error``).
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
                is_terminal=lambda o: o.get("type") in _ASK_TERMINAL,
            )
        return self._ask_nonstream(body)

    async def _ask_nonstream(self, body: dict) -> str:
        resp = await self._async_partner_http.post("/partner/ask", json=body)
        self._check_rest_response(resp)
        data = resp.json()
        return data.get("answer", "") if isinstance(data, dict) else ""

    def ask_my_agent(
        self,
        question: str,
        *,
        conversation_id: Optional[str] = None,
        stream: bool = False,
    ) -> Awaitable[dict] | AsyncIterator[dict]:
        """Talk to your own SuperMe AI agent (async).

        Example:
            ```python
            result = await client.ask_my_agent("Summarise my last 3 posts")

            async for evt in client.ask_my_agent("Summarise my posts", stream=True):
                if evt["type"] == "content":
                    print(evt["content"], end="", flush=True)
            ```

        Returns:
            An awaitable resolving to a dict with ``response`` and
            ``conversation_id``, or — when ``stream=True`` — an async generator
            of typed turn-event dicts (stops after a terminal event).
        """
        if stream:
            body: dict[str, Any] = {"question": question, "stream": True}
            if conversation_id:
                body["conversation_id"] = conversation_id
            return self._aiter_sse(
                self._async_partner_http,
                "POST",
                "/partner/agent",
                json=body,
                is_terminal=lambda o: o.get("type") in _AGENT_TERMINAL,
            )
        args: dict[str, Any] = {"question": question}
        if conversation_id:
            args["conversation_id"] = conversation_id
        return self._async_mcp_tool_call("ask_my_agent", args)
