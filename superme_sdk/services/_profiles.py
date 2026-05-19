"""User profile and search methods."""

from __future__ import annotations

from typing import Any, Optional


class ProfilesMixin:
    def get_profile(self, identifier: Optional[str] = None) -> dict:
        """Return profile info for a user.

        Example:
            ```python
            # your own profile
            me = client.get_profile()
            # another user — returns {"users": [...], "workgroups": [...]}
            result = client.get_profile("ludo")
            ```

        Args:
            identifier: User ID, username, or full name. Omit for your own profile.

        Returns:
            Own profile dict when called with no identifier; ``{"users", "workgroups"}``
            dict when an identifier is supplied.
        """
        if not identifier:
            return self._mcp_tool_call("get_my_profile", {})
        return self._mcp_tool_call("find_profiles", {"identifier": identifier})

    def find_user_by_name(self, name: str, *, limit: int = 10) -> dict:
        """Search for SuperMe users by name.

        Example:
            ```python
            result = client.find_user_by_name("ludo")
            for u in result["users"]:
                print(u["user_id"], u["name"])
            ```

        Args:
            name: Full or partial name to search for.
            limit: Maximum results to return.

        Returns:
            Dict with ``users`` (list of matches) and ``workgroups`` keys.
        """
        return self._mcp_tool_call(
            "find_profiles", {"identifier": name, "limit": limit}
        )

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
            Dict with ``results``, ``resolved_user_ids``, and ``unresolved`` keys.
        """
        return self._mcp_tool_call(
            "find_profiles",
            {"identifier": names, "limit": limit_per_name},
        )

    def find_users_on_topic(
        self,
        question: str,
        *,
        max_results: int = 10,
        excluded_user_ids: list[str] | None = None,
    ) -> dict:
        """Find SuperMe users who are experts on a topic.

        Example:
            ```python
            result = client.find_users_on_topic("product-led growth")
            for expert in result["experts"]:
                print(expert["user_name"], expert["why_selected"])
            ```

        Args:
            question: A topic or question to find experts on.
            max_results: Maximum number of experts to return (1-20, default 10).
            excluded_user_ids: User IDs to exclude from results.

        Returns:
            Dict with ``question`` and ``experts`` list, each having ``user_id``,
            ``user_name``, ``why_selected``, and ``relevance_score``.
        """
        args: dict[str, Any] = {"question": question, "max_results": max_results}
        if excluded_user_ids is not None:
            args["excluded_user_ids"] = excluded_user_ids
        return self._mcp_tool_call("find_experts", args)

    def perspective_search(self, question: str) -> dict:
        """Get perspectives from multiple experts on a topic.

        Example:
            ```python
            result = client.perspective_search("What is product-market fit?")
            print(result["synthesis"])
            for p in result["perspectives"]:
                print(p["expert_name"], p["perspective"])
            ```

        Args:
            question: A topic or question to get expert takes on.

        Returns:
            Dict with ``perspectives`` list and ``synthesis`` string.
        """
        return self._mcp_tool_call("search_perspective", {"question": question})
