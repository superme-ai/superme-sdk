"""Tests for LibraryMixin — unit (mocked) + live e2e.

Unit tests run on every commit with no external dependencies.
Live tests require SUPERME_API_KEY and run with ``pytest -m live``.
"""

from __future__ import annotations

import os

import httpx
import pytest
import respx

from superme_sdk.client import SuperMeClient
from superme_sdk.exceptions import SuperMeError

REST_BASE = "https://www.superme.ai"

# Fake JWT with user_id "uid_123"
FAKE_JWT = "eyJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoidWlkXzEyMyJ9.sig"


# ---------------------------------------------------------------------------
# Part A — Unit tests (mocked, always run)
# ---------------------------------------------------------------------------


class TestContractLibraryMethodsExist:
    def test_all_methods_present(self):
        expected = ["get_learnings", "get_learning", "get_ingestion_status"]
        for name in expected:
            assert hasattr(SuperMeClient, name), f"SuperMeClient missing method: {name}"
            assert callable(getattr(SuperMeClient, name))


class TestGetLearnings:
    @respx.mock
    def test_calls_correct_url_with_user_id(self):
        route = respx.get(f"{REST_BASE}/api/v3/library").mock(
            return_value=httpx.Response(200, json={"success": True, "items": []})
        )
        client = SuperMeClient(api_key=FAKE_JWT)
        client.get_learnings()
        assert route.called
        request_url = str(route.calls[0].request.url)
        assert "user_id=uid_123" in request_url
        client.close()

    @respx.mock
    def test_default_offset_sent(self):
        route = respx.get(f"{REST_BASE}/api/v3/library").mock(
            return_value=httpx.Response(200, json={"success": True, "items": []})
        )
        client = SuperMeClient(api_key=FAKE_JWT)
        client.get_learnings()
        request_url = str(route.calls[0].request.url)
        assert "offset=0" in request_url
        client.close()

    @respx.mock
    def test_optional_params_forwarded(self):
        route = respx.get(f"{REST_BASE}/api/v3/library").mock(
            return_value=httpx.Response(200, json={"success": True, "items": []})
        )
        client = SuperMeClient(api_key=FAKE_JWT)
        client.get_learnings(
            limit=5,
            collection="external",
            platform="medium",
            title_keyword="growth",
        )
        request_url = str(route.calls[0].request.url)
        assert "limit=5" in request_url
        assert "collection=external" in request_url
        assert "platform=medium" in request_url
        assert "title_keyword=growth" in request_url
        client.close()

    @respx.mock
    def test_returns_response(self):
        payload = {"success": True, "items": [{"learning_id": "l1", "title": "Test"}]}
        respx.get(f"{REST_BASE}/api/v3/library").mock(
            return_value=httpx.Response(200, json=payload)
        )
        client = SuperMeClient(api_key=FAKE_JWT)
        result = client.get_learnings()
        assert result == payload
        client.close()

    @respx.mock
    def test_4xx_raises(self):
        respx.get(f"{REST_BASE}/api/v3/library").mock(
            return_value=httpx.Response(403, json={"error": "forbidden"})
        )
        client = SuperMeClient(api_key=FAKE_JWT)
        with pytest.raises(SuperMeError):
            client.get_learnings()
        client.close()

    def test_raises_if_no_user_id(self):
        import base64, json as _json

        empty_payload = (
            base64.urlsafe_b64encode(_json.dumps({}).encode()).rstrip(b"=").decode()
        )
        no_uid_jwt = f"eyJhbGciOiJIUzI1NiJ9.{empty_payload}.sig"
        client = SuperMeClient(api_key=no_uid_jwt)
        with pytest.raises(ValueError, match="user_id"):
            client.get_learnings()
        client.close()


