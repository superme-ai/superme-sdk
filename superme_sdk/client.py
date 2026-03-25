"""SuperMe client -- direct HTTP calls via httpx."""

from __future__ import annotations

from typing import Any, Optional

import httpx


class SuperMeClient:
    """SuperMe API client.

    Example::

        client = SuperMeClient(api_key="your-superme-api-key")
        answer = client.ask("What is PMF?", username="ludo")
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.superme.ai",
        timeout: float = 120.0,
    ):
        if not api_key:
            raise ValueError("api_key is required")
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self._http = httpx.Client(
            base_url=self.base_url,
            headers={"Authorization": f"Bearer {self.api_key}"},
            timeout=timeout,
        )

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
        body = self._build_completion_body(
            messages=[{"role": "user", "content": question}],
            username=username,
            conversation_id=conversation_id,
            max_tokens=max_tokens,
            incognito=incognito,
            **kwargs,
        )
        data = self._post("/sdk/chat/completions", body)
        return data["choices"][0]["message"]["content"]

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
        body = self._build_completion_body(
            messages=messages,
            username=username,
            conversation_id=conversation_id,
            max_tokens=max_tokens,
            incognito=incognito,
            **kwargs,
        )
        data = self._post("/sdk/chat/completions", body)
        text = data["choices"][0]["message"]["content"]
        conv_id = (data.get("metadata") or {}).get("conversation_id")
        return text, conv_id

    def chat_completions(
        self,
        messages: list,
        username: str = "ludo",
        max_tokens: int = 1000,
        model: str = "gpt-4",
        response_format: Optional[dict] = None,
        **kwargs: Any,
    ) -> dict:
        """OpenAI-shaped chat completion (returns full response dict).

        Useful when callers need the raw OpenAI-format response body.
        """
        body = self._build_completion_body(
            messages=messages,
            username=username,
            max_tokens=max_tokens,
            model=model,
            response_format=response_format,
            **kwargs,
        )
        return self._post("/sdk/chat/completions", body)

    # ------------------------------------------------------------------
    # Raw HTTP
    # ------------------------------------------------------------------

    def raw_request(
        self, endpoint: str, method: str = "POST", **kwargs: Any
    ) -> httpx.Response:
        """Make a raw HTTP request to the SuperMe API.

        Args:
            endpoint: Path (e.g. ``"/mcp"``).
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

    def _build_completion_body(
        self,
        messages: list,
        username: str = "ludo",
        conversation_id: Optional[str] = None,
        max_tokens: int = 1000,
        incognito: bool = False,
        model: str = "gpt-4",
        response_format: Optional[dict] = None,
        **extra: Any,
    ) -> dict:
        body: dict = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "username": username,
        }
        if conversation_id:
            body["conversation_id"] = conversation_id
        if incognito:
            body["incognito"] = incognito
        if response_format:
            body["response_format"] = response_format
        body.update(extra)
        return body

    def _post(self, path: str, json_body: dict) -> dict:
        """POST JSON and return parsed response, raising on errors."""
        resp = self._http.post(path, json=json_body)
        resp.raise_for_status()
        return resp.json()

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
