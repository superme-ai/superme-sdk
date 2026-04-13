"""User profile and search methods."""

from __future__ import annotations

from typing import Any, Optional


class ProfilesMixin:

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

    def perspective_search(self, question: str) -> dict:
        """Get perspectives from multiple experts on a topic.

        Args:
            question: A topic or question to get expert takes on.

        Returns:
            Dict with synthesized answer and individual viewpoints.
        """
        return self._mcp_tool_call("perspective_search", {"question": question})
