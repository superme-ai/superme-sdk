"""SuperMe client -- OpenAI-compatible interface backed by MCP JSON-RPC."""

from __future__ import annotations

import json
from typing import Any, Optional

import httpx

from ._chat_proxy import Chat, Completions
from ._http import HttpMixin
from .services._agentic_resume import AgenticResumeMixin
from .services._companies import CompaniesMixin
from .services._content import ContentMixin
from .services._conversations import ConversationsMixin
from .services._groups import GroupsMixin
from .services._interviews import InterviewsMixin
from .services._profiles import ProfilesMixin
from .services._social import SocialMixin
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


class SuperMeClient(
    AgenticResumeMixin,
    ConversationsMixin,
    ProfilesMixin,
    GroupsMixin,
    CompaniesMixin,
    InterviewsMixin,
    ContentMixin,
    SocialMixin,
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
