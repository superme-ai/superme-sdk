"""Tests for partner SSE streaming (ask_stream, ask_my_agent_stream) and the
resource-backed conversation reads + user_details_read. Unit (mocked) only."""

from __future__ import annotations

import json

import httpx
import pytest
import respx

from superme_sdk.client import AsyncSuperMeClient, SuperMeClient

MCP_BASE = "https://mcp.superme.ai"
PARTNER_BASE = "https://api.superme.ai"

# Fake JWT with user_id "uid_123"
FAKE_JWT = "eyJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoidWlkXzEyMyJ9.sig"


def _sse(*events: dict) -> bytes:
    return "".join(
        f"event: {e['type']}\ndata: {json.dumps(e)}\n\n" for e in events
    ).encode()


def _rpc_ok(payload) -> httpx.Response:
    """JSON-RPC envelope for a tools/call result (content[].text = JSON)."""
    return httpx.Response(
        200,
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "result": {"content": [{"type": "text", "text": json.dumps(payload)}]},
        },
    )


def _rpc_resource(payload) -> httpx.Response:
    """JSON-RPC envelope for a resources/read result (contents[].text = JSON)."""
    return httpx.Response(
        200,
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "contents": [
                    {
                        "uri": "superme://x",
                        "mimeType": "application/json",
                        "text": json.dumps(payload),
                    }
                ]
            },
        },
    )


# ---------------------------------------------------------------------------
# Contract — methods exist
# ---------------------------------------------------------------------------


def test_streaming_methods_exist():
    for name in ("ask_stream", "ask_my_agent_stream"):
        assert callable(getattr(SuperMeClient, name))
        assert callable(getattr(AsyncSuperMeClient, name))


def test_get_user_details_exists():
    assert callable(getattr(SuperMeClient, "get_user_details"))


# ---------------------------------------------------------------------------
# ask_stream → /partner/ask
# ---------------------------------------------------------------------------


class TestAskStream:
    @respx.mock
    def test_posts_to_partner_ask_and_yields_chunks(self):
        route = respx.post(f"{PARTNER_BASE}/partner/ask").mock(
            return_value=httpx.Response(
                200,
                content=_sse(
                    {"type": "content", "text": "Grow"},
                    {"type": "content", "text": "th"},
                    {"type": "done", "conversation_id": "conv_9"},
                ),
                headers={"content-type": "text/event-stream"},
            )
        )
        with SuperMeClient(api_key=FAKE_JWT) as client:
            chunks = list(client.ask_stream("What is PMF?", username="ludo"))

        body = json.loads(route.calls[0].request.content)
        assert body["identifier"] == "ludo"
        assert body["question"] == "What is PMF?"
        assert body["stream"] is True
        assert [c["type"] for c in chunks] == ["content", "content", "done"]
        assert chunks[-1]["conversation_id"] == "conv_9"

    @respx.mock
    def test_stops_after_error(self):
        respx.post(f"{PARTNER_BASE}/partner/ask").mock(
            return_value=httpx.Response(
                200,
                content=_sse(
                    {"type": "error", "message": "boom"},
                    {"type": "content", "text": "should not be seen"},
                ),
                headers={"content-type": "text/event-stream"},
            )
        )
        with SuperMeClient(api_key=FAKE_JWT) as client:
            chunks = list(client.ask_stream("hi", username="ludo"))
        assert len(chunks) == 1
        assert chunks[0]["type"] == "error"

    @respx.mock
    def test_forwards_conversation_id(self):
        route = respx.post(f"{PARTNER_BASE}/partner/ask").mock(
            return_value=httpx.Response(
                200,
                content=_sse({"type": "done", "conversation_id": "c1"}),
                headers={"content-type": "text/event-stream"},
            )
        )
        with SuperMeClient(api_key=FAKE_JWT) as client:
            list(client.ask_stream("hi", username="ludo", conversation_id="c1"))
        body = json.loads(route.calls[0].request.content)
        assert body["conversation_id"] == "c1"


# ---------------------------------------------------------------------------
# ask_my_agent_stream → /partner/agent
# ---------------------------------------------------------------------------


class TestAskMyAgentStream:
    @respx.mock
    def test_posts_to_partner_agent_and_yields_turn_events(self):
        route = respx.post(f"{PARTNER_BASE}/partner/agent").mock(
            return_value=httpx.Response(
                200,
                content=_sse(
                    {"type": "turn_started", "conversation_id": "c1", "turn_id": "t1"},
                    {"type": "content", "conversation_id": "c1", "content": "hi"},
                    {
                        "type": "turn_completed",
                        "conversation_id": "c1",
                        "turn_id": "t1",
                    },
                ),
                headers={"content-type": "text/event-stream"},
            )
        )
        with SuperMeClient(api_key=FAKE_JWT) as client:
            events = list(client.ask_my_agent_stream("summarise"))

        body = json.loads(route.calls[0].request.content)
        assert body["question"] == "summarise"
        assert body["stream"] is True
        assert [e["type"] for e in events][-1] == "turn_completed"

    @respx.mock
    def test_stops_after_turn_failed(self):
        respx.post(f"{PARTNER_BASE}/partner/agent").mock(
            return_value=httpx.Response(
                200,
                content=_sse(
                    {"type": "turn_failed", "conversation_id": "c1", "error": "x"},
                    {"type": "content", "conversation_id": "c1", "content": "nope"},
                ),
                headers={"content-type": "text/event-stream"},
            )
        )
        with SuperMeClient(api_key=FAKE_JWT) as client:
            events = list(client.ask_my_agent_stream("hi"))
        assert len(events) == 1
        assert events[0]["type"] == "turn_failed"


