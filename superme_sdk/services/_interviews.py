"""Interview methods."""

from __future__ import annotations

import json


class InterviewsMixin:
    def start_interview(self, role_id: str) -> dict:
        """Start a background agent interview via REST API.

        Returns:
            Dict with ``interview_id`` and ``status`` (initially ``"preparing"``).
            Poll :meth:`get_interview_status` for progress.
        """
        resp = self._rest_http.post(
            "/api/v3/interview/start-agent",
            json={"role_id": role_id},
        )
        self._check_rest_response(resp)
        return resp.json()

    def get_interview_status(self, interview_id: str) -> dict:
        """Poll interview status.

        Returns:
            Dict with ``status``, ``stages``, and other session info.
        """
        resp = self._rest_http.get(f"/api/v3/interview/{interview_id}/status")
        self._check_rest_response(resp)
        return resp.json()

    def get_interview_transcript(self, interview_id: str) -> dict:
        """Get the full transcript for an interview.

        Returns:
            Dict with ``transcript`` list of stages and messages.
        """
        resp = self._rest_http.get(f"/api/v3/interview/{interview_id}/transcript")
        self._check_rest_response(resp)
        return resp.json()

    def list_my_interviews(self) -> list[dict]:
        """List interviews for the authenticated user.

        Returns:
            List of interview summary dicts.
        """
        uid = self.user_id
        if not uid:
            raise ValueError("Cannot extract user_id from token")
        resp = self._rest_http.get(f"/api/v3/interview/by-user/{uid}")
        self._check_rest_response(resp)
        return resp.json().get("interviews", [])

    def stream_interview(self, interview_id: str):
        """Stream interview events via SSE from ``GET /api/v3/interview/{id}/stream``.

        Yields dicts parsed from the SSE ``data:`` lines. Each dict has an
        ``event`` key (``"message"``, ``"status"``, or ``"stage_change"``).

        Terminal statuses (``completed``, ``scoring``, ``scored``, ``failed``,
        ``withdrawn``) cause the generator to return.
        """
        terminal = {"completed", "scoring", "scored", "failed", "withdrawn"}
        with self._rest_http.stream(
            "GET",
            f"/api/v3/interview/{interview_id}/stream",
            headers={"Accept-Encoding": "identity"},
            timeout=None,
        ) as resp:
            resp.raise_for_status()
            buf = ""
            for raw in resp.iter_text():
                buf += raw
                while "\n" in buf:
                    line, buf = buf.split("\n", 1)
                    line = line.strip()
                    if not line or line.startswith(":"):
                        continue
                    if line.startswith("data: "):
                        line = line[6:]
                    elif line.startswith("data:"):
                        line = line[5:]
                    else:
                        continue
                    try:
                        obj = json.loads(line)
                    except (json.JSONDecodeError, ValueError):
                        continue
                    if isinstance(obj, dict):
                        yield obj
                        if obj.get("status") in terminal:
                            return
