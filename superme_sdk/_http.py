"""HTTP / JSON-RPC / SSE internals mixin."""

from __future__ import annotations

import base64
import json
from typing import Any, Generator, Optional

import httpx

from ._sse import iter_sse_lines
from .exceptions import APIError, AuthError, MCPError, NotFoundError, RateLimitError
from .models import StreamEvent


def _decode_jwt(token: str) -> dict[str, Any]:
    """Decode the payload of a JWT token without verifying the signature.

    Returns an empty dict if the token is malformed or cannot be decoded.
    """
    try:
        parts = token.split(".")
        padded = parts[1] + "=" * (-len(parts[1]) % 4)
        result = json.loads(base64.urlsafe_b64decode(padded))
        return result if isinstance(result, dict) else {}
    except Exception:
        return {}


class HttpMixin:
    """Private HTTP, JSON-RPC, and SSE plumbing shared by all domain mixins.

    Expects the following attributes set by ``SuperMeClient.__init__``:
        self._http, self._rest_http, self._rpc_id, self.api_key, self.base_url
    """

    def _stream_direct(
        self,
        question: str,
        *,
        conversation_id: Optional[str] = None,
    ) -> Generator[StreamEvent, None, None]:
        """Stream via the direct /mcp/chat/stream endpoint.

        Yields :class:`~superme_sdk.models.StreamEvent` objects.
        The final event has ``done=True`` and ``conversation_id`` populated.
        """
        payload: dict[str, Any] = {"question": question}
        if conversation_id:
            payload["conversation_id"] = conversation_id

        token_data = _decode_jwt(self.api_key)
        if token_data.get("user_id"):
            payload["user_id"] = token_data["user_id"]

        conv_id_out: Optional[str] = conversation_id

        # Disable compression so chunks arrive unbuffered
        with self._http.stream(
            "POST",
            "/mcp/chat/stream",
            json=payload,
            headers={"Accept-Encoding": "identity"},
        ) as resp:
            if not resp.is_success:
                resp.read()
            self._check_rest_response(resp)

            for line in iter_sse_lines(resp):
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
        self._check_rest_response(resp)

        ct = resp.headers.get("content-type", "")
        if "text/event-stream" in ct:
            body = self._parse_sse_json(resp.text)
        else:
            body = resp.json()

        if "error" in body:
            err = body["error"]
            raise MCPError(
                f"MCP error {err.get('code', '?')}: {err.get('message', str(err))}",
                code=err.get("code"),
            )
        return body.get("result", {})

    def _mcp_tool_call(
        self, tool_name: str, arguments: dict
    ) -> dict[str, Any] | list[Any]:
        """Call an MCP tool and return the parsed JSON content (dict or list)."""
        result = self._mcp_request(
            "tools/call",
            {"name": tool_name, "arguments": arguments},
        )
        # MCP tools return {content: [{type: "text", text: "<json>"}]}
        content_list = result.get("content", [])
        if not content_list:
            return {}
        raw_text = content_list[0].get("text")
        text = (raw_text or "").strip() or "{}"
        return json.loads(text)

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
        """Raise a typed exception on non-2xx REST responses."""
        if resp.is_success:
            return
        try:
            body = resp.json()
            msg = body.get("error") or body.get("message") or resp.text
        except Exception:
            msg = resp.text
        status = resp.status_code
        if status in (401, 403):
            raise AuthError(msg, status_code=status)
        if status == 404:
            raise NotFoundError(msg, status_code=status)
        if status == 429:
            raise RateLimitError(msg, status_code=status)
        raise APIError(msg, status_code=status)
