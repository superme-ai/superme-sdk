"""Conversation methods — async."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any, Optional

_ASK_TERMINAL = {"done", "error"}
_AGENT_TERMINAL = {"turn_completed", "turn_failed", "turn_interrupted"}


class AsyncConversationsMixin:
    """Async variants of :class:`~superme_sdk.services._conversations.ConversationsMixin`.

    Streaming methods hold an open SSE connection until a terminal event. If you
    stop early (``break``), call ``aclose()`` on the generator (or fully drain
    it) so the connection is released promptly rather than at GC time.
    """

    async def ask_my_agent(
        self,
        question: str,
        *,
        conversation_id: Optional[str] = None,
    ) -> dict:
        """Talk to your own SuperMe AI agent (async).

        Returns:
            Dict with ``response`` and ``conversation_id``.
        """
        args: dict[str, Any] = {"question": question}
        if conversation_id:
            args["conversation_id"] = conversation_id
        return await self._async_mcp_tool_call("ask_my_agent", args)

    async def ask_stream(
        self,
        question: str,
        username: str = "ludo",
        *,
        conversation_id: Optional[str] = None,
    ) -> AsyncIterator[dict]:
        """Stream an answer from a user's agent via ``POST /partner/ask`` (SSE).

        Example:
            ```python
            async for chunk in client.ask_stream("What is PMF?", username="ludo"):
                if chunk["type"] == "content":
                    print(chunk["text"], end="", flush=True)
            ```

        Yields:
            Chunk dicts with a ``type`` key: ``content`` (``text``), ``tool``
            (``label``), ``done`` (``conversation_id``), or ``error``
            (``message``). Stops after ``done`` or ``error``.
        """
        body: dict[str, Any] = {
            "identifier": username,
            "question": question,
            "stream": True,
        }
        if conversation_id:
            body["conversation_id"] = conversation_id
        async for chunk in self._aiter_sse(
            self._async_partner_http,
            "POST",
            "/partner/ask",
            json=body,
            is_terminal=lambda o: o.get("type") in _ASK_TERMINAL,
        ):
            yield chunk

    async def ask_my_agent_stream(
        self,
        question: str,
        *,
        conversation_id: Optional[str] = None,
    ) -> AsyncIterator[dict]:
        """Stream your own agent's turn via ``POST /partner/agent`` (SSE).

        Example:
            ```python
            async for evt in client.ask_my_agent_stream("Summarise my posts"):
                if evt["type"] == "content":
                    print(evt["content"], end="", flush=True)
            ```

        Yields:
            Typed turn-event dicts (``turn_started``, ``content``, ``message``,
            ``tool_call``, ``tool_result``, ``turn_completed``, ``turn_failed``,
            ...). Stops after a terminal event.
        """
        body: dict[str, Any] = {"question": question, "stream": True}
        if conversation_id:
            body["conversation_id"] = conversation_id
        async for evt in self._aiter_sse(
            self._async_partner_http,
            "POST",
            "/partner/agent",
            json=body,
            is_terminal=lambda o: o.get("type") in _AGENT_TERMINAL,
        ):
            yield evt
