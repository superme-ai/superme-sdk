"""Conversation and MCP tool helper methods — sync."""

from __future__ import annotations

import warnings
from collections.abc import Iterator
from typing import Any, Optional

_ASK_TERMINAL = {"done", "error"}
_AGENT_TERMINAL = {"turn_completed", "turn_failed", "turn_interrupted"}


class ConversationsMixin:
    def ask(
        self,
        question: str,
        username: str = "ludo",
        conversation_id: Optional[str] = None,
        max_tokens: int = 1000,
        incognito: bool = False,
        stream: bool = False,
        **kwargs: Any,
    ) -> str | Iterator[dict]:
        """Ask a single question to a user's SuperMe agent.

        Example:
            ```python
            answer = client.ask("What is PMF?", username="ludo")
            print(answer)

            # anonymously
            answer = client.ask("What is PMF?", username="ludo", incognito=True)

            # streaming (yields chunk dicts over SSE)
            for chunk in client.ask("What is PMF?", username="ludo", stream=True):
                if chunk["type"] == "content":
                    print(chunk["text"], end="", flush=True)
            ```

        Args:
            question: The question to ask.
            username: Target SuperMe username or user_id.
            conversation_id: Continue an existing conversation.
            max_tokens: Max response tokens (non-streaming only).
            incognito: Ask anonymously (non-streaming only).
            stream: If True, return a generator of SSE chunk dicts instead of
                the answer string.

        Returns:
            The answer string, or — when ``stream=True`` — a generator yielding
            chunk dicts (``type``: ``content``/``tool``/``done``/``error``),
            stopping after ``done`` or ``error``. ``incognito`` and
            ``max_tokens`` do not apply to the streaming path.
        """
        if stream:
            body: dict[str, Any] = {
                "identifier": username,
                "question": question,
                "stream": True,
            }
            if conversation_id:
                body["conversation_id"] = conversation_id
            return self._iter_sse(
                self._partner_http,
                "POST",
                "/partner/ask",
                json=body,
                is_terminal=lambda o: o.get("type") in _ASK_TERMINAL,
            )
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

    def ask_my_agent(
        self,
        question: str,
        *,
        conversation_id: Optional[str] = None,
        stream: bool = False,
    ) -> dict | Iterator[dict]:
        """Talk to your own SuperMe AI agent.

        Example:
            ```python
            result = client.ask_my_agent("Summarise my last 3 posts")
            print(result["response"])

            # streaming (yields typed turn-event dicts over SSE)
            for evt in client.ask_my_agent("Summarise my posts", stream=True):
                if evt["type"] == "content":
                    print(evt["content"], end="", flush=True)
            ```

        Args:
            question: Your message to the agent.
            conversation_id: Continue an existing conversation.
            stream: If True, return a generator of SSE turn-event dicts instead
                of the final dict.

        Returns:
            Dict with ``response`` and ``conversation_id``, or — when
            ``stream=True`` — a generator yielding typed turn-event dicts
            (``turn_started``, ``content``, ``message``, ``tool_call``,
            ``tool_result``, ``turn_completed``, ``turn_failed``, ...), stopping
            after a terminal event.
        """
        if stream:
            body: dict[str, Any] = {"question": question, "stream": True}
            if conversation_id:
                body["conversation_id"] = conversation_id
            return self._iter_sse(
                self._partner_http,
                "POST",
                "/partner/agent",
                json=body,
                is_terminal=lambda o: o.get("type") in _AGENT_TERMINAL,
            )
        args: dict[str, Any] = {"question": question}
        if conversation_id:
            args["conversation_id"] = conversation_id
        return self._mcp_tool_call("ask_my_agent", args)
