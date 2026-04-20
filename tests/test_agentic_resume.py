"""Tests for AgenticResumeMixin — unit (mocked) + live e2e.

Unit tests run on every commit with no external dependencies.
Live tests require SUPERME_API_KEY and run with ``pytest -m live``.
"""

from __future__ import annotations

import os

import httpx
import pytest
import respx

from superme_sdk.client import SuperMeClient

REST_BASE = "https://www.superme.ai"
FAKE_JWT = "eyJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoidWlkXzEyMyJ9.sig"

_FAKE_RESUME = {
    "structured_data": {
        "prompt_stats": {
            "metrics": {
                "total_prompts": 1234,
                "active_days": 90,
                "usage_rate": "78%",
                "sessions": 42,
                "longest_streak": 14,
            },
        },
        "shipped": {
            "product_context": "Built core platform",
            "domains": [{"name": "API", "prose": "REST API layer"}],
            "tech_stack": [{"layer": "backend", "tech": "Python"}],
        },
        "notable_sessions": [
            {"name": "Big refactor", "date": "2025-04-01", "messages": 50, "hours": 3.0, "what_happened": "Rewrote auth"}
        ],
        "prompt_style": {
            "traits": [{"label": "Direct", "evidence": "Often skips pleasantries"}],
            "overall": "Concise and task-oriented",
        },
    },
    "raw_markdown": "# Raw data\nSome content",
    "html": "<html>...</html>",
    "created_at": "2025-04-01T10:00:00Z",
    "updated_at": "2025-04-18T10:00:00Z",
}


# ---------------------------------------------------------------------------
# Contract tests
# ---------------------------------------------------------------------------


class TestContractAllMethodsExist:
    def test_all_methods_present(self):
        expected = [
            "get_agentic_resume",
            "regenerate_agentic_resume",
            "create_agentic_resume_token",
        ]
        for name in expected:
            assert hasattr(SuperMeClient, name), f"SuperMeClient missing method: {name}"
            assert callable(getattr(SuperMeClient, name))


# ---------------------------------------------------------------------------
# get_agentic_resume
# ---------------------------------------------------------------------------


class TestGetAgenticResume:
    @respx.mock
    def test_get_resume_returns_data(self):
        respx.get(f"{REST_BASE}/api/v3/agentic-resume").mock(
            return_value=httpx.Response(200, json=_FAKE_RESUME)
        )
        client = SuperMeClient(api_key=FAKE_JWT)
        result = client.get_agentic_resume()
        assert result["structured_data"] is not None
        assert result["raw_markdown"] == "# Raw data\nSome content"
        client.close()

    @respx.mock
    def test_get_resume_404_returns_empty(self):
        """404 means no resume exists yet — should return a full sentinel dict."""
        respx.get(f"{REST_BASE}/api/v3/agentic-resume").mock(
            return_value=httpx.Response(404, json={"detail": "not found"})
        )
        client = SuperMeClient(api_key=FAKE_JWT)
        result = client.get_agentic_resume()
        assert result["structured_data"] is None
        assert result["raw_markdown"] is None
        assert result["html"] is None
        assert result["created_at"] is None
        assert result["updated_at"] is None
        client.close()

    @respx.mock
    def test_get_resume_5xx_raises(self):
        respx.get(f"{REST_BASE}/api/v3/agentic-resume").mock(
            return_value=httpx.Response(500, json={"error": "server error"})
        )
        client = SuperMeClient(api_key=FAKE_JWT)
        with pytest.raises(RuntimeError):
            client.get_agentic_resume()
        client.close()

    @respx.mock
    def test_get_resume_calls_correct_url(self):
        route = respx.get(f"{REST_BASE}/api/v3/agentic-resume").mock(
            return_value=httpx.Response(200, json=_FAKE_RESUME)
        )
        client = SuperMeClient(api_key=FAKE_JWT)
        client.get_agentic_resume()
        assert route.called
        client.close()


# ---------------------------------------------------------------------------
# regenerate_agentic_resume
# ---------------------------------------------------------------------------


