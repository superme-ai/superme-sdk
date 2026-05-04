"""Conversation and MCP tool helper methods — sync."""

from __future__ import annotations

import warnings
from typing import Any, Generator, Optional

from superme_sdk.models import StreamEvent


class ConversationsMixin:
    def ask(
        self,
        question: str,
        username: str = "ludo",
        conversation_id: Optional[str] = None,
        max_tokens: int = 1000,
        incognito: bool = False,
        **kwargs: Any,
    ) -> str:
        """Ask a single question.

        Example:
            ```python
            answer = client.ask("What is PMF?", username="ludo")
            print(answer)

            # anonymously
            answer = client.ask("What is PMF?", username="ludo", incognito=True)
            ```

        Args:
            question: The question to ask.
            username: Target SuperMe username.
            conversation_id: Continue an existing conversation.
            max_tokens: Max response tokens.
            incognito: Ask anonymously.

        Returns:
            Answer text.
        """
        response = self.chat.completions.create(
            messages=[{"role": "user", "content": question}],
            username=username,
            conversation_id=conversation_id,
            max_tokens=max_tokens,
            incognito=incognito,
            **kwargs,
        )
        return response.choices[0].message.content

    def ask_with_history(
        self,
        messages: list,
        username: str = "ludo",
        conversation_id: Optional[str] = None,
        max_tokens: int = 1000,
        incognito: bool = False,
        **kwargs: Any,
    ) -> tuple:
        """Ask with conversation history.

        .. deprecated::
            Use :meth:`ask` with ``conversation_id`` instead.
            Only the last user message in ``messages`` is actually sent;
            the rest of the list is ignored.

        Example:
            ```python
            # Preferred — use ask() with conversation_id
            answer = client.ask("What is growth hacking?", username="ludo")
            answer2 = client.ask(
                "Give me 3 examples",
                username="ludo",
                conversation_id=conv_id,
            )
            ```

        Args:
            messages: List of ``{"role": ..., "content": ...}`` dicts.
                Only the last user message is sent; prior messages are ignored.
            username: Target SuperMe username.
            conversation_id: Continue an existing conversation.
            max_tokens: Ignored.
            incognito: Ask anonymously.

        Returns:
            ``(answer_text, conversation_id)``
        """
        warnings.warn(
            "ask_with_history() is deprecated — use ask() with conversation_id instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        response = self.chat.completions.create(
            messages=messages,
            username=username,
            conversation_id=conversation_id,
            max_tokens=max_tokens,
            incognito=incognito,
            **kwargs,
        )
        conv_id = (response.metadata or {}).get("conversation_id")
        return response.choices[0].message.content, conv_id

    def mcp_tool_call(
        self, tool_name: str, arguments: dict
    ) -> "dict[str, Any] | list[Any]":
        """Call any MCP tool by name and return the parsed result.

        .. deprecated::
            Use ``client.low_level.tool_call()`` instead.

        Example:
            ```python
            result = client.low_level.tool_call("get_profile", {"identifier": "ludo"})
            ```

        Args:
            tool_name: MCP tool name (e.g. ``"get_profile"``).
            arguments: Tool arguments dict.

        Returns:
            Parsed JSON dict from the tool's response content.
        """
        warnings.warn(
            "client.mcp_tool_call() is deprecated — use client.low_level.tool_call() instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self._mcp_tool_call(tool_name, arguments)

    def mcp_list_tools(self) -> list[dict]:
        """List all available MCP tools.

        .. deprecated::
            Use ``client.low_level.list_tools()`` instead.

        Example:
            ```python
            tools = client.low_level.list_tools()
            for t in tools:
                print(t["name"])
            ```

        Returns:
            List of tool definitions.
        """
        warnings.warn(
            "client.mcp_list_tools() is deprecated — use client.low_level.list_tools() instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        data = self._mcp_request("tools/list", {})
        return data.get("tools", [])

    def list_conversations(self, *, limit: int = 20) -> list[dict]:
        """Return the authenticated user's most recent conversations.

        Example:
            ```python
            convs = client.list_conversations(limit=5)
            for c in convs:
                print(c["conversation_id"], c["title"])
            ```

        Args:
            limit: Maximum number of conversations to return.

        Returns:
            List of conversation summary dicts.
        """
        result = self._mcp_tool_call("list_conversations", {"limit": limit})
        if isinstance(result, list):
            return result
        conversations = result.get("conversations", [])
        return conversations if isinstance(conversations, list) else []

    def get_conversation(self, conversation_id: str) -> dict:
        """Fetch full details of a single conversation, including all messages.

        Example:
            ```python
            conv = client.get_conversation("conv_abc123")
            for msg in conv["messages"]:
                print(msg["role"], msg["content"])
            ```

        Args:
            conversation_id: The conversation ID (from list_conversations).

        Returns:
            Conversation dict with metadata and message history.
        """
        return self._mcp_tool_call(
            "get_conversation", {"conversation_id": conversation_id}
        )

    def ask_my_agent_stream(
        self,
        question: str,
        *,
        conversation_id: Optional[str] = None,
    ) -> Generator[StreamEvent, None, None]:
        """Stream a response from your SuperMe AI agent.

        Example:
            ```python
            for event in client.ask_my_agent_stream("Summarise my last 3 posts"):
                if event.done:
                    print("conversation_id:", event.conversation_id)
                else:
                    print(event.text, end="", flush=True)
            ```

        Yields :class:`~superme_sdk.models.StreamEvent` objects.
        The final event has ``done=True`` and ``conversation_id`` set.
        """
        yield from self._stream_direct(question, conversation_id=conversation_id)

    def ask_my_agent(
        self,
        question: str,
        *,
        conversation_id: Optional[str] = None,
    ) -> dict:
        """Talk to your own SuperMe AI agent.

        Example:
            ```python
            result = client.ask_my_agent("Summarise my last 3 posts")
            print(result["response"])

            # continue the conversation
            result2 = client.ask_my_agent(
                "Make it shorter",
                conversation_id=result["conversation_id"],
            )
            ```

        Args:
            question: Your message to the agent.
            conversation_id: Continue an existing conversation.

        Returns:
            Dict with ``response`` and ``conversation_id``.
        """
        args: dict[str, Any] = {"question": question}
        if conversation_id:
            args["conversation_id"] = conversation_id
        return self._mcp_tool_call("ask_my_agent", args)


