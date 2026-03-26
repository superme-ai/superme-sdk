"""SuperMe client -- OpenAI-compatible interface backed by MCP JSON-RPC."""

from __future__ import annotations

import json
import time
import uuid
from typing import Any, Optional

import httpx


# ---------------------------------------------------------------------------
# Response model classes (mirror OpenAI SDK objects)
# ---------------------------------------------------------------------------


class Message:
    """A single chat message."""

    def __init__(self, data: dict) -> None:
        self.role: str = data.get("role", "assistant")
        self.content: str = data.get("content", "") or ""


class Choice:
    """One completion choice."""

    def __init__(self, data: dict) -> None:
        self.index: int = data.get("index", 0)
        self.message = Message(data.get("message", {}))
        self.finish_reason: Optional[str] = data.get("finish_reason")


class Usage:
    """Token usage statistics."""

    def __init__(self, data: dict) -> None:
        self.prompt_tokens: int = data.get("prompt_tokens", 0)
        self.completion_tokens: int = data.get("completion_tokens", 0)
        self.total_tokens: int = data.get("total_tokens", 0)


class ChatCompletion:
    """OpenAI-compatible chat completion response.

    SuperMe-specific fields (``metadata``) are preserved as attributes.
    """

    def __init__(self, data: dict) -> None:
        self.id: str = data.get("id", "")
        self.object: str = data.get("object", "chat.completion")
        self.created: int = data.get("created", 0)
        self.model: str = data.get("model", "")
        self.choices: list[Choice] = [Choice(c) for c in data.get("choices", [])]
        self.usage = Usage(data.get("usage") or {})
        self.metadata: Optional[dict] = data.get("metadata")


# ---------------------------------------------------------------------------
# Chat proxy classes (client.chat.completions.create)
# ---------------------------------------------------------------------------


class Completions:
    """Proxy for ``client.chat.completions``."""

    def __init__(self, client: "SuperMeClient") -> None:
        self._client = client

    def create(
        self,
        messages: list,
        model: str = "gpt-4",
        *,
        username: str = "ludo",
        conversation_id: Optional[str] = None,
        max_tokens: int = 1000,
        incognito: bool = False,
        response_format: Optional[dict] = None,
        **kwargs: Any,
    ) -> ChatCompletion:
        """Create a chat completion via the MCP ``ask`` tool.

        Args:
            messages: List of ``{"role": ..., "content": ...}`` dicts.
            model: Model name (ignored by MCP, kept for interface compat).
            username: Target SuperMe username (maps to MCP ``identifier``).
            conversation_id: Continue an existing conversation.
            max_tokens: Max response tokens (not used by MCP, kept for compat).
            incognito: Ask anonymously.
            response_format: Not supported via MCP (ignored).

        Returns:
            :class:`ChatCompletion` with ``.choices[0].message.content``
            and ``.metadata["conversation_id"]``.

        Example::

            response = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": "What is PMF?"}],
                username="ludo",
            )
            print(response.choices[0].message.content)
        """
        # Backward-compat: pre-hardening callers used extra_body={"username": ...}
        # to pass routing params through the OpenAI-compatible interface.
        # Extract any recognised fields from extra_body and let them override
        # the direct kwargs so old call sites keep working without changes.
        extra_body: dict = kwargs.pop("extra_body", {}) or {}
        if "username" in extra_body:
            username = extra_body["username"]
        if "incognito" in extra_body:
            incognito = extra_body["incognito"]
        if "conversation_id" in extra_body:
            conversation_id = extra_body["conversation_id"]

        # Extract the last user message as the question
        question = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                question = msg.get("content", "")
                break

        if not question:
            raise ValueError("messages must contain at least one user message")

        args: dict[str, Any] = {
            "identifier": username,
            "question": question,
        }
        if conversation_id:
            args["conversation_id"] = conversation_id
        if incognito:
            args["incognito"] = True

        result = self._client._mcp_tool_call("ask", args)

        # Build an OpenAI-shaped ChatCompletion from the MCP result
        return ChatCompletion(
            {
                "id": f"chatcmpl-{uuid.uuid4().hex[:12]}",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": model,
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": result.get("response", ""),
                        },
                        "finish_reason": "stop",
                    }
                ],
                "usage": {},
                "metadata": {
                    "conversation_id": result.get("conversation_id"),
                    "target_user": result.get("target_user"),
                    "target_user_id": result.get("target_user_id"),
                },
            }
        )


class Chat:
    """Proxy for ``client.chat``."""

    def __init__(self, client: "SuperMeClient") -> None:
        self.completions = Completions(client)


# ---------------------------------------------------------------------------
# Main client
# ---------------------------------------------------------------------------


