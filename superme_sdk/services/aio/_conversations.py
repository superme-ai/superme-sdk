"""Conversation methods — async."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any, Optional

from ..._transport._sse import aiter_sse_lines

_ASK_TERMINAL = {"done", "error"}
_AGENT_TERMINAL = {"turn_completed", "turn_failed", "turn_interrupted"}


class AsyncConversationsMixin:
    """Async variants of :class:`~superme_sdk.services._conversations.ConversationsMixin`."""

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
        async for chunk in self._astream_partner("/partner/ask", body, _ASK_TERMINAL):
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
        async for evt in self._astream_partner("/partner/agent", body, _AGENT_TERMINAL):
            yield evt

    async def _astream_partner(
        self, path: str, body: dict, terminal: set[str]
    ) -> AsyncIterator[dict]:
        async with self._async_partner_http.stream(
            "POST",
            path,
            json=body,
            headers={"Accept-Encoding": "identity"},
            timeout=None,
        ) as resp:
            if not resp.is_success:
                await resp.aread()
            self._check_rest_response(resp)
            async for line in aiter_sse_lines(resp):
                try:
                    obj = json.loads(line)
                except (json.JSONDecodeError, ValueError):
                    continue
                if not isinstance(obj, dict):
                    continue
                yield obj
                if obj.get("type") in terminal:
                    return
