"""SuperMe client that provides OpenAI-compatible interface"""

from typing import Any, Optional

import requests
from openai import OpenAI


class SuperMeClient:
    """
    SuperMe client with OpenAI-compatible interface.

    This client provides a simple way to interact with SuperMe's AI API
    using the familiar OpenAI client interface.

    Example:
        >>> client = SuperMeClient(
        ...     username="your-username",
        ...     key="your-api-key",
        ...     base_url="https://api.superme.ai"
        ... )
        >>> response = client.chat.completions.create(
        ...     model="gpt-4",
        ...     messages=[{"role": "user", "content": "Hello!"}],
        ...     user="1"
        ... )
        >>> print(response.choices[0].message.content)
    """

    def __init__(
        self,
        username: str,
        key: str,
        base_url: str = "https://api.superme.ai",
        auto_login: bool = True,
    ):
        """
        Initialize SuperMe client.

        Args:
            username: SuperMe username
            key: SuperMe API key
            base_url: Base URL for SuperMe API (default: https://api.superme.ai)
            auto_login: Automatically login on initialization (default: True)
        """
        self.username = username
        self.key = key
        self.base_url = base_url.rstrip("/")
        self._jwt_token: Optional[str] = None
        self._openai_client: Optional[OpenAI] = None

        if auto_login:
            self.login()

    def login(self) -> str:
        """
        Login to SuperMe and get JWT token.

        Returns:
            JWT token

        Raises:
            Exception: If login fails
        """
        response = requests.post(
            f"{self.base_url}/login",
            json={
                "username": self.username,
                "password": self.key,
                "client": "MCP",
            },
        )

        if response.status_code != 200:
            raise Exception(
                f"Login failed with status {response.status_code}: {response.text}"
            )

        self._jwt_token = response.json()["backend_token"]

        # Initialize OpenAI client with SuperMe endpoint
        self._openai_client = OpenAI(
            base_url=f"{self.base_url}/mcp", api_key=self._jwt_token
        )

        return self._jwt_token

    @property
    def chat(self) -> Any:
        """
        Access to chat completions interface (OpenAI-compatible).

        Returns:
            OpenAI chat interface

        Example:
            >>> response = client.chat.completions.create(
            ...     model="gpt-4",
            ...     messages=[{"role": "user", "content": "Hello!"}],
            ...     extra_body={"user": "1"}
            ... )
        """
        if not self._openai_client:
            raise Exception("Not logged in. Call login() first.")
        return self._openai_client.chat

    @property
    def token(self) -> Optional[str]:
        """Get the current JWT token."""
        return self._jwt_token

    def ask(
        self,
        question: str,
        user_id: str = "1",
        conversation_id: Optional[str] = None,
        max_tokens: int = 1000,
        **kwargs,
    ) -> str:
        """
        Simplified method to ask a question.

        Args:
            question: The question to ask
            user_id: SuperMe user ID to query (default: "1")
            conversation_id: Continue existing conversation (optional)
            max_tokens: Maximum tokens in response (default: 1000)
            **kwargs: Additional arguments to pass to OpenAI client

        Returns:
            AI response as string

        Example:
            >>> answer = client.ask("What are growth strategies?", user_id="1")
            >>> print(answer)
        """
        extra_body = {"user": user_id}
        if conversation_id:
            extra_body["conversation_id"] = conversation_id

        response = self.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": question}],
            extra_body=extra_body,
            max_tokens=max_tokens,
            **kwargs,
        )

        return response.choices[0].message.content

    def ask_with_history(
        self,
        messages: list[dict],
        user_id: str = "1",
        conversation_id: Optional[str] = None,
        max_tokens: int = 1000,
        **kwargs,
    ) -> tuple[str, str]:
        """
        Ask a question with conversation history.

        Args:
            messages: List of messages in OpenAI format
            user_id: SuperMe user ID to query (default: "1")
            conversation_id: Continue existing conversation (optional)
            max_tokens: Maximum tokens in response (default: 1000)
            **kwargs: Additional arguments to pass to OpenAI client

        Returns:
            Tuple of (response_text, conversation_id)

        Example:
            >>> messages = [
            ...     {"role": "user", "content": "What is PMF?"},
            ...     {"role": "assistant", "content": "Product-market fit..."},
            ...     {"role": "user", "content": "How to measure it?"}
            ... ]
            >>> answer, conv_id = client.ask_with_history(messages, user_id="1")
        """
        extra_body = {"user": user_id}
        if conversation_id:
            extra_body["conversation_id"] = conversation_id

        response = self.chat.completions.create(
            model="gpt-4",
            messages=messages,
            extra_body=extra_body,
            max_tokens=max_tokens,
            **kwargs,
        )

        response_text = response.choices[0].message.content
        response_conv_id = (
            response.metadata.get("conversation_id")
            if hasattr(response, "metadata")
            else None
        )

        return response_text, response_conv_id

    def raw_request(
        self, endpoint: str, method: str = "POST", **kwargs
    ) -> requests.Response:
        """
        Make a raw HTTP request to SuperMe API.

        Args:
            endpoint: API endpoint (e.g., "/mcp/completion")
            method: HTTP method (default: POST)
            **kwargs: Additional arguments to pass to requests

        Returns:
            requests.Response object

        Example:
            >>> response = client.raw_request(
            ...     "/mcp",
            ...     json={"method": "tools/list"}
            ... )
        """
        if not self._jwt_token:
            raise Exception("Not logged in. Call login() first.")

        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {self._jwt_token}"

        url = f"{self.base_url}{endpoint}"
        return requests.request(method, url, headers=headers, **kwargs)
