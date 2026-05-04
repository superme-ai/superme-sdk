"""Workgroup methods — async.

A *workgroup* is a saved set of SuperMe users (e.g. a project team or advisory
board) that the owner has assembled for repeated reference. Members are SuperMe
users — resolve names via :meth:`find_user_by_name` first.
"""

from __future__ import annotations

from typing import Any, Optional


class AsyncWorkgroupsMixin:
    """Async variants of :class:`~superme_sdk.services._workgroups.WorkgroupsMixin`."""

    async def list_workgroups(self) -> list[dict]:
        """List your workgroups, most recently used first (async)."""
        result = await self._async_mcp_tool_call("list_workgroups", {})
        if isinstance(result, dict):
            groups = result.get("groups", [])
            return groups if isinstance(groups, list) else []
        return []

    async def get_workgroup(self, group_id: str) -> Optional[dict]:
        """Get a single workgroup by ID (async)."""
        result = await self._async_mcp_tool_call(
            "get_workgroup", {"group_id": group_id}
        )
        if isinstance(result, dict) and "error" not in result:
            return result
        return None

    async def create_workgroup(
        self,
        name: str,
        handle: str,
        *,
        description: str = "",
        members: Optional[list[dict]] = None,
    ) -> dict:
        """Create a new workgroup (async)."""
        args: dict[str, Any] = {"name": name, "handle": handle}
        if description:
            args["description"] = description
        if members is not None:
            args["members"] = members
        return await self._async_mcp_tool_call("create_workgroup", args)

    async def update_workgroup(
        self,
        group_id: str,
        *,
        name: Optional[str] = None,
        handle: Optional[str] = None,
        description: Optional[str] = None,
        members: Optional[list[dict]] = None,
    ) -> dict:
        """Update an existing workgroup (async).

        ``members`` is a full replacement — pass the complete desired member list.
        """
        args: dict[str, Any] = {"group_id": group_id}
        if name is not None:
            args["name"] = name
        if handle is not None:
            args["handle"] = handle
        if description is not None:
            args["description"] = description
        if members is not None:
            args["members"] = members
        return await self._async_mcp_tool_call("update_workgroup", args)
