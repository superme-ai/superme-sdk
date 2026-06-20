"""Async provisioning methods."""

from __future__ import annotations

import asyncio
from typing import Any, Optional


_BATCH_CONCURRENCY = 10


class AsyncProvisionMixin:
    async def provision_create(
        self,
        community_id: str,
        *,
        name: str,
        linkedin_url: str,
        contact_email: Optional[str] = None,
        notes: Optional[str] = None,
        socials: Optional[dict[str, str]] = None,
        external_urls: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        """Provision a single community member (async).

        Args:
            community_id: The community to provision into.
            name: Full name of the person being provisioned.
            linkedin_url: LinkedIn profile URL (``linkedin.com/in/<slug>``).
            contact_email: Email address for invite delivery.
            notes: Community-scoped note (e.g. intro context, WhatsApp note).
            socials: Platform handles, e.g. ``{"x": "janesmith"}``.
            external_urls: URLs to import into the person's knowledge base.

        Returns:
            Dict with ``provision`` record including ``user_id``, ``token``,
            ``claim_url``, and ``status``.
        """
        body: dict[str, Any] = {
            "community_id": community_id,
            "name": name,
            "linkedin_url": linkedin_url,
        }
        if contact_email is not None:
            body["contact_email"] = contact_email
        if notes is not None:
            body["notes"] = notes
        if socials is not None:
            body["socials"] = socials
        if external_urls is not None:
            body["external_urls"] = external_urls

        resp = await self._async_rest_http.post(
            f"/api/v3/provision/{community_id}", json=body
        )
        self._check_rest_response(resp)
        return resp.json()

    async def provision_create_batch(
        self,
        community_id: str,
        profiles: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Provision multiple community members concurrently (async).

        Fans out up to 10 concurrent :meth:`provision_create` calls.
        Results are in the same order as ``profiles``; failed items have an
        ``"error"`` key instead of ``"provision"``.

        Args:
            community_id: The community to provision into.
            profiles: List of profile dicts (``name``, ``linkedin_url``,
                ``contact_email``, ``notes``, ``socials``, ``external_urls``).

        Returns:
            List of result dicts in the same order as ``profiles``.
        """
        sem = asyncio.Semaphore(_BATCH_CONCURRENCY)

        async def _one(profile: dict[str, Any]) -> dict[str, Any]:
            async with sem:
                return await self.provision_create(community_id, **profile)

        tasks = [asyncio.create_task(_one(p)) for p in profiles]
        results = []
        for task in tasks:
            try:
                results.append(await task)
            except Exception as exc:  # noqa: BLE001
                results.append({"error": str(exc)})
        return results

    async def provision_send_invites(
        self,
        community_id: str,
        user_ids: list[str],
    ) -> dict[str, Any]:
        """Send invite emails to provisioned members (async).

        Args:
            community_id: The community whose provisions to invite.
            user_ids: List of provisioned user IDs to send invites to.

        Returns:
            Dict with ``sent``, ``skipped``, and ``failed`` lists.
        """
        resp = await self._async_rest_http.post(
            f"/api/v3/provision/{community_id}/invite",
            json={"community_id": community_id, "user_ids": user_ids},
        )
        self._check_rest_response(resp)
        return resp.json()

    async def provision_list(self, community_id: str) -> dict[str, Any]:
        """List all provisions for a community (async).

        Args:
            community_id: The community to list provisions for.

        Returns:
            Dict with ``provisions`` list and ``count``.
        """
        resp = await self._async_rest_http.get(
            f"/api/v3/provision/{community_id}",
            params={"community_id": community_id},
        )
        self._check_rest_response(resp)
        return resp.json()
