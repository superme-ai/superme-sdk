"""HTTP / JSON-RPC / SSE internals mixin."""

from __future__ import annotations

import json
from typing import Any, Optional

import httpx


class HttpMixin:
    """Private HTTP, JSON-RPC, and SSE plumbing shared by all domain mixins.

    Expects the following attributes set by ``SuperMeClient.__init__``:
        self._http, self._rest_http, self._rpc_id, self.api_key, self.base_url
    """

    @property
    def _is_stream_endpoint(self) -> bool:
        """True when base_url points to the direct stream endpoint (not MCP JSON-RPC)."""
        return "/mcp/chat/stream" in self.base_url

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
        return self._http.request(method, endpoint, **kwargs)

    def _next_rpc_id(self) -> int:
        self._rpc_id += 1
        return self._rpc_id

    def _mcp_request(self, method: str, params: dict) -> dict:
        """Send a JSON-RPC 2.0 request to /mcp on the REST base URL.

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
        resp = self._http.post("/mcp/", json=payload)
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
        text = (content_list[0].get("text") or "").strip() or "{}"
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
                current_block.append(line[6:] + "\n")
            elif line.startswith("data:"):
                current_block.append(line[5:] + "\n")
            elif line == "" and current_block:
                # end of an event block — commit and reset
                last_block = current_block
                current_block = []
        # Stream may not end with a blank line; treat any trailing lines as last
        if current_block:
            last_block = current_block
        if not last_block:
            raise ValueError("No data lines found in SSE response")
        return json.loads("".join(last_block).rstrip("\n"))

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
