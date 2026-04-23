"""Interview methods — sync."""

from __future__ import annotations

import json
from typing import Any

from .._sse import iter_sse_lines


class InterviewsMixin:
    def start_interview(self, role_id: str) -> dict:
        """Start a background agent interview via REST API.

        Example:
            ```python
            session = client.start_interview("role_abc123")
            interview_id = session["interview_id"]
            ```

        Returns:
            Dict with ``interview_id`` and ``status`` (initially ``"preparing"``).
            Poll :meth:`get_interview_status` for progress.
        """
        resp = self._rest_http.post(
            "/api/v3/agent/interview/start",
            json={"role_id": role_id},
        )
        self._check_rest_response(resp)
        return resp.json()

    def get_interview_status(self, interview_id: str) -> dict:
        """Poll interview status.

        Example:
            ```python
            status = client.get_interview_status("interview_abc123")
            print(status["status"])  # "preparing", "in_progress", "completed", ...
            ```

        Returns:
            Dict with ``status``, ``stages``, and other session info.
        """
        resp = self._rest_http.get(f"/api/v3/interview/{interview_id}/status")
        self._check_rest_response(resp)
        return resp.json()

    def get_interview_transcript(self, interview_id: str) -> dict:
        """Get the full transcript for an interview.

        Example:
            ```python
            transcript = client.get_interview_transcript("interview_abc123")
            for stage in transcript["transcript"]:
                print(stage)
            ```

        Returns:
            Dict with ``transcript`` list of stages and messages.
        """
        resp = self._rest_http.get(f"/api/v3/interview/{interview_id}/transcript")
        self._check_rest_response(resp)
        return resp.json()

    def list_my_interviews(self) -> list[dict]:
        """List interviews for the authenticated user.

        Example:
            ```python
            interviews = client.list_my_interviews()
            for i in interviews:
                print(i["interview_id"], i["status"])
            ```

        Returns:
            List of interview summary dicts.
        """
        uid = self.user_id
        if not uid:
            raise ValueError("Cannot extract user_id from token")
        resp = self._rest_http.get(f"/api/v3/interview/by-user/{uid}")
        self._check_rest_response(resp)
        return resp.json().get("interviews", [])

    def send_interview_message(
        self,
        interview_id: str,
        message: str,
        *,
        stage_number: int | None = None,
        attachments: list[dict[str, Any]] | None = None,
    ) -> dict:
        """Send a candidate message during an AWAITING_INPUT stage.

        Example:
            ```python
            reply = client.send_interview_message(
                "interview_abc123",
                "I have 5 years of experience building distributed systems.",
            )
            print(reply["message"])  # interviewer's reply
            print(reply["stage_name"])
            ```

        Args:
            interview_id: The interview session ID.
            message: The candidate's message text.
            stage_number: Optional stage number for manual-stage interviews.
            attachments: Optional list of ``{gcs_path, filename, content_type}`` dicts.

        Returns:
            Dict with ``interview_id``, ``stage_name``, ``message`` (interviewer reply),
            and ``next_manual_stage``.
        """
        payload: dict[str, Any] = {"message": message}
        if stage_number is not None:
            payload["stage_number"] = stage_number
        if attachments is not None:
            payload["attachments"] = attachments
        resp = self._rest_http.post(
            f"/api/v3/agent/interview/{interview_id}/message",
            json=payload,
        )
        self._check_rest_response(resp)
        return resp.json()

    def submit_interview(self, interview_id: str) -> dict:
        """Submit a completed interview for scoring.

        Example:
            ```python
            result = client.submit_interview("interview_abc123")
            print(result["status"])  # "submitted"
            ```

        Args:
            interview_id: The interview session ID.

        Returns:
            Dict with updated interview status.
        """
        resp = self._rest_http.post(f"/api/v3/interview/{interview_id}/submit")
        self._check_rest_response(resp)
        return resp.json()

    def send_interview_feedback(
        self,
        interview_id: str,
        stage_number: int,
        rating: int,
        comments: str,
    ) -> dict:
        """Leave feedback on an interview stage.

        Example:
            ```python
            result = client.send_interview_feedback(
                "interview_abc123",
                stage_number=1,
                rating=4,
                comments="Good questions, well-structured.",
            )
            ```

        Args:
            interview_id: The interview session ID.
            stage_number: The stage number to leave feedback on.
            rating: Rating from 1 to 5.
            comments: Feedback comments text.

        Returns:
            Dict with feedback confirmation.
        """
        resp = self._rest_http.post(
            f"/api/v3/agent/interview/{interview_id}/feedback",
            json={
                "stage_number": stage_number,
                "rating": rating,
                "comments": comments,
            },
        )
        self._check_rest_response(resp)
        return resp.json()

    def stream_interview(self, interview_id: str):
        """Stream interview events via SSE from ``GET /api/v3/agent/interview/{id}/stream``.

        Example:
            ```python
            for event in client.stream_interview("interview_abc123"):
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
        with self._rest_http.stream(
            "GET",
            f"/api/v3/agent/interview/{interview_id}/stream",
            headers={"Accept-Encoding": "identity"},
            timeout=None,
        ) as resp:
            if not resp.is_success:
                resp.read()
            self._check_rest_response(resp)
            for line in iter_sse_lines(resp):
                try:
                    obj = json.loads(line)
                except (json.JSONDecodeError, ValueError):
                    continue
                if isinstance(obj, dict):
                    yield obj
                    if obj.get("status") in terminal:
                        return


