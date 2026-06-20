"""Provisioning methods — create and invite community members."""

from __future__ import annotations

import concurrent.futures
from typing import Any, Optional

import httpx


_BATCH_CONCURRENCY = 10


def _provision_body(
    community_id: str,
    name: str,
    linkedin_url: str,
    contact_email: Optional[str] = None,
    notes: Optional[str] = None,
    socials: Optional[dict[str, str]] = None,
    external_urls: Optional[list[str]] = None,
) -> dict[str, Any]:
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
    return body


class ProvisionMixin:
    def provision_create(
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
        """Provision a single community member.

        Example:
            ```python
            result = client.provision_create(
                "community_abc",
                name="Jane Smith",
                linkedin_url="https://linkedin.com/in/janesmith",
                contact_email="jane@example.com",
                notes="Met at Dubai summit",
            )
            print(result["provision"]["user_id"])
            ```

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
        body = _provision_body(
            community_id,
            name,
            linkedin_url,
            contact_email,
            notes,
            socials,
            external_urls,
        )
        resp = self._rest_http.post(f"/api/v3/provision/{community_id}", json=body)
        self._check_rest_response(resp)
        return resp.json()

    def provision_create_batch(
        self,
        community_id: str,
        profiles: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Provision multiple community members concurrently.

        Fans out up to 10 concurrent requests using a dedicated batch-scoped
        HTTP client (avoids sharing the main client across threads). Results
        are returned in the same order as ``profiles``. Failed items have an
        ``"error"`` key instead of ``"provision"``.

        Example:
            ```python
            results = client.provision_create_batch(
                "community_abc",
                profiles=[
                    {
                        "name": "Jane Smith",
                        "linkedin_url": "https://linkedin.com/in/janesmith",
                        "notes": "WhatsApp intro: loves B2B SaaS",
                    },
                    {
                        "name": "John Doe",
                        "linkedin_url": "https://linkedin.com/in/johndoe",
                        "contact_email": "john@example.com",
                    },
                ],
            )
            for r in results:
                if "error" in r:
                    print("failed:", r["error"])
                else:
                    print("provisioned:", r["provision"]["user_id"])
            ```

        Args:
            community_id: The community to provision into.
            profiles: List of profile dicts. Each supports the same keys as
                :meth:`provision_create` (``name``, ``linkedin_url``,
                ``contact_email``, ``notes``, ``socials``, ``external_urls``).

        Returns:
            List of result dicts in the same order as ``profiles``.
        """
        results: list[dict[str, Any]] = [{}] * len(profiles)

        # Fresh client scoped to this batch — avoids sharing self._rest_http across threads.
        batch_client = httpx.Client(
            base_url=self.rest_base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
            },
            timeout=self._rest_http.timeout,
        )

        def _one(index: int, profile: dict[str, Any]) -> None:
            try:
                body = _provision_body(community_id, **profile)
                resp = batch_client.post(f"/api/v3/provision/{community_id}", json=body)
                self._check_rest_response(resp)
                results[index] = resp.json()
            except Exception as exc:  # noqa: BLE001
                results[index] = {"error": str(exc)}

        try:
            with concurrent.futures.ThreadPoolExecutor(
                max_workers=_BATCH_CONCURRENCY
            ) as pool:
                futs = [pool.submit(_one, i, p) for i, p in enumerate(profiles)]
                concurrent.futures.wait(futs)
        finally:
            batch_client.close()

        return results

    def provision_send_invites(
        self,
        community_id: str,
        user_ids: list[str],
    ) -> dict[str, Any]:
        """Send invite emails to provisioned members.

        Example:
            ```python
            result = client.provision_send_invites(
                "community_abc",
                user_ids=["user_123", "user_456"],
            )
            print(result["sent"], result["skipped"], result["failed"])
            ```

        Args:
            community_id: The community whose provisions to invite.
            user_ids: List of provisioned user IDs to send invites to.

        Returns:
            Dict with ``sent``, ``skipped``, and ``failed`` lists.
        """
        resp = self._rest_http.post(
            f"/api/v3/provision/{community_id}/invite",
            json={"community_id": community_id, "user_ids": user_ids},
        )
        self._check_rest_response(resp)
        return resp.json()

    def provision_list(self, community_id: str) -> dict[str, Any]:
        """List all provisions for a community.

        Example:
            ```python
            result = client.provision_list("community_abc")
            for p in result["provisions"]:
                print(p["user_id"], p["status"])
            ```

        Args:
            community_id: The community to list provisions for.

        Returns:
            Dict with ``provisions`` list and ``count``.
        """
        resp = self._rest_http.get(
            f"/api/v3/provision/{community_id}",
            params={"community_id": community_id},
        )
        self._check_rest_response(resp)
        return resp.json()
