"""Group conversation methods — async."""

from __future__ import annotations

import json
from typing import Any, AsyncGenerator, Optional

from ..._transport._sse import aiter_sse_lines


class AsyncGroupsMixin:
    """Async variants of :class:`~superme_sdk.services._groups.GroupsMixin`.

    Note: ``group_converse()`` (non-streaming) is sync-only.
    Use ``group_converse_stream()`` here for async access.
    """

    async def group_converse_stream(
        self,
        participants: list[str],
        topic: str,
        *,
        max_turns: int = 3,
        conversation_id: Optional[str] = None,
    ) -> AsyncGenerator[dict, None]:
        """Stream a group conversation, yielding each perspective as it completes (async).

        Example:
            ```python
            async for event in client.group_converse_stream(
                participants=["ludo", "duy"],
                topic="What is the future of AI agents?",
            ):
                if event.get("_done"):
                    print("conversation_id:", event["conversation_id"])
                else:
                    print(event["user_name"], event["content"])
            ```

        Yields dicts with keys: type, user_name, content, turn, user_id.
        Final yield: ``{"type": "done", "conversation_id": str, "_done": True}``.
        """
        payload: dict[str, Any] = {
            "participants": participants,
            "topic": topic,
            "max_turns": max_turns,
        }
        if conversation_id is not None:
            payload["conversation_id"] = conversation_id

        async with self._async_http.stream(
            "POST",
            "/mcp/chat/stream/group_converse",
            json=payload,
            headers={"Accept-Encoding": "identity"},
        ) as resp:
            if not resp.is_success:
                await resp.aread()
            self._check_rest_response(resp)
            async for line in aiter_sse_lines(resp):
                try:
                    obj = json.loads(line)
                except (json.JSONDecodeError, ValueError):
                    continue
                if not isinstance(obj, dict):
                    continue
                if obj.get("type") == "done":
                    obj["_done"] = True
                yield obj
