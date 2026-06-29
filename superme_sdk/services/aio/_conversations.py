"""Conversation methods — async."""

from __future__ import annotations

from typing import Any, Optional


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
