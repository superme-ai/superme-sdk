"""Tests for AgenticResumeMixin — agentic resume REST methods."""

from __future__ import annotations

import httpx
import pytest
import respx

from superme_sdk.client import SuperMeClient

REST_BASE = "https://www.superme.ai"

_FAKE_JWT = (
    "eyJhbGciOiAiSFMyNTYiLCAidHlwIjogIkpXVCJ9"
    ".eyJ1c2VyX2lkIjogInVpZF90ZXN0MTIzIn0"
    ".fakesig"
)


@pytest.fixture
def client():
    c = SuperMeClient(api_key=_FAKE_JWT)
    yield c
    c.close()


# ---------------------------------------------------------------------------
# generate_resume_token
# ---------------------------------------------------------------------------


@respx.mock
def test_generate_resume_token_posts_correct_route(client):
    route = respx.post(f"{REST_BASE}/api/v3/agentic-resume/token").mock(
        return_value=httpx.Response(200, json={"token": "tok_abc", "instructions_url": "/api/v3/agentic-resume/instructions/tok_abc"})
    )
    result = client.generate_resume_token()
    assert route.called
    assert result["token"] == "tok_abc"


@respx.mock
def test_generate_resume_token_sends_auth_header(client):
    route = respx.post(f"{REST_BASE}/api/v3/agentic-resume/token").mock(
        return_value=httpx.Response(200, json={"token": "tok_abc"})
    )
    client.generate_resume_token()
    assert route.calls[0].request.headers["authorization"] == f"Bearer {_FAKE_JWT}"


# ---------------------------------------------------------------------------
# get_resume_instructions
# ---------------------------------------------------------------------------


@respx.mock
def test_get_resume_instructions_gets_correct_route(client):
    route = respx.get(f"{REST_BASE}/api/v3/agentic-resume/instructions/tok_abc").mock(
        return_value=httpx.Response(200, text="# Build resume like this...")
    )
    result = client.get_resume_instructions("tok_abc")
    assert route.called
    assert "Build resume" in result


@respx.mock
def test_get_resume_instructions_returns_string(client):
    respx.get(f"{REST_BASE}/api/v3/agentic-resume/instructions/tok_abc").mock(
        return_value=httpx.Response(200, text="instructions markdown")
    )
    result = client.get_resume_instructions("tok_abc")
    assert isinstance(result, str)


# ---------------------------------------------------------------------------
# upload_resume
# ---------------------------------------------------------------------------


@respx.mock
def test_upload_resume_posts_correct_route(client):
    route = respx.post(f"{REST_BASE}/api/v3/agentic-resume/upload/tok_abc").mock(
        return_value=httpx.Response(200, json={"status": "accepted"})
    )
    result = client.upload_resume("tok_abc", "# John Doe\n\nExperience: ...")
    assert route.called
    assert result["status"] == "accepted"


@respx.mock
def test_upload_resume_sends_markdown_as_bytes(client):
    route = respx.post(f"{REST_BASE}/api/v3/agentic-resume/upload/tok_abc").mock(
        return_value=httpx.Response(200, json={"status": "accepted"})
    )
    markdown = "# My Resume"
    client.upload_resume("tok_abc", markdown)
    assert route.calls[0].request.content == markdown.encode()


@respx.mock
def test_upload_resume_http_error_raises(client):
    respx.post(f"{REST_BASE}/api/v3/agentic-resume/upload/tok_abc").mock(
        return_value=httpx.Response(413, json={"error": "too large"})
    )
    with pytest.raises(Exception):
        client.upload_resume("tok_abc", "x" * 100)


# ---------------------------------------------------------------------------
# get_resume
# ---------------------------------------------------------------------------


@respx.mock
def test_get_resume_gets_correct_route(client):
    route = respx.get(f"{REST_BASE}/api/v3/agentic-resume/").mock(
        return_value=httpx.Response(200, json={"structured_data": {"name": "Alice"}, "html": "<p>Alice</p>"})
    )
    result = client.get_resume()
    assert route.called
    assert result["structured_data"]["name"] == "Alice"


@respx.mock
def test_get_resume_404_raises(client):
    respx.get(f"{REST_BASE}/api/v3/agentic-resume/").mock(
        return_value=httpx.Response(404, json={"error": "not found"})
    )
    with pytest.raises(Exception):
        client.get_resume()


# ---------------------------------------------------------------------------
# regenerate_resume
# ---------------------------------------------------------------------------


@respx.mock
def test_regenerate_resume_posts_correct_route(client):
    route = respx.post(f"{REST_BASE}/api/v3/agentic-resume/regenerate").mock(
        return_value=httpx.Response(200, json={"structured_data": {"name": "Bob"}, "html": "<p>Bob</p>"})
    )
    result = client.regenerate_resume()
    assert route.called
    assert result["structured_data"]["name"] == "Bob"


@respx.mock
def test_regenerate_resume_sends_auth_header(client):
    route = respx.post(f"{REST_BASE}/api/v3/agentic-resume/regenerate").mock(
        return_value=httpx.Response(200, json={"structured_data": {}})
    )
    client.regenerate_resume()
    assert route.calls[0].request.headers["authorization"] == f"Bearer {_FAKE_JWT}"


# ---------------------------------------------------------------------------
# Live integration tests (skipped unless SUPERME_API_KEY is set)
# ---------------------------------------------------------------------------


@pytest.mark.live
def test_live_generate_resume_token(live_client):
    """generate_resume_token returns a usable token."""
    result = live_client.generate_resume_token()
    assert isinstance(result, dict)
    assert "token" in result
    assert result["token"]


@pytest.mark.live
def test_live_get_resume_instructions(live_client):
    """get_resume_instructions returns non-empty markdown string."""
    token_data = live_client.generate_resume_token()
    token = token_data["token"]
    instructions = live_client.get_resume_instructions(token)
    assert isinstance(instructions, str)
    assert len(instructions) > 0


@pytest.mark.live
def test_live_get_resume(live_client):
    """get_resume returns a dict, or skips if no resume has been uploaded yet."""
    try:
        result = live_client.get_resume()
        assert isinstance(result, dict)
    except RuntimeError:
        # _check_rest_response raises RuntimeError on non-2xx (e.g. 404 when
        # no resume exists yet). Treat as expected — skip rather than fail.
        pytest.skip("No resume uploaded for this account yet (got non-2xx)")