# ---------------------------------------------------------------------------
# async streaming
# ---------------------------------------------------------------------------


class TestAsyncStreaming:
    @pytest.mark.asyncio
    @respx.mock
    async def test_async_ask_stream(self):
        respx.post(f"{PARTNER_BASE}/partner/ask").mock(
            return_value=httpx.Response(
                200,
                content=_sse(
                    {"type": "content", "text": "hello"},
                    {"type": "done", "conversation_id": "c1"},
                ),
                headers={"content-type": "text/event-stream"},
            )
        )
        async with AsyncSuperMeClient(api_key=FAKE_JWT) as client:
            chunks = [c async for c in client.ask_stream("hi", username="ludo")]
        assert [c["type"] for c in chunks] == ["content", "done"]

    @pytest.mark.asyncio
    @respx.mock
    async def test_async_agent_stream_stops_at_terminal(self):
        respx.post(f"{PARTNER_BASE}/partner/agent").mock(
            return_value=httpx.Response(
                200,
                content=_sse(
                    {"type": "content", "conversation_id": "c1", "content": "x"},
                    {"type": "turn_completed", "conversation_id": "c1"},
                    {"type": "content", "conversation_id": "c1", "content": "after"},
                ),
                headers={"content-type": "text/event-stream"},
            )
        )
        async with AsyncSuperMeClient(api_key=FAKE_JWT) as client:
            events = [e async for e in client.ask_my_agent_stream("hi")]
        assert [e["type"] for e in events] == ["content", "turn_completed"]


# ---------------------------------------------------------------------------
# get_user_details → user_details_read tool
# ---------------------------------------------------------------------------


class TestGetUserDetails:
    @respx.mock
    def test_calls_user_details_read(self):
        details = {
            "user_id": "u1",
            "name": "Elena",
            "summary": "deep bio",
            "work_experience": [],
            "education": [],
            "skills": ["growth"],
        }
        route = respx.post(f"{MCP_BASE}/mcp/").mock(return_value=_rpc_ok(details))
        with SuperMeClient(api_key=FAKE_JWT) as client:
            result = client.get_user_details("elena-verna")
        body = json.loads(route.calls[0].request.content)
        assert body["params"]["name"] == "user_details_read"
        assert body["params"]["arguments"]["identifier"] == "elena-verna"
        assert result["summary"] == "deep bio"


# ---------------------------------------------------------------------------
# resource-backed reads (fixes broken conversation_list/conversation_read)
# ---------------------------------------------------------------------------


class TestResourceBackedReads:
    @respx.mock
    def test_list_conversations_reads_resource(self):
        convs = [{"conversation_id": "c1"}, {"conversation_id": "c2"}]
        route = respx.post(f"{MCP_BASE}/mcp/").mock(return_value=_rpc_resource(convs))
        with SuperMeClient(api_key=FAKE_JWT) as client:
            result = client.list_conversations(limit=5)
        body = json.loads(route.calls[0].request.content)
        assert body["method"] == "resources/read"
        assert body["params"]["uri"] == "superme://me/conversations"
        assert result == convs

    @respx.mock
    def test_list_conversations_respects_limit(self):
        convs = [{"conversation_id": f"c{i}"} for i in range(10)]
        respx.post(f"{MCP_BASE}/mcp/").mock(return_value=_rpc_resource(convs))
        with SuperMeClient(api_key=FAKE_JWT) as client:
            result = client.list_conversations(limit=3)
        assert len(result) == 3

    @respx.mock
    def test_get_conversation_reads_resource(self):
        conv = {"conversation_id": "c1", "messages": [{"role": "user"}]}
        route = respx.post(f"{MCP_BASE}/mcp/").mock(return_value=_rpc_resource(conv))
        with SuperMeClient(api_key=FAKE_JWT) as client:
            result = client.get_conversation("c1")
        body = json.loads(route.calls[0].request.content)
        assert body["method"] == "resources/read"
        assert body["params"]["uri"] == "superme://conversation/c1"
        assert result == conv

    @respx.mock
    def test_get_profile_own_reads_resource(self):
        me = {"name": "Me", "title": "Founder"}
        route = respx.post(f"{MCP_BASE}/mcp/").mock(return_value=_rpc_resource(me))
        with SuperMeClient(api_key=FAKE_JWT) as client:
            result = client.get_profile()
        body = json.loads(route.calls[0].request.content)
        assert body["method"] == "resources/read"
        assert body["params"]["uri"] == "superme://me/profile"
        assert result == me