class SuperMeClient:
    """SuperMe API client with OpenAI-compatible interface.

    Communicates with the SuperMe MCP server via JSON-RPC.

    Example::

        client = SuperMeClient(api_key="your-superme-api-key")

        # OpenAI-style
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": "What is PMF?"}],
            username="ludo",
        )
        print(response.choices[0].message.content)

        # Convenience helpers
        answer = client.ask("What is PMF?", username="ludo")
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://mcp.superme.ai",
        timeout: float = 120.0,
    ):
        if not api_key:
            raise ValueError("api_key is required")
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self._http = httpx.Client(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
            },
            timeout=timeout,
        )
        self._rpc_id = 0
        self.chat = Chat(self)

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def token(self) -> str:
        """Current API token."""
        return self.api_key

    # ------------------------------------------------------------------
    # High-level helpers
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # MCP tool helpers
    # ------------------------------------------------------------------

    def mcp_tool_call(self, tool_name: str, arguments: dict) -> Any:
        """Call any MCP tool by name and return the parsed result."""
        return self._mcp_tool_call(tool_name, arguments)

    def mcp_list_tools(self) -> list[dict]:
        """List all available MCP tools."""
        data = self._mcp_request("tools/list", {})
        return data.get("tools", [])

    # ------------------------------------------------------------------
    # Conversations
    # ------------------------------------------------------------------

    def list_conversations(self, *, limit: int = 20) -> list[dict]:
        """Return the authenticated user's most recent conversations.

        Args:
            limit: Maximum number of conversations to return.

        Returns:
            List of conversation summary dicts.
        """
        return self._mcp_tool_call("list_conversations", {"limit": limit})

    def get_conversation(self, conversation_id: str) -> dict:
        """Fetch full details of a single conversation, including all messages.

        Args:
            conversation_id: The conversation ID (from list_conversations).

        Returns:
            Conversation dict with metadata and message history.
        """
        return self._mcp_tool_call(
            "get_conversation", {"conversation_id": conversation_id}
        )

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
        """
        args: dict[str, Any] = {"question": question}
        if conversation_id:
            args["conversation_id"] = conversation_id
        return self._mcp_tool_call("ask_my_agent", args)

    # ------------------------------------------------------------------
    # Users
    # ------------------------------------------------------------------

    def get_profile(self, identifier: Optional[str] = None) -> dict:
        """Return public profile info for a user.

        Args:
            identifier: User ID, username, or full name. Omit for your own profile.

        Returns:
            Profile dict.
        """
        args: dict[str, Any] = {}
        if identifier:
            args["identifier"] = identifier
        return self._mcp_tool_call("get_profile", args)

    def find_user_by_name(self, name: str, *, limit: int = 10) -> dict:
        """Search for SuperMe users by name.

        Args:
            name: Full or partial name to search for.
            limit: Maximum results to return.

        Returns:
            Dict with match results.
        """
        return self._mcp_tool_call(
            "find_user_by_name", {"name": name, "limit": limit}
        )

    def find_users_by_names(
        self, names: list[str], *, limit_per_name: int = 10
    ) -> dict:
        """Resolve multiple names to SuperMe users in a single call.

        Args:
            names: List of names to look up.
            limit_per_name: Maximum matches per name.

        Returns:
            Dict with per-name matches and resolved_user_ids map.
        """
        return self._mcp_tool_call(
            "find_users_by_names",
            {"names": names, "limit_per_name": limit_per_name},
        )

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def perspective_search(self, question: str) -> dict:
        """Get perspectives from multiple experts on a topic.

        Args:
            question: A topic or question to get expert takes on.

        Returns:
            Dict with synthesized answer and individual viewpoints.
        """
        return self._mcp_tool_call("perspective_search", {"question": question})

    # ------------------------------------------------------------------
    # Content
    # ------------------------------------------------------------------

    def add_internal_content(
        self,
        input: list[str],
        *,
        extended_content: Optional[str] = None,
        past_instructions: Optional[str] = None,
    ) -> dict:
        """Save notes or knowledge to your personal library.

        Args:
            input: Text blocks to save.
            extended_content: Optional longer-form content.
            past_instructions: Instructions for how the AI should use this content.

        Returns:
            Dict with success status and learning IDs.
        """
        args: dict[str, Any] = {"input": input}
        if extended_content is not None:
            args["extended_content"] = extended_content
        if past_instructions is not None:
            args["past_instructions"] = past_instructions
        return self._mcp_tool_call("add_internal_content", args)

    def update_internal_content(
        self,
        learning_id: str,
        *,
        user_input: Optional[list[str]] = None,
        extended_content: Optional[str] = None,
        past_instructions: Optional[str] = None,
    ) -> dict:
        """Update an existing note in your library.

        Args:
            learning_id: The learning ID to update.
            user_input: Replacement note content.
            extended_content: Replacement long-form content.
            past_instructions: Replacement AI usage instructions.

        Returns:
            Dict with update result.
        """
        args: dict[str, Any] = {"learning_id": learning_id}
        if user_input is not None:
            args["user_input"] = user_input
        if extended_content is not None:
            args["extended_content"] = extended_content
        if past_instructions is not None:
            args["past_instructions"] = past_instructions
        return self._mcp_tool_call("update_internal_content", args)

    def add_external_content(
        self,
        urls: list[dict],
        *,
        reference: bool = True,
        instant_recrawl: bool = True,
    ) -> dict:
        """Submit URLs to be crawled and added to your knowledge base.

        Args:
            urls: List of URL objects. Each must have a ``"url"`` key.
            reference: Show citations from this content in AI answers.
            instant_recrawl: Crawl immediately vs. queue.

        Returns:
            Dict with counts of successful, existing, and failed URLs.
        """
        return self._mcp_tool_call(
            "add_external_content",
            {"urls": urls, "reference": reference, "instant_recrawl": instant_recrawl},
        )

    def check_uncrawled_urls(self, urls: list[str]) -> dict:
        """Check which URLs are not yet in your knowledge base.

        Args:
            urls: URLs to check.

        Returns:
            Dict with ``uncrawled_urls`` list and counts.
        """
        return self._mcp_tool_call("check_uncrawled_urls", {"urls": urls})

    # ------------------------------------------------------------------
    # Raw request helpers
    # ------------------------------------------------------------------

    def raw_request(self, method: str, params: dict | None = None) -> dict:
        """Send a raw MCP JSON-RPC request and return the result.

        Args:
            method: JSON-RPC method name (e.g. ``"tools/list"``).
            params: JSON-RPC params dict.

        Returns:
            Parsed ``result`` dict from the JSON-RPC response.
        """
        return self._mcp_request(method, params or {})

    def http_request(
        self, endpoint: str, method: str = "POST", **kwargs: Any
    ) -> httpx.Response:
        """Make a raw HTTP request to the SuperMe API.

        Args:
            endpoint: Path (e.g. ``"/health"``).
            method: HTTP method.
            **kwargs: Passed to ``httpx.Client.request``.

        Returns:
            ``httpx.Response`` object.
        """
        url = f"{self.base_url}{endpoint}"
        return self._http.request(method, url, **kwargs)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _next_rpc_id(self) -> int:
        self._rpc_id += 1
        return self._rpc_id

    def _mcp_request(self, method: str, params: dict) -> dict:
        """Send a JSON-RPC 2.0 request to the MCP endpoint.

        FastMCP Streamable HTTP may respond with either
        ``application/json`` or ``text/event-stream`` (SSE).  This method
        handles both transparently.
        """
        payload = {
            "jsonrpc": "2.0",
            "id": self._next_rpc_id(),
            "method": method,
            "params": params,
        }
        resp = self._http.post("/", json=payload)
        resp.raise_for_status()

        ct = resp.headers.get("content-type", "")
        if "text/event-stream" in ct:
            body = self._parse_sse_json(resp.text)
        else:
            body = resp.json()

        if "error" in body:
            err = body["error"]
            raise RuntimeError(
                f"MCP error {err.get('code', '?')}: {err.get('message', str(err))}"
            )
        return body.get("result", {})

    def _mcp_tool_call(self, tool_name: str, arguments: dict) -> Any:
        """Call an MCP tool and return the parsed JSON content."""
        result = self._mcp_request(
            "tools/call",
            {"name": tool_name, "arguments": arguments},
        )
        content_list = result.get("content", [])
        if not content_list:
            return {}
        text = content_list[0].get("text", "").strip()
        if not text:
            return {}
        # raw_decode parses the first valid JSON value and ignores any
        # trailing content — guards against 'Extra data' responses.
        obj, _ = json.JSONDecoder().raw_decode(text)
        return obj

    @staticmethod
    def _parse_sse_json(text: str) -> dict:
        """Extract the last JSON-RPC object from an SSE stream.

        SSE format is ``event: <name>\\ndata: <json>\\n\\n``.  We collect
        all ``data:`` lines from the last event block and parse them.

        We track two lists: ``current_block`` (lines accumulating for the
        event in progress) and ``last_block`` (lines from the most recently
        *completed* event).  A blank line marks the end of an event block —
        we commit ``current_block`` into ``last_block`` and start fresh.
        If the stream doesn't end with a blank line the in-progress lines
        are treated as the final block.
        """
        current_block: list[str] = []
        last_block: list[str] = []
        for line in text.splitlines():
            if line.startswith("data: "):
                current_block.append(line[6:])
            elif line.startswith("data:"):
                current_block.append(line[5:])
            elif line == "" and current_block:
                # end of an event block — commit and reset
                last_block = current_block
                current_block = []
        # Stream may not end with a blank line; treat any trailing lines as last
        if current_block:
            last_block = current_block
        if not last_block:
            raise ValueError("No data lines found in SSE response")
        return json.loads("".join(last_block))

    # ------------------------------------------------------------------
    # Context manager / cleanup
    # ------------------------------------------------------------------

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._http.close()

    def __enter__(self) -> "SuperMeClient":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()
