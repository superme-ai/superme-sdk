"""Interview methods — async."""

from __future__ import annotations

import json
from typing import Any, AsyncGenerator

from ..._transport._sse import aiter_sse_lines


class AsyncInterviewsMixin:
    """Async variants of :class:`~superme_sdk.services._interviews.InterviewsMixin`."""

    async def start_interview(self, role_id: str) -> dict:
        """Start a background agent interview via REST API (async).

        Returns:
            Dict with ``interview_id`` and ``status``.
        """
        resp = await self._async_rest_http.post(
            "/api/v3/agent/interview/start",
            json={"role_id": role_id},
        )
        self._check_rest_response(resp)
        return resp.json()

    async def get_interview_status(self, interview_id: str) -> dict:
        """Poll interview status (async).

        Returns:
            Dict with ``status``, ``stages``, and other session info.
        """
        resp = await self._async_rest_http.get(
            f"/api/v3/interview/{interview_id}/status"
        )
        self._check_rest_response(resp)
        return resp.json()

    async def get_interview_transcript(self, interview_id: str) -> dict:
        """Get the full transcript for an interview (async).

        Returns:
            Dict with ``transcript`` list of stages and messages.
        """
        resp = await self._async_rest_http.get(
            f"/api/v3/interview/{interview_id}/transcript"
        )
        self._check_rest_response(resp)
        return resp.json()

    async def list_my_interviews(self) -> list[dict]:
        """List interviews for the authenticated user (async).

        Returns:
            List of interview summary dicts.
        """
        uid = self.user_id
        if not uid:
            raise ValueError("Cannot extract user_id from token")
        resp = await self._async_rest_http.get(f"/api/v3/interview/by-user/{uid}")
        self._check_rest_response(resp)
        return resp.json().get("interviews", [])

    async def send_interview_message(
        self,
        interview_id: str,
        message: str,
        *,
        stage_number: int | None = None,
        attachments: list[dict[str, Any]] | None = None,
    ) -> dict:
        """Send a candidate message during an AWAITING_INPUT stage (async).

        Returns:
            Dict with ``interview_id``, ``stage_name``, ``message``, and
            ``next_manual_stage``.
        """
        payload: dict[str, Any] = {"message": message}
        if stage_number is not None:
            payload["stage_number"] = stage_number
        if attachments is not None:
            payload["attachments"] = attachments
        resp = await self._async_rest_http.post(
            f"/api/v3/agent/interview/{interview_id}/message",
            json=payload,
        )
        self._check_rest_response(resp)
        return resp.json()

    async def stream_interview(self, interview_id: str) -> AsyncGenerator[dict, None]:
        """Stream interview events via SSE (async).

        Example:
            ```python
            async for event in client.stream_interview("interview_abc123"):
                if event.get("event") == "message":
                    print(event["content"])
                elif event.get("event") == "status":
                    print("status:", event["status"])
            ```

        Yields dicts parsed from the SSE ``data:`` lines. Each dict has an
        ``event`` key (``"message"``, ``"status"``, or ``"stage_change"``).

        Terminal statuses (``completed``, ``scoring``, ``scored``, ``failed``,
        ``withdrawn``) cause the generator to return.
        """
        terminal = {"completed", "scoring", "scored", "failed", "withdrawn"}
        async with self._async_rest_http.stream(
            "GET",
            f"/api/v3/agent/interview/{interview_id}/stream",
            headers={"Accept-Encoding": "identity"},
            timeout=None,
        ) as resp:
            if not resp.is_success:
                await resp.aread()
            self._check_rest_response(resp)
            async for line in aiter_sse_lines(resp):
                try:
                    obj = json.loads(line)
                except (json.JSONDecodeError, ValueError):
                    continue
                if isinstance(obj, dict):
                    yield obj
                    if obj.get("status") in terminal:
                        return