class TestGetLearning:
    @respx.mock
    def test_calls_getlearning_with_learning_id(self):
        route = respx.get(f"{REST_BASE}/api/v3/library/getlearning").mock(
            return_value=httpx.Response(
                200, json={"learning_id": "l1", "title": "My Post"}
            )
        )
        client = SuperMeClient(api_key=FAKE_JWT)
        client.get_learning("l1")
        assert route.called
        request_url = str(route.calls[0].request.url)
        assert "learning_id=l1" in request_url
        client.close()

    @respx.mock
    def test_returns_learning_dict(self):
        payload = {"learning_id": "l1", "title": "My Post", "summary": "A summary"}
        respx.get(f"{REST_BASE}/api/v3/library/getlearning").mock(
            return_value=httpx.Response(200, json=payload)
        )
        client = SuperMeClient(api_key=FAKE_JWT)
        result = client.get_learning("l1")
        assert result == payload
        client.close()

    @respx.mock
    def test_404_raises(self):
        respx.get(f"{REST_BASE}/api/v3/library/getlearning").mock(
            return_value=httpx.Response(404, json={"error": "Learning not found"})
        )
        client = SuperMeClient(api_key=FAKE_JWT)
        with pytest.raises(SuperMeError):
            client.get_learning("bad_id")
        client.close()


class TestGetIngestionStatus:
    @respx.mock
    def test_calls_ingestion_with_user_id(self):
        route = respx.get(f"{REST_BASE}/api/v3/library/ingestion").mock(
            return_value=httpx.Response(200, json={"success": True, "pending": 2})
        )
        client = SuperMeClient(api_key=FAKE_JWT)
        client.get_ingestion_status()
        assert route.called
        request_url = str(route.calls[0].request.url)
        assert "user_id=uid_123" in request_url
        client.close()

    @respx.mock
    def test_returns_response(self):
        payload = {"success": True, "pending": 1, "done": 10, "failed": 0}
        respx.get(f"{REST_BASE}/api/v3/library/ingestion").mock(
            return_value=httpx.Response(200, json=payload)
        )
        client = SuperMeClient(api_key=FAKE_JWT)
        result = client.get_ingestion_status()
        assert result == payload
        client.close()

    @respx.mock
    def test_4xx_raises(self):
        respx.get(f"{REST_BASE}/api/v3/library/ingestion").mock(
            return_value=httpx.Response(403, json={"error": "forbidden"})
        )
        client = SuperMeClient(api_key=FAKE_JWT)
        with pytest.raises(SuperMeError):
            client.get_ingestion_status()
        client.close()

    def test_raises_if_no_user_id(self):
        import base64, json as _json

        empty_payload = (
            base64.urlsafe_b64encode(_json.dumps({}).encode()).rstrip(b"=").decode()
        )
        no_uid_jwt = f"eyJhbGciOiJIUzI1NiJ9.{empty_payload}.sig"
        client = SuperMeClient(api_key=no_uid_jwt)
        with pytest.raises(ValueError, match="user_id"):
            client.get_ingestion_status()
        client.close()


# ---------------------------------------------------------------------------
# Part B — Live e2e tests (require SUPERME_API_KEY, run with -m live)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def live_lib_client():
    key = os.getenv("SUPERME_API_KEY", "")
    if not key:
        pytest.skip("SUPERME_API_KEY not set")
    client = SuperMeClient(api_key=key)
    yield client
    client.close()


@pytest.mark.live
def test_live_get_learnings_returns_list(live_lib_client):
    result = live_lib_client.get_learnings(limit=5)
    assert isinstance(result, dict)
    assert "items" in result or "learnings" in result or "success" in result


@pytest.mark.live
def test_live_get_learnings_pagination(live_lib_client):
    """Second page with offset > 0 returns a dict (may be empty)."""
    result = live_lib_client.get_learnings(limit=3, offset=0)
    assert isinstance(result, dict)
    result2 = live_lib_client.get_learnings(limit=3, offset=3)
    assert isinstance(result2, dict)


@pytest.mark.live
def test_live_get_learning_roundtrip(live_lib_client):
    """Fetch first item from get_learnings and retrieve it individually."""
    page = live_lib_client.get_learnings(limit=1)
    items = page.get("items") or page.get("learnings") or []
    if not items:
        pytest.skip("No library items for this account")
    learning_id = items[0].get("learning_id") or items[0].get("id")
    assert learning_id, f"item missing id: {items[0]}"
    detail = live_lib_client.get_learning(learning_id)
    assert isinstance(detail, dict)


@pytest.mark.live
def test_live_get_ingestion_status(live_lib_client):
    result = live_lib_client.get_ingestion_status()
    assert isinstance(result, dict)
