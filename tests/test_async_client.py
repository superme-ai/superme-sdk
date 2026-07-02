"""Tests for AsyncSuperMeClient — async streaming and request methods."""

from __future__ import annotations

import json

import httpx
import pytest
import respx

from superme_sdk.client import AsyncSuperMeClient
from superme_sdk.exceptions import AuthError, MCPError

MCP_BASE = "https://mcp.superme.ai"
REST_BASE = "https://www.superme.ai"

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _sse(*objs) -> bytes:
    """Encode dicts as ``data: <json>\\n\\n`` SSE lines."""
    return "".join(f"data: {json.dumps(o)}\n\n" for o in objs).encode()


# ---------------------------------------------------------------------------
# construction
# ---------------------------------------------------------------------------


async def test_async_client_raises_on_empty_key():
    with pytest.raises(ValueError, match="api_key is required"):
        AsyncSuperMeClient(api_key="")


async def test_async_client_stores_token():
    async with AsyncSuperMeClient(api_key="test-key") as client:
        assert client.token == "test-key"


async def test_async_client_context_manager():
    async with AsyncSuperMeClient(api_key="tok") as client:
        assert client.token == "tok"


# ---------------------------------------------------------------------------
# stream_interview
# ---------------------------------------------------------------------------


@respx.mock
async def test_stream_interview_yields_events():
    sse = _sse(
        {"event": "stage_change", "stage_number": 1, "stage_name": "Intro"},
        {"event": "token", "role": "company", "token": "Hello", "stage_number": 1},
        {"event": "status", "status": "awaiting_input"},
    )
    respx.get(f"{REST_BASE}/api/v3/agent/interview/iv_123/stream").mock(
        return_value=httpx.Response(200, content=sse)
    )
    async with AsyncSuperMeClient(api_key="tok") as client:
        events = [ev async for ev in client.stream_interview("iv_123")]

    assert len(events) == 3
    assert events[0]["event"] == "stage_change"
    assert events[1]["token"] == "Hello"


@respx.mock
async def test_stream_interview_stops_on_terminal_status():
    sse = _sse(
        {"event": "token", "role": "company", "token": "Hi"},
        {"event": "status", "status": "completed"},
        # This event should NOT be yielded — we stop after terminal status
        {"event": "token", "role": "company", "token": "Should not appear"},
    )
    respx.get(f"{REST_BASE}/api/v3/agent/interview/iv_term/stream").mock(
        return_value=httpx.Response(200, content=sse)
    )
    async with AsyncSuperMeClient(api_key="tok") as client:
        events = [ev async for ev in client.stream_interview("iv_term")]

    assert len(events) == 2
    assert events[-1]["status"] == "completed"


# ---------------------------------------------------------------------------
# get_interview_transcript
# ---------------------------------------------------------------------------


@respx.mock
async def test_get_interview_transcript_returns_dict():
    transcript_data = {"transcript": [{"stage_number": 1, "messages": []}]}
    respx.get(f"{REST_BASE}/api/v3/interview/iv_abc/transcript").mock(
        return_value=httpx.Response(200, json=transcript_data)
    )
    async with AsyncSuperMeClient(api_key="tok") as client:
        result = await client.get_interview_transcript("iv_abc")
    assert result["transcript"] == transcript_data["transcript"]


# ---------------------------------------------------------------------------
# get_agentic_resume
# ---------------------------------------------------------------------------


@respx.mock
async def test_get_agentic_resume_returns_dict():
    resume_data = {"structured_data": {"name": "Test"}, "raw_markdown": "# Test"}
    respx.get(f"{REST_BASE}/api/v3/agentic-resume").mock(
        return_value=httpx.Response(200, json=resume_data)
    )
    async with AsyncSuperMeClient(api_key="tok") as client:
        result = await client.get_agentic_resume()
    assert result["structured_data"] == {"name": "Test"}


@respx.mock
async def test_get_agentic_resume_404_returns_null_structured_data():
    respx.get(f"{REST_BASE}/api/v3/agentic-resume").mock(
        return_value=httpx.Response(404, json={"error": "not found"})
    )
    async with AsyncSuperMeClient(api_key="tok") as client:
        result = await client.get_agentic_resume()
    assert result["structured_data"] is None


# ---------------------------------------------------------------------------
# error handling
# ---------------------------------------------------------------------------


@respx.mock
async def test_async_client_401_raises_auth_error():
    respx.get(f"{REST_BASE}/api/v3/agentic-resume").mock(
        return_value=httpx.Response(401, json={"error": "unauthorized"})
    )
    async with AsyncSuperMeClient(api_key="bad-key") as client:
        with pytest.raises(AuthError):
            await client.get_agentic_resume()


@respx.mock
async def test_async_client_mcp_error_raises():
    respx.post(f"{MCP_BASE}/mcp/").mock(
        return_value=httpx.Response(
            200,
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "error": {"code": -32600, "message": "Bad request"},
            },
        )
    )
    async with AsyncSuperMeClient(api_key="tok") as client:
        with pytest.raises(MCPError, match="MCP error -32600"):
            await client.get_user_details("someone")


# ---------------------------------------------------------------------------
# live tests
# ---------------------------------------------------------------------------


@pytest.mark.live
async def test_live_get_agentic_resume(async_live_client):
    result = await async_live_client.get_agentic_resume()
    # May or may not have a resume — just check the shape
    assert "structured_data" in result


@pytest.mark.live
async def test_live_stream_interview_list(async_live_client):
    interviews = await async_live_client.list_my_interviews()
    assert isinstance(interviews, list)
