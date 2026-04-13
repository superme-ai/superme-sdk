"""Chat proxy classes (client.chat.completions.create)."""

from __future__ import annotations

import time
import uuid
from typing import TYPE_CHECKING, Any, Optional

from .models import ChatCompletion

if TYPE_CHECKING:
    from .client import SuperMeClient


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
