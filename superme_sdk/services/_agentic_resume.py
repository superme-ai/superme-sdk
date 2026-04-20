"""Agentic resume methods."""

from __future__ import annotations


class AgenticResumeMixin:
    def generate_resume_token(self) -> dict:
        """Generate a one-time upload token for the agentic resume flow.

        Returns:
            Dict with ``token`` and ``instructions_url`` for the agent to fetch.
        """
        resp = self._rest_http.post("/api/v3/agentic-resume/token")
        self._check_rest_response(resp)
        return resp.json()

    def get_resume_instructions(self, token: str) -> str:
        """Fetch the markdown prompt that tells the agent how to build the resume.

        Args:
            token: One-time token from :meth:`generate_resume_token`.

        Returns:
            Markdown string with instructions and the upload URL embedded.
        """
        resp = self._rest_http.get(
            f"/api/v3/agentic-resume/instructions/{token}",
            headers={"Accept": "text/markdown"},
        )
        self._check_rest_response(resp)
        return resp.text

    def upload_resume(self, token: str, markdown: str) -> dict:
        """Upload raw resume markdown via a one-time token.

        The server accepts the payload, stores raw markdown, and triggers
        LLM synthesis in the background.  The caller should poll
        :meth:`get_resume` until the structured data appears.

        Args:
            token: One-time token from :meth:`generate_resume_token`.
            markdown: Raw resume text in markdown format (max 500 KB).

        Returns:
            Dict with ``status: "accepted"`` on success.
        """
        resp = self._rest_http.post(
            f"/api/v3/agentic-resume/upload/{token}",
            content=markdown.encode(),
            headers={"Content-Type": "text/plain"},
        )
        self._check_rest_response(resp)
        return resp.json()

    def get_resume(self) -> dict:
        """Read the authenticated user's synthesized resume.

        Returns:
            Dict with ``structured_data`` and ``html`` fields.

        Raises:
            httpx.HTTPStatusError: 404 if no resume has been uploaded yet.
        """
        resp = self._rest_http.get("/api/v3/agentic-resume/")
        self._check_rest_response(resp)
        return resp.json()

    def regenerate_resume(self) -> dict:
        """Re-synthesize the resume from stored raw data using the LLM.

        Returns:
            Dict with updated ``structured_data`` and ``html``.
        """
        resp = self._rest_http.post("/api/v3/agentic-resume/regenerate")
        self._check_rest_response(resp)
        return resp.json()
