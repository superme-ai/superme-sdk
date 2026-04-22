"""User profile and search methods."""

from __future__ import annotations

from typing import Any, Optional


class ProfilesMixin:
    def get_profile(self, identifier: Optional[str] = None) -> dict:
        """Return public profile info for a user.

        Example:
            ```python
            profile = client.get_profile("ludo")
            # or your own profile
            me = client.get_profile()
            ```

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

        Example:
            ```python
            results = client.find_user_by_name("ludo")
            ```

        Args:
            name: Full or partial name to search for.
            limit: Maximum results to return.

        Returns:
            Dict with match results.
        """
        return self._mcp_tool_call("find_user_by_name", {"name": name, "limit": limit})

    def find_users_by_names(
        self, names: list[str], *, limit_per_name: int = 10
    ) -> dict:
        """Resolve multiple names to SuperMe users in a single call.

        Example:
            ```python
            result = client.find_users_by_names(["ludo", "duy"])
            ids = result["resolved_user_ids"]
            ```

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

    def find_users_on_topic(
        self,
        question: str,
        *,
        max_results: int = 10,
        excluded_user_ids: list[str] | None = None,
    ) -> dict:
        """Find SuperMe users who are experts on a topic.

        Unlike :meth:`perspective_search` (which returns answers), this returns
        *who* knows about the topic — useful for resolving experts before calling
        :meth:`ask`.

        Example:
            ```python
            result = client.find_users_on_topic("product-led growth")
            for expert in result["users"]:
                print(expert["username"], expert["score"])
            ```

        Args:
            question: A topic or question to find experts on.
            max_results: Maximum number of experts to return (1-20, default 10).
            excluded_user_ids: User IDs to exclude from results.

        Returns:
            Dict with ``users`` list, each having ``username``, ``user_id``,
            and relevance info.
        """
        args: dict[str, Any] = {"question": question, "max_results": max_results}
        if excluded_user_ids is not None:
            args["excluded_user_ids"] = excluded_user_ids
        return self._mcp_tool_call("find_users_on_topic", args)

    def perspective_search(self, question: str) -> dict:
        """Get perspectives from multiple experts on a topic.

        Example:
            ```python
            result = client.perspective_search("What is product-market fit?")
            print(result["answer"])
            for view in result["viewpoints"]:
                print(view["username"], view["content"])
            ```

        Args:
            question: A topic or question to get expert takes on.

        Returns:
            Dict with synthesized answer and individual viewpoints.
        """
        return self._mcp_tool_call("perspective_search", {"question": question})
