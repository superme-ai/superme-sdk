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
        rest_base_url: str = "https://www.superme.ai",
        timeout: float = 120.0,
    ):
        if not api_key:
            raise ValueError("api_key is required")
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.rest_base_url = rest_base_url.rstrip("/")
        _auth_headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }
        self._http = httpx.Client(
            base_url=self.base_url,
            headers=_auth_headers,
            timeout=timeout,
            follow_redirects=True,
        )
        self._rest_http = httpx.Client(
            base_url=self.rest_base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Accept": "application/json",
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

    @property
    def user_id(self) -> Optional[str]:
        """Extract user_id from the JWT token payload."""
        try:
            import base64
            parts = self.api_key.split(".")
            padded = parts[1] + "=" * (-len(parts[1]) % 4)
            data = json.loads(base64.urlsafe_b64decode(padded))
            return data.get("user_id")
        except Exception:
            return None

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
        result = self._mcp_tool_call("list_conversations", {"limit": limit})
        conversations = result.get("conversations", [])
        return conversations if isinstance(conversations, list) else []

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

    @property
    def _is_stream_endpoint(self) -> bool:
        """True when base_url points to the direct stream endpoint (not MCP JSON-RPC)."""
        return "/mcp/chat/stream" in self.base_url

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

    def _stream_direct(
        self,
        question: str,
        *,
        conversation_id: Optional[str] = None,
    ):
        """Stream via the direct /mcp/chat/stream endpoint."""
        payload: dict[str, Any] = {"question": question}
        if conversation_id:
            payload["conversation_id"] = conversation_id

        # Extract user_id from JWT token payload
        try:
            import base64
            parts = self.api_key.split(".")
            padded = parts[1] + "=" * (-len(parts[1]) % 4)
            token_data = json.loads(base64.urlsafe_b64decode(padded))
            payload["user_id"] = token_data.get("user_id", "")
        except Exception:
            pass

        conv_id_out: Optional[str] = conversation_id

        # Disable compression so chunks arrive unbuffered
        with self._http.stream(
            "POST", "/mcp/chat/stream", json=payload,
            headers={"Accept-Encoding": "identity"},
        ) as resp:
            resp.raise_for_status()

            buf = ""
            for raw_chunk in resp.iter_text():
                buf += raw_chunk
                while "\n" in buf:
                    line, buf = buf.split("\n", 1)
                    line = line.strip()
                    if not line:
                        continue
                    # Strip SSE "data: " prefix if present
                    if line.startswith("data: "):
                        line = line[6:]
                    elif line.startswith("data:"):
                        line = line[5:]
                    try:
                        obj = json.loads(line)
                    except (json.JSONDecodeError, ValueError):
                        yield line
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
                            yield text
                    elif msg_type == "done":
                        pass

        yield {"conversation_id": conv_id_out, "_done": True}

    def _stream_mcp(
        self,
        question: str,
        *,
        conversation_id: Optional[str] = None,
    ):
        """Stream via the MCP JSON-RPC endpoint."""
        args: dict[str, Any] = {"question": question}
        if conversation_id:
            args["conversation_id"] = conversation_id

        payload = {
            "jsonrpc": "2.0",
            "id": self._next_rpc_id(),
            "method": "tools/call",
            "params": {"name": "ask_my_agent", "arguments": args},
        }

        with self._http.stream("POST", "/", json=payload) as resp:
            resp.raise_for_status()
            ct = resp.headers.get("content-type", "")

            # Non-SSE fallback: yield full response at once
            if "text/event-stream" not in ct:
                resp.read()
                body = resp.json()
                if "error" in body:
                    err = body["error"]
                    raise RuntimeError(
                        f"MCP error {err.get('code', '?')}: {err.get('message', str(err))}"
                    )
                result = self._extract_tool_result(body.get("result", {}))
                if result:
                    yield result.get("response", "")
                    yield {"conversation_id": result.get("conversation_id"), "_done": True}
                else:
                    yield {"conversation_id": None, "_done": True}
                return

            # SSE streaming: yield deltas between progressive responses
            current_block: list[str] = []
            prev_text = ""
            conv_id_out: Optional[str] = None

            for raw_line in resp.iter_lines():
                if raw_line.startswith("data: "):
                    current_block.append(raw_line[6:])
                elif raw_line.startswith("data:"):
                    current_block.append(raw_line[5:])
                elif raw_line == "" and current_block:
                    try:
                        obj = json.loads("".join(current_block))
                    except (json.JSONDecodeError, ValueError):
                        current_block = []
                        continue
                    if "error" in obj:
                        err = obj["error"]
                        raise RuntimeError(
                            f"MCP error {err.get('code', '?')}: {err.get('message', str(err))}"
                        )
                    if "result" in obj:
                        result = self._extract_tool_result(obj["result"])
                        if result:
                            conv_id_out = result.get("conversation_id") or conv_id_out
                            full_text = result.get("response", "")
                            if len(full_text) > len(prev_text):
                                yield full_text[len(prev_text):]
                                prev_text = full_text
                    current_block = []

            # Handle trailing block without a final blank line
            if current_block:
                try:
                    obj = json.loads("".join(current_block))
                    if "result" in obj:
                        result = self._extract_tool_result(obj["result"])
                        if result:
                            conv_id_out = result.get("conversation_id") or conv_id_out
                            full_text = result.get("response", "")
                            if len(full_text) > len(prev_text):
                                yield full_text[len(prev_text):]
                except (json.JSONDecodeError, ValueError):
                    pass

            if prev_text or conv_id_out:
                yield {"conversation_id": conv_id_out, "_done": True}

    @staticmethod
    def _extract_tool_result(result: dict) -> Optional[dict]:
        """Parse the JSON payload from an MCP tool result content block."""
        content_list = result.get("content", [])
        if not content_list:
            return None
        text = (content_list[0].get("text") or "").strip()
        if not text:
            return None
        try:
            obj, _ = json.JSONDecoder().raw_decode(text)
            return obj if isinstance(obj, dict) else None
        except (json.JSONDecodeError, ValueError):
            return None

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

    def group_converse(
        self,
        participants: list[str],
        topic: str,
        *,
        max_turns: int = 3,
    ) -> dict:
        """Start a multi-turn group conversation between multiple people.

        Args:
            participants: People to include — names, usernames, or user IDs.
                At least 2 must resolve to known users.
            topic: The topic or question for the group to discuss.
            max_turns: Maximum conversation turns (1-5, default 3).

        Returns:
            Dict with conversation_id, perspectives, participant_ids, and
            any unresolved identifiers.
        """
        args: dict[str, Any] = {
            "participants": participants,
            "topic": topic,
        }
        if max_turns != 3:
            args["max_turns"] = max_turns
        return self._mcp_tool_call("group_converse", args)

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

    def _mcp_tool_call(self, tool_name: str, arguments: dict) -> dict:
        """Call an MCP tool and return the parsed JSON content."""
        result = self._mcp_request(
            "tools/call",
            {"name": tool_name, "arguments": arguments},
        )
        # MCP tools return {content: [{type: "text", text: "<json>"}]}
        content_list = result.get("content", [])
        if not content_list:
            return {}
        text = content_list[0].get("text") or "{}"
        parsed = json.loads(text)
        if not isinstance(parsed, dict):
            raise TypeError(
                f"Expected MCP tool to return a JSON object, got {type(parsed).__name__}"
            )
        return parsed

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

    # ------------------------------------------------------------------
    # Accounts (REST API — https://www.superme.ai/api/v1/)
    # ------------------------------------------------------------------

    @staticmethod
    def _check_rest_response(resp: "httpx.Response") -> None:
        """Raise with the API error message on non-2xx responses."""
        if resp.is_success:
            return
        try:
            body = resp.json()
            msg = body.get("error") or body.get("message") or resp.text
        except Exception:
            msg = resp.text
        raise RuntimeError(msg)

    def get_connected_accounts(self, user_id: Optional[str] = None) -> dict:
        """Return connected social accounts for the authenticated user.

        Args:
            user_id: Target user ID. Omit to use the authenticated user.

        Returns:
            Dict with ``connected_accounts`` and ``connected_blogs`` fields.
        """
        params: dict[str, Any] = {}
        uid = user_id or self.user_id
        if uid:
            params["user_id"] = uid
        resp = self._rest_http.get("/api/v1/get_connected_accounts", params=params)
        self._check_rest_response(resp)
        return resp.json()

    def connect_social(
        self,
        platform: str,
        handle: str,
        token: Optional[str] = None,
    ) -> dict:
        """Connect a social platform account.

        Args:
            platform: Platform name — one of: medium, substack, x, instagram,
                youtube, beehiiv, google_drive, linkedin, github, notion.
            handle: Username / handle / URL for the platform.
            token: API token (required for beehiiv; optional for github).

        Returns:
            Dict with ``status`` field.
        """
        body: dict[str, Any] = {"platform": platform, "handle": handle}
        if token is not None:
            body["token"] = token
        resp = self._rest_http.post("/api/v1/connect_social", json=body)
        self._check_rest_response(resp)
        return resp.json()

    def disconnect_social(self, platform: str) -> dict:
        """Disconnect a social platform account.

        Args:
            platform: Platform name to disconnect.

        Returns:
            Dict with ``status`` field.
        """
        resp = self._rest_http.post(
            "/api/v1/disconnect_social", json={"platform": platform}
        )
        self._check_rest_response(resp)
        return resp.json()

    def connect_blog(self, url: str) -> dict:
        """Connect a custom blog or website.

        Args:
            url: Full URL of the blog (e.g. ``https://myblog.com``).
                 Substack, Medium, Beehiiv, YouTube, and GitHub URLs are rejected.

        Returns:
            Dict with ``status`` field.
        """
        resp = self._rest_http.post("/api/v1/connect_blog", json={"url": url})
        self._check_rest_response(resp)
        return resp.json()

    def disconnect_blog(self, url: str) -> dict:
        """Disconnect a custom blog.

        Args:
            url: Full URL of the blog to disconnect.

        Returns:
            Dict with ``status`` field.
        """
        resp = self._rest_http.post("/api/v1/disconnect_blog", json={"url": url})
        self._check_rest_response(resp)
        return resp.json()

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._rest_http.close()
        self._http.close()

    def __enter__(self) -> "SuperMeClient":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()
