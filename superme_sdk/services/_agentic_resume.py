"""Agentic resume methods."""

from __future__ import annotations


class AgenticResumeMixin:
    def get_agentic_resume(self) -> dict:
        """Fetch the authenticated user's agentic resume.

        Example:
            ```python
            resume = client.get_agentic_resume()
            print(resume["structured_data"])
            ```

        Returns:
            Dict with ``structured_data``, ``raw_markdown``, ``html``,
            ``created_at``, and ``updated_at``.
            Returns ``{"structured_data": None}`` when no resume exists yet
            (the backend returns 404 in that case).
        """
        resp = self._rest_http.get("/api/v3/agentic-resume")
        if resp.status_code == 404:
            return {"structured_data": None}
        self._check_rest_response(resp)
        return resp.json()

    def create_agentic_resume_token(self) -> dict:
        """Generate a one-time upload token for agentic resume ingestion.

        This token is used by external agents (e.g. Claude Code) to upload
        raw resume markdown.  The workflow is:

        1. Call this method to get a ``token``, ``upload_url``, and
           ``instructions_url``.
        2. Give the ``instructions_url`` to an AI agent.
        3. The agent reads the instructions and POSTs markdown to
           ``upload_url``.
        4. The backend synthesises the structured resume in the background.

        Example:
            ```python
            result = client.create_agentic_resume_token()
            print(result["upload_url"])      # one-time upload endpoint
            print(result["instructions_url"])  # agent instructions markdown
            ```

        Returns:
            Dict with ``token``, ``upload_url``, ``instructions_url``,
            and ``expires_at`` (ISO-8601, 1-hour TTL).
        """
        resp = self._rest_http.post("/api/v3/agentic-resume/token")
        self._check_rest_response(resp)
        return resp.json()

    def regenerate_agentic_resume(self) -> dict:
        """Re-synthesize the agentic resume from stored raw markdown.

        Example:
            ```python
            result = client.regenerate_agentic_resume()
            print(result["structured_data"])
            ```

        Returns:
            Dict with ``structured_data`` and ``html`` after re-synthesis.
        """
        resp = self._rest_http.post("/api/v3/agentic-resume/regenerate")
        self._check_rest_response(resp)
        return resp.json()
