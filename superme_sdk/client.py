"""SuperMe client -- OpenAI-compatible interface backed by MCP JSON-RPC."""

from __future__ import annotations

from typing import Any, Optional

import httpx

from ._transport._chat_proxy import Chat, Completions
from ._transport._http import HttpMixin, _decode_jwt
from .aio._http import AsyncHttpMixin
from .services._agentic_resume import AgenticResumeMixin
from .services._companies import CompaniesMixin
from .services._content import ContentMixin
from .services._conversations import ConversationsMixin
from .services._groups import GroupsMixin
from .services._interviews import InterviewsMixin
from .services._library import LibraryMixin
from .services._profiles import ProfilesMixin
from .services._social import SocialMixin
from .services._workgroups import WorkgroupsMixin
from .services.aio._agentic_resume import AsyncAgenticResumeMixin
from .services.aio._conversations import AsyncConversationsMixin
from .services.aio._groups import AsyncGroupsMixin
from .services.aio._interviews import AsyncInterviewsMixin
from .services.aio._workgroups import AsyncWorkgroupsMixin
from .models import ChatCompletion, Choice, Message, Usage

# Re-export for backward compatibility:
# `from superme_sdk.client import ChatCompletion` must keep working.
__all__ = [
    "SuperMeClient",
    "ChatCompletion",
    "Choice",
    "Message",
    "Usage",
    "Chat",
    "Completions",
]


class LowLevel:
    """Direct access to MCP protocol and raw HTTP.

    Prefer the domain-specific client methods for day-to-day use.
    This namespace is for power users who need to call MCP tools directly
    or send raw HTTP requests.

    Access via ``client.low_level``::

        tools = client.low_level.list_tools()
        result = client.low_level.tool_call("get_profile", {"identifier": "ludo"})
    """

    def __init__(self, client: "SuperMeClient") -> None:
        self._client = client

    def tool_call(
        self, tool_name: str, arguments: dict
    ) -> "dict[str, Any] | list[Any]":
        """Call any MCP tool by name and return the parsed result.

        Args:
            tool_name: MCP tool name (e.g. ``"get_profile"``).
            arguments: Tool arguments dict.

        Returns:
            Parsed JSON dict (or list) from the tool's response content.
        """
        return self._client._mcp_tool_call(tool_name, arguments)

    def list_tools(self) -> list[dict]:
        """List all available MCP tools.

        Returns:
            List of tool definition dicts (name, description, inputSchema).
        """
        data = self._client._mcp_request("tools/list", {})
        return data.get("tools", [])


class SuperMeClient(
    AgenticResumeMixin,
    ConversationsMixin,
    ProfilesMixin,
    GroupsMixin,
    CompaniesMixin,
    InterviewsMixin,
    LibraryMixin,
    ContentMixin,
    SocialMixin,
    WorkgroupsMixin,
    HttpMixin,
):
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

        # Low-level MCP access
        tools = client.low_level.list_tools()
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
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
            },
            timeout=timeout,
        )
        self._rpc_id = 0
        self.chat = Chat(self)
        self.low_level = LowLevel(self)

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
        return _decode_jwt(self.api_key).get("user_id")

    # ------------------------------------------------------------------
    # Context manager / cleanup
    # ------------------------------------------------------------------

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._rest_http.close()
        self._http.close()

    def __enter__(self) -> "SuperMeClient":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()


class AsyncSuperMeClient(
    AsyncAgenticResumeMixin,
    AsyncConversationsMixin,
    AsyncGroupsMixin,
    AsyncInterviewsMixin,
    AsyncWorkgroupsMixin,
    AsyncHttpMixin,
    # HttpMixin provides _check_rest_response, _parse_sse_json, _decode_jwt via MRO
    HttpMixin,
):
    """Async SuperMe API client.

    Drop-in async counterpart to :class:`SuperMeClient`.  Use with
    ``async with`` or call :meth:`aclose` when done.

    Example::

        async with AsyncSuperMeClient(api_key="your-superme-api-key") as client:
            async for event in client.ask_my_agent_stream("Summarise my last 3 posts"):
                if event.done:
                    print("done, conv_id:", event.conversation_id)
                else:
                    print(event.text, end="", flush=True)

            async for event in client.stream_interview("interview_abc123"):
                print(event)
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
        self._async_http = httpx.AsyncClient(
            base_url=self.base_url,
            headers=_auth_headers,
            timeout=timeout,
            follow_redirects=True,
        )
        self._async_rest_http = httpx.AsyncClient(
            base_url=self.rest_base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
            },
            timeout=timeout,
        )
        self._rpc_id = 0

    # ------------------------------------------------------------------
    # Properties (mirrors SuperMeClient)
    # ------------------------------------------------------------------

    @property
    def token(self) -> str:
        """Current API token."""
        return self.api_key

    @property
    def user_id(self) -> Optional[str]:
        """Extract user_id from the JWT token payload."""
        return _decode_jwt(self.api_key).get("user_id")

    # ------------------------------------------------------------------
    # Async context manager / cleanup
    # ------------------------------------------------------------------

    async def aclose(self) -> None:
        """Close the underlying async HTTP clients."""
        await self._async_rest_http.aclose()
        await self._async_http.aclose()

    async def __aenter__(self) -> "AsyncSuperMeClient":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.aclose()
