"""Library (knowledge base) methods."""

from __future__ import annotations

from typing import Any, Optional


class LibraryMixin:
    def get_learnings(
        self,
        *,
        limit: Optional[int] = None,
        offset: int = 0,
        collection: Optional[str] = None,
        platform: Optional[str] = None,
        title_keyword: Optional[str] = None,
        privacy_filter: Optional[str] = None,
        unread_only: bool = False,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> dict:
        """List knowledge items in the authenticated user's library.

        Example:
            ```python
            page = client.get_learnings(limit=20)
            for item in page["items"]:
                print(item["learning_id"], item["title"])

            # filter to external content only
            page = client.get_learnings(collection="external", limit=10)
            ```

        Args:
            limit: Maximum items to return. Omit for backend default.
            offset: Pagination offset (default 0).
            collection: Filter by type — ``"internal"``, ``"external"``,
                or ``"social"``.
            platform: Filter by source platform (e.g. ``"medium"``).
            title_keyword: Substring search on item title.
            privacy_filter: One of ``"public"``, ``"network"``, ``"private"``.
            unread_only: Return only unread items.
            date_from: ISO-8601 lower bound on ``content_published_at``.
            date_to: ISO-8601 upper bound on ``content_published_at``.

        Returns:
            Dict with ``items`` list and pagination info.
        """
        uid = self.user_id
        if not uid:
            raise ValueError("Cannot extract user_id from token")

        params: dict[str, Any] = {"user_id": uid, "offset": offset}
        if limit is not None:
            params["limit"] = limit
        if collection is not None:
            params["collection"] = collection
        if platform is not None:
            params["platform"] = platform
        if title_keyword is not None:
            params["title_keyword"] = title_keyword
        if privacy_filter is not None:
            params["privacy_filter"] = privacy_filter
        if unread_only:
            params["unread_only"] = True
        if date_from is not None:
            params["date_from"] = date_from
        if date_to is not None:
            params["date_to"] = date_to

        resp = self._rest_http.get("/api/v3/library", params=params)
        self._check_rest_response(resp)
        return resp.json()

    def get_learning(self, learning_id: str) -> dict:
        """Fetch a single library item by ID.

        Example:
            ```python
            item = client.get_learning("learning_abc123")
            print(item["title"], item["summary"])
            ```

        Args:
            learning_id: The learning ID (from :meth:`get_learnings`).

        Returns:
            Dict with full learning metadata and content.
        """
        resp = self._rest_http.get(
            "/api/v3/library/getlearning", params={"learning_id": learning_id}
        )
        self._check_rest_response(resp)
        return resp.json()

    def search_library(
        self,
        query: str,
        *,
        platform: Optional[str] = None,
        limit: int = 20,
    ) -> dict:
        """Search the authenticated user's own library by free-text query.

        Hybrid (semantic + lexical) search across notes, links, and social
        posts. Includes drafts and private rows because the search is
        self-scoped.

        Example:
            ```python
            page = client.search_library("retrieval evaluation")
            for hit in page["results"]:
                print(hit["score"], hit["text"][:80])

            # Filter to one platform
            page = client.search_library("growth", platform="medium", limit=5)
            ```

        Args:
            query: Free-text search query (required, non-empty).
            platform: Optional platform filter (e.g. ``"medium"``, ``"x"``,
                ``"linkedin"``, ``"github"``, ``"notion"``). ``None`` runs
                across notes + links + social.
            limit: Max excerpts to return (1-50, default 20).

        Returns:
            Dict with ``success`` and ``results`` — a list of excerpts shaped
            like ``InsightExcerpt`` (id, score, text, type, platform, url,
            chunk_index, date, ...).
        """
        if not query or not query.strip():
            raise ValueError("query must be a non-empty string")
        if not 1 <= limit <= 50:
            raise ValueError("limit must be between 1 and 50")

        uid = self.user_id
        if not uid:
            raise ValueError("Cannot extract user_id from token")

        params: dict[str, Any] = {
            "user_id": uid,
            "query": query,
            "limit": limit,
        }
        if platform is not None:
            params["platform"] = platform

        resp = self._rest_http.get("/api/v3/library/search", params=params)
        self._check_rest_response(resp)
        return resp.json()

    def get_ingestion_status(self) -> dict:
        """Check the ingestion status of the authenticated user's library.

        Returns a summary of how many items are pending, processing, done,
        or failed. Useful to poll after :meth:`add_external_content` to know
        when URLs finish processing.

        Example:
            ```python
            status = client.get_ingestion_status()
            print(status)
            ```

        Returns:
            Dict with ingestion counts and status breakdown.
        """
        uid = self.user_id
        if not uid:
            raise ValueError("Cannot extract user_id from token")

        resp = self._rest_http.get("/api/v3/library/ingestion", params={"user_id": uid})
        self._check_rest_response(resp)
        return resp.json()
