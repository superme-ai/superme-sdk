"""Group conversation methods."""

from __future__ import annotations

import json
from typing import Any, Optional


class GroupsMixin:

    def group_converse(
        self,
        participants: list[str],
        topic: str,
        *,
        max_turns: int = 3,
        conversation_id: Optional[str] = None,
    ) -> dict:
        """Start or continue a multi-turn group conversation.

        Args:
            participants: People to include — names, usernames, or user IDs.
                At least 2 must resolve to known users.
            topic: The topic or question for the group to discuss.
            max_turns: Maximum conversation turns (1-5, default 3).
            conversation_id: Continue an existing conversation. Omit to start new.

        Returns:
            Dict with conversation_id, perspectives, participant_ids, and
            any unresolved identifiers.
        """
        args: dict[str, Any] = {
            "participants": participants,
            "topic": topic,
        }
        if max_turns != 3:
            args["max_turns"] = max_turns
        if conversation_id is not None:
            args["conversation_id"] = conversation_id
        return self._mcp_tool_call("group_converse", args)

    def group_converse_stream(
        self,
        participants: list[str],
        topic: str,
        *,
        max_turns: int = 3,
        conversation_id: Optional[str] = None,
    ):
        """Stream a group conversation, yielding each perspective as it completes.

        Yields dicts with keys: type, user_name, content, turn, user_id.
        Final yield: {"type": "done", "conversation_id": str, "_done": True}.
        """
        payload: dict[str, Any] = {
            "participants": participants,
            "topic": topic,
            "max_turns": max_turns,
        }
        if conversation_id:
            payload["conversation_id"] = conversation_id

        with self._http.stream(
            "POST",
            "/mcp/chat/stream/group_converse",
            json=payload,
            headers={"Accept-Encoding": "identity"},
        ) as resp:
            resp.raise_for_status()

            buf = ""
            for raw_chunk in resp.iter_text():
                buf += raw_chunk
                while "\n" in buf:
                    line, buf = buf.split("\n", 1)
                    line = line.strip()
                    if not line:
                        continue
                    if line.startswith("data: "):
                        line = line[6:]
                    elif line.startswith("data:"):
                        line = line[5:]
                    try:
                        obj = json.loads(line)
                    except (json.JSONDecodeError, ValueError):
                        continue
                    if not isinstance(obj, dict):
                        continue
                    if obj.get("type") == "done":
                        obj["_done"] = True
                    yield obj
