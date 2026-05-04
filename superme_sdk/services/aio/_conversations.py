"""Conversation methods — async."""

from __future__ import annotations

import json
from typing import Any, AsyncGenerator, Optional

from superme_sdk.models import StreamEvent
from ..._transport._ndjson import aiter_ndjson_lines


class AsyncConversationsMixin:
    """Async variants of :class:`~superme_sdk.services._conversations.ConversationsMixin`."""

    async def ask_my_agent_stream(
        self,
        question: str,
        *,
        conversation_id: Optional[str] = None,
    ) -> AsyncGenerator[StreamEvent, None]:
        """Stream a response from your SuperMe AI agent (async).

        Example:
            ```python
            async for event in client.ask_my_agent_stream("Summarise my last 3 posts"):
                if event.done:
                    print("conversation_id:", event.conversation_id)
                else:
                    print(event.text, end="", flush=True)
            ```

        Yields :class:`~superme_sdk.models.StreamEvent` objects.
        The final event has ``done=True`` and ``conversation_id`` set.
        """
        from ..._transport._http import _decode_jwt

        payload: dict[str, Any] = {"question": question}
        if conversation_id:
            payload["conversation_id"] = conversation_id

        token_data = _decode_jwt(self.api_key)
        if token_data.get("user_id"):
            payload["user_id"] = token_data["user_id"]

        conv_id_out: Optional[str] = conversation_id

        async with self._async_http.stream(
            "POST",
            "/mcp/chat/stream",
            json=payload,
            headers={"Accept-Encoding": "identity"},
        ) as resp:
            if not resp.is_success:
                await resp.aread()
            self._check_rest_response(resp)

            async for line in aiter_ndjson_lines(resp):
                try:
                    obj = json.loads(line)
                except (json.JSONDecodeError, ValueError):
                    yield StreamEvent(text=line)
                    continue
                if not isinstance(obj, dict):
                    continue
                msg_type = obj.get("type", "")
                metadata = obj.get("metadata") or {}
                if msg_type == "session_info":
                    conv_id_out = metadata.get("session_id") or conv_id_out
                elif msg_type == "content":
                    text = obj.get("content", "")
                    if text:
                        yield StreamEvent(text=text)

        yield StreamEvent(done=True, conversation_id=conv_id_out)

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
