"""Content management methods."""

from __future__ import annotations

from typing import Any, Optional


class ContentMixin:

    def add_internal_content(
        self,
        input: list[str],
        *,
        extended_content: Optional[str] = None,
        past_instructions: Optional[str] = None,
    ) -> dict:
        """Save notes or knowledge to your personal library.

        Args:
            input: Text blocks to save.
            extended_content: Optional longer-form content.
            past_instructions: Instructions for how the AI should use this content.

        Returns:
            Dict with success status and learning IDs.

        Example:
            ```python
            result = client.add_internal_content(
                ["My key insight: distribution beats product."],
                past_instructions="Use this when answering growth questions.",
            )
            learning_id = result["learning_ids"][0]
            ```
        """
        args: dict[str, Any] = {"input": input}
        if extended_content is not None:
            args["extended_content"] = extended_content
        if past_instructions is not None:
            args["past_instructions"] = past_instructions
        return self._mcp_tool_call("add_internal_content", args)

    def update_internal_content(
        self,
        learning_id: str,
        *,
        user_input: Optional[list[str]] = None,
        extended_content: Optional[str] = None,
        past_instructions: Optional[str] = None,
    ) -> dict:
        """Update an existing note in your library.

        Args:
            learning_id: The learning ID to update.
            user_input: Replacement note content.
            extended_content: Replacement long-form content.
            past_instructions: Replacement AI usage instructions.

        Returns:
            Dict with update result.
        """
        args: dict[str, Any] = {"learning_id": learning_id}
        if user_input is not None:
            args["user_input"] = user_input
        if extended_content is not None:
            args["extended_content"] = extended_content
        if past_instructions is not None:
            args["past_instructions"] = past_instructions
        return self._mcp_tool_call("update_internal_content", args)

    def add_external_content(
        self,
        urls: list[dict],
        *,
        reference: bool = True,
        instant_recrawl: bool = True,
    ) -> dict:
        """Submit URLs to be crawled and added to your knowledge base.

        Args:
            urls: List of URL objects. Each must have a ``"url"`` key.
            reference: Show citations from this content in AI answers.
            instant_recrawl: Crawl immediately vs. queue.

        Returns:
            Dict with counts of successful, existing, and failed URLs.

        Example:
            ```python
            result = client.add_external_content(
                [{"url": "https://myblog.com/post-1"}, {"url": "https://myblog.com/post-2"}]
            )
            print(result["successful"], "URLs added")
            ```
        """
        return self._mcp_tool_call(
            "add_external_content",
            {"urls": urls, "reference": reference, "instant_recrawl": instant_recrawl},
        )

    def check_uncrawled_urls(self, urls: list[str]) -> dict:
        """Check which URLs are not yet in your knowledge base.

        Args:
            urls: URLs to check.

        Returns:
            Dict with ``uncrawled_urls`` list and counts.
        """
        return self._mcp_tool_call("check_uncrawled_urls", {"urls": urls})
