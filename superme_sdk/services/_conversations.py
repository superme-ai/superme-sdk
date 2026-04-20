"""Conversation and MCP tool helper methods."""

from __future__ import annotations

from typing import Any, Optional


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

        Args:
            question: The question to ask.
            username: Target SuperMe username.
            conversation_id: Continue an existing conversation.
            max_tokens: Max response tokens.
            incognito: Ask anonymously.

        Returns:
            Answer text.

        Example:
            ```python
            answer = client.ask("What is PMF?", username="ludo")
            print(answer)

            # anonymously
            answer = client.ask("What is PMF?", username="ludo", incognito=True)
            ```
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

        Args:
            messages: List of ``{"role": ..., "content": ...}`` dicts.
            username: Target SuperMe username.
            conversation_id: Continue an existing conversation.
            max_tokens: Max response tokens.
            incognito: Ask anonymously.

        Returns:
            ``(answer_text, conversation_id)``

        Example:
            ```python
            messages = [{"role": "user", "content": "What is growth hacking?"}]
            answer, conv_id = client.ask_with_history(messages, username="ludo")

            # follow-up in the same conversation
            messages += [
                {"role": "assistant", "content": answer},
                {"role": "user", "content": "Give me 3 examples"},
            ]
            answer2, _ = client.ask_with_history(
                messages, username="ludo", conversation_id=conv_id
            )
            ```
        """
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

    def mcp_tool_call(self, tool_name: str, arguments: dict) -> dict:
        """Call any MCP tool by name and return the parsed result.

        Args:
            tool_name: MCP tool name (e.g. ``"get_profile"``).
            arguments: Tool arguments dict.

        Returns:
            Parsed JSON dict from the tool's response content.
        """
        return self._mcp_tool_call(tool_name, arguments)

    def mcp_list_tools(self) -> list[dict]:
        """List all available MCP tools.

        Returns:
            List of tool definitions.
        """
        data = self._mcp_request("tools/list", {})
        return data.get("tools", [])

    def list_conversations(self, *, limit: int = 20) -> list[dict]:
        """Return the authenticated user's most recent conversations.

        Args:
            limit: Maximum number of conversations to return.

        Returns:
            List of conversation summary dicts.

        Example:
            ```python
            convs = client.list_conversations(limit=5)
            for c in convs:
                print(c["conversation_id"], c["title"])
            ```
        """
        result = self._mcp_tool_call("list_conversations", {"limit": limit})
        if isinstance(result, list):
            return result
        conversations = result.get("conversations", [])
        return conversations if isinstance(conversations, list) else []

    def get_conversation(self, conversation_id: str) -> dict:
        """Fetch full details of a single conversation, including all messages.

        Args:
            conversation_id: The conversation ID (from list_conversations).

        Returns:
            Conversation dict with metadata and message history.

        Example:
            ```python
            conv = client.get_conversation("conv_abc123")
            for msg in conv["messages"]:
                print(msg["role"], msg["content"])
            ```
        """
        return self._mcp_tool_call(
            "get_conversation", {"conversation_id": conversation_id}
        )

    def ask_my_agent_stream(
        self,
        question: str,
        *,
        conversation_id: Optional[str] = None,
    ):
        """Stream a response from your SuperMe AI agent.

        Yields string chunks as they arrive from the server via SSE.
        The last item is always a dict
        ``{"conversation_id": ..., "_done": True}`` so callers can capture
        the conversation ID without a second call.
        """
        # if self._is_stream_endpoint:
        yield from self._stream_direct(question, conversation_id=conversation_id)
        # else:
        #     yield from self._stream_mcp(question, conversation_id=conversation_id)

    def ask_my_agent(
        self,
        question: str,
        *,
        conversation_id: Optional[str] = None,
    ) -> dict:
        """Talk to your own SuperMe AI agent.

        Args:
            question: Your message to the agent.
            conversation_id: Continue an existing conversation.

        Returns:
            Dict with ``response`` and ``conversation_id``.

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
        """
        args: dict[str, Any] = {"question": question}
        if conversation_id:
            args["conversation_id"] = conversation_id
        return self._mcp_tool_call("ask_my_agent", args)
