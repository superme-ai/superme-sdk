"""Workgroup methods — sync.

A *workgroup* is a saved set of SuperMe users (e.g. a project team or advisory
board) that the owner has assembled for repeated reference. Members are SuperMe
users — resolve names via :meth:`find_user_by_name` first.
"""

from __future__ import annotations

from typing import Any, Optional


class WorkgroupsMixin:
    def list_workgroups(self) -> list[dict]:
        """List your workgroups, most recently used first.

        Example:
            ```python
            for g in client.list_workgroups():
                print(g["handle"], g["name"], len(g["members"]))
            ```

        Returns:
            List of workgroup dicts. Each has ``id``, ``handle``, ``name``,
            ``description``, ``members`` (list of ``{user_id, name}``), and
            ``created_at`` / ``updated_at`` / ``last_used_at`` timestamps.
        """
        result = self._mcp_tool_call("list_workgroups", {})
        if isinstance(result, dict):
            groups = result.get("groups", [])
            return groups if isinstance(groups, list) else []
        return []

    def get_workgroup(self, group_id: str) -> Optional[dict]:
        """Get a single workgroup by ID.

        Example:
            ```python
            group = client.get_workgroup("abc123")
            for m in group["members"]:
                print(m["user_id"], m["name"])
            ```

        Returns:
            Workgroup dict, or ``None`` if no group with that ID exists.
        """
        result = self._mcp_tool_call("get_workgroup", {"group_id": group_id})
        if isinstance(result, dict) and "error" not in result:
            return result
        return None

    def create_workgroup(
        self,
        name: str,
        handle: str,
        *,
        description: str = "",
        members: Optional[list[dict]] = None,
    ) -> dict:
        """Create a new workgroup.

        Example:
            ```python
            group = client.create_workgroup(
                name="Growth advisory board",
                handle="growth-board",
                members=[
                    {"user_id": "abc123", "name": "Casey Winters"},
                    {"user_id": "def456", "name": "Elena Verna"},
                ],
            )
            print(group["id"])
            ```

        Args:
            name: Human-readable name.
            handle: Short unique handle within your account.
            description: Optional longer description.
            members: Initial member list, each entry ``{"user_id", "name"}``.
                Resolve names to user_ids via :meth:`find_user_by_name` first.

        Returns:
            The created workgroup dict (or ``{"error": ...}`` if the handle
            is already taken).
        """
        args: dict[str, Any] = {"name": name, "handle": handle}
        if description:
            args["description"] = description
        if members is not None:
            args["members"] = members
        return self._mcp_tool_call("create_workgroup", args)

    def update_workgroup(
        self,
        group_id: str,
        *,
        name: Optional[str] = None,
        handle: Optional[str] = None,
        description: Optional[str] = None,
        members: Optional[list[dict]] = None,
    ) -> dict:
        """Update an existing workgroup you own.

        Only the fields you pass are changed. ``members`` is a full replacement —
        pass the complete desired member list, not a delta.

        Example:
            ```python
            client.update_workgroup(
                "abc123",
                name="Growth advisors (Q2)",
                members=[{"user_id": "abc", "name": "Casey"}],
            )
            ```

        Returns:
            The updated workgroup dict, or ``{"error": ...}`` on conflict /
            not-found.
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
        return self._mcp_tool_call("update_workgroup", args)
