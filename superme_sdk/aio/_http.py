"""Async HTTP / JSON-RPC internals mixin.

Mirrors :class:`~superme_sdk._http.HttpMixin` using ``httpx.AsyncClient``.
Expects the following attributes set by ``AsyncSuperMeClient.__init__``:
    self._async_http, self._async_rest_http, self._rpc_id, self.api_key

``AsyncSuperMeClient`` also inherits ``HttpMixin``, so the static helpers
``_check_rest_response`` and ``_parse_sse_json`` are available via MRO.
"""

from __future__ import annotations

import json
from typing import Any

from ..exceptions import MCPError


class AsyncHttpMixin:
    """Async HTTP and JSON-RPC plumbing for :class:`AsyncSuperMeClient`.

    Works alongside :class:`~superme_sdk._http.HttpMixin` in the MRO —
    static helpers (``_check_rest_response``, ``_parse_sse_json``) are
    provided by that class and do not need to be duplicated here.
    """

    async def _async_mcp_request(self, method: str, params: dict) -> dict:
        """Send an async JSON-RPC 2.0 request to /mcp."""
        payload = {
            "jsonrpc": "2.0",
            "id": self._next_rpc_id(),
            "method": method,
            "params": params,
        }
        resp = await self._async_http.post("/mcp/", json=payload)
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

    async def _async_mcp_tool_call(
        self, tool_name: str, arguments: dict
    ) -> "dict[str, Any] | list[Any]":
        """Call an MCP tool asynchronously and return the parsed JSON content."""
        result = await self._async_mcp_request(
            "tools/call",
            {"name": tool_name, "arguments": arguments},
        )
        content_list = result.get("content", [])
        if not content_list:
            return {}
        raw_text = content_list[0].get("text")
        text = (raw_text or "").strip() or "{}"
        return json.loads(text)
