"""Social account and blog connection methods."""

from __future__ import annotations

from typing import Any, Optional


class SocialMixin:

    def get_connected_accounts(self, user_id: Optional[str] = None) -> dict:
        """Return connected social accounts for the authenticated user.

        Args:
            user_id: Target user ID. Omit to use the authenticated user.

        Returns:
            Dict with ``connected_accounts`` and ``connected_blogs`` fields.

        Example:
            ```python
            accounts = client.get_connected_accounts()
            for acc in accounts["connected_accounts"]:
                print(acc["platform"], acc["handle"])
            ```
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

        Example:
            ```python
            client.connect_social("x", "myhandle")
            client.connect_social("beehiiv", "my-pub", token="beehiiv_token")
            ```
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