class TestRegenerateAgenticResume:
    @respx.mock
    def test_regenerate_returns_structured_data(self):
        payload = {"structured_data": _FAKE_RESUME["structured_data"], "html": "<html/>"}
        respx.post(f"{REST_BASE}/api/v3/agentic-resume/regenerate").mock(
            return_value=httpx.Response(200, json=payload)
        )
        client = SuperMeClient(api_key=FAKE_JWT)
        result = client.regenerate_agentic_resume()
        assert result["structured_data"] is not None
        assert result["html"] == "<html/>"
        client.close()

    @respx.mock
    def test_regenerate_404_raises(self):
        """404 from regenerate means no raw markdown stored — should raise."""
        respx.post(f"{REST_BASE}/api/v3/agentic-resume/regenerate").mock(
            return_value=httpx.Response(404, json={"detail": "not found"})
        )
        client = SuperMeClient(api_key=FAKE_JWT)
        with pytest.raises(RuntimeError):
            client.regenerate_agentic_resume()
        client.close()

    @respx.mock
    def test_regenerate_5xx_raises(self):
        respx.post(f"{REST_BASE}/api/v3/agentic-resume/regenerate").mock(
            return_value=httpx.Response(500, json={"error": "synthesis failed"})
        )
        client = SuperMeClient(api_key=FAKE_JWT)
        with pytest.raises(RuntimeError):
            client.regenerate_agentic_resume()
        client.close()

    @respx.mock
    def test_regenerate_calls_correct_url(self):
        route = respx.post(f"{REST_BASE}/api/v3/agentic-resume/regenerate").mock(
            return_value=httpx.Response(200, json={"structured_data": {}, "html": ""})
        )
        client = SuperMeClient(api_key=FAKE_JWT)
        client.regenerate_agentic_resume()
        assert route.called
        client.close()


# ---------------------------------------------------------------------------
# create_agentic_resume_token
# ---------------------------------------------------------------------------


class TestCreateAgenticResumeToken:
    @respx.mock
    def test_create_token_returns_urls(self):
        payload = {
            "token": "tok_abc123",
            "upload_url": "https://www.superme.ai/api/v3/agentic-resume/upload/tok_abc123",
            "instructions_url": "https://www.superme.ai/api/v3/agentic-resume/instructions/tok_abc123",
            "expires_at": "2025-04-18T11:00:00Z",
        }
        respx.post(f"{REST_BASE}/api/v3/agentic-resume/token").mock(
            return_value=httpx.Response(200, json=payload)
        )
        client = SuperMeClient(api_key=FAKE_JWT)
        result = client.create_agentic_resume_token()
        assert result["token"] == "tok_abc123"
        assert "upload_url" in result
        assert "instructions_url" in result
        assert "expires_at" in result
        client.close()

    @respx.mock
    def test_create_token_calls_correct_url(self):
        route = respx.post(f"{REST_BASE}/api/v3/agentic-resume/token").mock(
            return_value=httpx.Response(200, json={"token": "t", "upload_url": "u", "instructions_url": "i", "expires_at": "e"})
        )
        client = SuperMeClient(api_key=FAKE_JWT)
        client.create_agentic_resume_token()
        assert route.called
        client.close()

    @respx.mock
    def test_create_token_401_raises(self):
        respx.post(f"{REST_BASE}/api/v3/agentic-resume/token").mock(
            return_value=httpx.Response(401, json={"error": "unauthorized"})
        )
        client = SuperMeClient(api_key=FAKE_JWT)
        with pytest.raises(RuntimeError):
            client.create_agentic_resume_token()
        client.close()


# ---------------------------------------------------------------------------
# Live e2e tests
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def live_client():
    key = os.getenv("SUPERME_API_KEY", "")
    if not key:
        pytest.skip("SUPERME_API_KEY not set")
    client = SuperMeClient(api_key=key)
    yield client
    client.close()


@pytest.mark.live
def test_live_get_agentic_resume(live_client):
    """get_agentic_resume returns a dict (may be empty if no resume exists)."""
    result = live_client.get_agentic_resume()
    assert isinstance(result, dict)
    assert "structured_data" in result


@pytest.mark.live
def test_live_create_agentic_resume_token(live_client):
    """create_agentic_resume_token returns token + URLs."""
    result = live_client.create_agentic_resume_token()
    assert "token" in result
    assert "upload_url" in result
    assert "instructions_url" in result
    assert "expires_at" in result


@pytest.mark.live
def test_live_regenerate_requires_existing_data(live_client):
    """regenerate raises if no resume exists, or returns structured_data if one does."""
    resume = live_client.get_agentic_resume()
    if not resume.get("structured_data"):
        with pytest.raises((RuntimeError, Exception)):
            live_client.regenerate_agentic_resume()
    else:
        result = live_client.regenerate_agentic_resume()
        assert isinstance(result, dict)
        assert "structured_data" in result
