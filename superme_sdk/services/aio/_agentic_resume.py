"""Agentic resume methods — async."""

from __future__ import annotations


class AsyncAgenticResumeMixin:
    """Async variants of :class:`~superme_sdk.services._agentic_resume.AgenticResumeMixin`."""

    async def get_agentic_resume(self) -> dict:
        """Fetch the authenticated user's agentic resume (async).

        Returns:
            Dict with ``structured_data``, ``raw_markdown``, ``html``,
            ``created_at``, and ``updated_at``.
            Returns ``{"structured_data": None}`` when no resume exists yet.
        """
        resp = await self._async_rest_http.get("/api/v3/agentic-resume")
        if resp.status_code == 404:
            return {
                "structured_data": None,
                "raw_markdown": None,
                "html": None,
                "created_at": None,
                "updated_at": None,
            }
        self._check_rest_response(resp)
        return resp.json()

    async def create_agentic_resume_token(self) -> dict:
        """Generate a one-time upload token for agentic resume ingestion (async).

        Returns:
            Dict with ``token``, ``upload_url``, ``instructions_url``,
            and ``expires_at`` (ISO-8601, 1-hour TTL).
        """
        resp = await self._async_rest_http.post("/api/v3/agentic-resume/token")
        self._check_rest_response(resp)
        return resp.json()

    async def regenerate_agentic_resume(self) -> dict:
        """Re-synthesize the agentic resume from stored raw markdown (async).

        Returns:
            Dict with ``structured_data`` and ``html`` after re-synthesis.
        """
        resp = await self._async_rest_http.post("/api/v3/agentic-resume/regenerate")
        self._check_rest_response(resp)
        return resp.json()
