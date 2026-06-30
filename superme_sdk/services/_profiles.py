"""User profile and search methods."""

from __future__ import annotations

from typing import Any, Optional


class ProfilesMixin:
    def get_profile(self, identifier: Optional[str] = None) -> dict:
        """Return public profile info for a user.

        Example:
            ```python
            me = client.get_profile()
            profile = client.get_profile("ludo")
            print(profile["name"], profile["user_id"])
            ```

        Args:
            identifier: User ID, username, or full name. Omit for your own
                profile.

        Returns:
            When called without ``identifier`` (own profile): dict with
            ``name``, ``title``, ``location``, ``avatar_image``, and joined
            communities. When called with ``identifier``: flat profile dict with
            ``user_id``, ``in_network``, ``name``, and other public fields.
            Returns ``{}`` if no match is found.
        """
        if not identifier:
            result = self._mcp_read_resource("superme://me/profile")
            return result if isinstance(result, dict) else {}
        result = self._mcp_tool_call("user_profile_search", {"identifier": identifier})
        users = result.get("users", []) if isinstance(result, dict) else []
        return users[0] if users else {}

    def get_user_details(self, identifier: str) -> dict:
        """Read one user's full public profile by user_id or username.

        Unlike :meth:`get_profile` (a search card — name, title, location), this
        returns the deep profile: un-truncated summary plus structured work
        experience, education, and skills. Resolve a name to a user_id or
        username with :meth:`find_user_by_name` first.

        Example:
            ```python
            details = client.get_user_details("elena-verna")
            print(details["summary"])
            for job in details["work_experience"]:
                print(job["company"], job["title"])
            ```

        Args:
            identifier: A user_id or username (from a search result).

        Returns:
            Profile dict with ``user_id``, ``name``, ``title``, ``company``,
            ``summary``, ``skills``, ``work_experience``, and ``education``.
            Contains an ``error`` key if the profile is missing or not visible.
        """
        result = self._mcp_tool_call("user_details_read", {"identifier": identifier})
        return result if isinstance(result, dict) else {}

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
            "user_profile_search", {"identifier": name, "limit": limit}
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
            "user_profile_search",
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
        return self._mcp_tool_call("user_expert_search", args)
