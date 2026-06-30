"""User profile and search methods — async."""

from __future__ import annotations

from typing import Any, Optional


class AsyncProfilesMixin:
    """Async variants of :class:`~superme_sdk.services._profiles.ProfilesMixin`."""

    async def get_profile(self, identifier: Optional[str] = None) -> dict:
        """Return public profile info for a user (async).

        Omit ``identifier`` for your own profile (reads ``superme://me/profile``);
        pass one to look up another user via ``user_profile_search``.
        """
        if not identifier:
            result = await self._async_mcp_read_resource("superme://me/profile")
            return result if isinstance(result, dict) else {}
        result = await self._async_mcp_tool_call(
            "user_profile_search", {"identifier": identifier}
        )
        users = result.get("users", []) if isinstance(result, dict) else []
        return users[0] if users else {}

    async def get_user_details(self, identifier: str) -> dict:
        """Read one user's full public profile by user_id or username (async).

        Deeper than :meth:`get_profile` — returns the un-truncated summary plus
        structured work experience, education, and skills.
        """
        result = await self._async_mcp_tool_call(
            "user_details_read", {"identifier": identifier}
        )
        return result if isinstance(result, dict) else {}

    async def find_user_by_name(self, name: str, *, limit: int = 10) -> dict:
        """Search for SuperMe users by name (async)."""
        return await self._async_mcp_tool_call(
            "user_profile_search", {"identifier": name, "limit": limit}
        )

    async def find_users_by_names(
        self, names: list[str], *, limit_per_name: int = 10
    ) -> dict:
        """Resolve multiple names to SuperMe users in a single call (async)."""
        return await self._async_mcp_tool_call(
            "user_profile_search",
            {"identifier": names, "limit": limit_per_name},
        )

    async def find_users_on_topic(
        self,
        question: str,
        *,
        max_results: int = 10,
        excluded_user_ids: list[str] | None = None,
    ) -> dict:
        """Find SuperMe users who are experts on a topic (async)."""
        args: dict[str, Any] = {"question": question, "max_results": max_results}
        if excluded_user_ids is not None:
            args["excluded_user_ids"] = excluded_user_ids
        return await self._async_mcp_tool_call("user_expert_search", args)
