"""Tests for superme_sdk.client — SuperMeClient (MCP JSON-RPC transport)."""

import json

import httpx
import pytest
import respx

from superme_sdk.client import SuperMeClient, ChatCompletion

MCP_BASE = "https://mcp.superme.ai"

# MCP ask tool response (what the backend returns inside JSON-RPC)
ASK_RESULT = {
    "conversation_id": "conv_123",
    "target_user": "ludo",
    "target_user_id": "uid_456",
    "question": "What is PMF?",
    "response": "Growth marketing is...",
    "status": "success",
}

# Full JSON-RPC 2.0 response wrapping the MCP tool call result
MCP_TOOL_RESPONSE = {
    "jsonrpc": "2.0",
    "id": 1,
    "result": {
        "content": [
            {"type": "text", "text": json.dumps(ASK_RESULT)},
        ],
    },
}


def _mock_mcp_ask():
    """Helper to mock a POST / that returns ASK_RESULT."""
    return respx.post(f"{MCP_BASE}/mcp/").mock(
        return_value=httpx.Response(200, json=MCP_TOOL_RESPONSE)
    )


# ---- construction ----


def test_client_raises_on_empty_key():
    with pytest.raises(ValueError, match="api_key is required"):
        SuperMeClient(api_key="")


def test_client_explicit_key():
    client = SuperMeClient(api_key="explicit")
    assert client.token == "explicit"
    client.close()


# ---- ask ----


@respx.mock
def test_ask_returns_text():
    _mock_mcp_ask()
    client = SuperMeClient(api_key="tok")
    result = client.ask("What is PMF?", username="ludo")
    assert result == "Growth marketing is..."
    client.close()


@respx.mock
def test_ask_sends_correct_jsonrpc_body():
    route = _mock_mcp_ask()
    client = SuperMeClient(api_key="tok")
    client.ask("question", username="alice", incognito=True)

    body = json.loads(route.calls[0].request.content)
    assert body["jsonrpc"] == "2.0"
    assert body["method"] == "tools/call"
    assert body["params"]["name"] == "ask"
    assert body["params"]["arguments"]["identifier"] == "alice"
    assert body["params"]["arguments"]["question"] == "question"
    assert body["params"]["arguments"]["incognito"] is True
    client.close()


@respx.mock
def test_ask_sends_auth_header():
    route = _mock_mcp_ask()
    client = SuperMeClient(api_key="my-jwt")
    client.ask("hi", username="ludo")

    auth = route.calls[0].request.headers["authorization"]
    assert auth == "Bearer my-jwt"
    client.close()


@respx.mock
def test_ask_sends_conversation_id():
    route = _mock_mcp_ask()
    client = SuperMeClient(api_key="tok")
    client.ask("hi", username="ludo", conversation_id="conv_abc")

    body = json.loads(route.calls[0].request.content)
    assert body["params"]["arguments"]["conversation_id"] == "conv_abc"
    client.close()


# ---- ask_with_history ----


@respx.mock
def test_ask_with_history_returns_tuple():
    _mock_mcp_ask()
    client = SuperMeClient(api_key="tok")
    text, conv_id = client.ask_with_history(
        [{"role": "user", "content": "Q1"}], username="ludo"
    )
    assert text == "Growth marketing is..."
    assert conv_id == "conv_123"
    client.close()


@respx.mock
def test_ask_with_history_extracts_last_user_message():
    route = _mock_mcp_ask()
    client = SuperMeClient(api_key="tok")
    client.ask_with_history(
        [
            {"role": "user", "content": "first"},
            {"role": "assistant", "content": "reply"},
            {"role": "user", "content": "follow-up"},
        ],
        username="ludo",
    )
    body = json.loads(route.calls[0].request.content)
    assert body["params"]["arguments"]["question"] == "follow-up"
    client.close()


# ---- chat.completions.create ----


@respx.mock
def test_chat_completions_create_returns_object():
    _mock_mcp_ask()
    client = SuperMeClient(api_key="tok")
    response = client.chat.completions.create(
        messages=[{"role": "user", "content": "hi"}],
        username="ludo",
    )
    assert isinstance(response, ChatCompletion)
    assert response.choices[0].message.content == "Growth marketing is..."
    assert response.choices[0].message.role == "assistant"
    assert response.metadata["conversation_id"] == "conv_123"
    assert response.metadata["target_user"] == "ludo"
    assert response.model == "gpt-4"
    client.close()


@respx.mock
def test_chat_completions_create_no_user_message_raises():
    client = SuperMeClient(api_key="tok")
    with pytest.raises(ValueError, match="at least one user message"):
        client.chat.completions.create(
            messages=[{"role": "system", "content": "be helpful"}],
            username="ludo",
        )
    client.close()


# ---- mcp_tool_call ----


@respx.mock
def test_mcp_tool_call():
    profile_result = {"name": "Ludo", "username": "ludo"}
    respx.post(f"{MCP_BASE}/mcp/").mock(
        return_value=httpx.Response(
            200,
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "result": {
                    "content": [
                        {"type": "text", "text": json.dumps(profile_result)},
                    ],
                },
            },
        )
    )
    client = SuperMeClient(api_key="tok")
    result = client.mcp_tool_call("get_profile", {"identifier": "ludo"})
    assert result["name"] == "Ludo"
    client.close()


# ---- MCP error handling ----


@respx.mock
def test_mcp_error_raises_runtime_error():
    respx.post(f"{MCP_BASE}/mcp/").mock(
        return_value=httpx.Response(
            200,
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "error": {"code": -32600, "message": "Invalid Request"},
            },
        )
    )
    client = SuperMeClient(api_key="tok")
    with pytest.raises(RuntimeError, match="MCP error -32600"):
        client.ask("hi", username="ludo")
    client.close()


@respx.mock
def test_http_error_raises():
    respx.post(f"{MCP_BASE}/mcp/").mock(
        return_value=httpx.Response(401, json={"error": "unauthorized"})
    )
    client = SuperMeClient(api_key="bad-tok")
    with pytest.raises(httpx.HTTPStatusError):
        client.ask("hi", username="ludo")
    client.close()


# ---- raw_request ----


@respx.mock
def test_raw_request():
    tools_response = {
        "jsonrpc": "2.0",
        "id": 1,
        "result": {"tools": [{"name": "ask", "description": "Ask a question"}]},
    }
    respx.post(f"{MCP_BASE}/mcp/").mock(
        return_value=httpx.Response(200, json=tools_response)
    )
    client = SuperMeClient(api_key="tok")
    result = client.raw_request("tools/list")
    assert result["tools"][0]["name"] == "ask"
    client.close()


# ---- context manager ----


@respx.mock
def test_context_manager():
    _mock_mcp_ask()
    with SuperMeClient(api_key="tok") as client:
        result = client.ask("hi", username="ludo")
        assert result == "Growth marketing is..."


# ---- live integration tests ----
# Run automatically when SUPERME_API_KEY is set and the backend is reachable.
# Skipped silently otherwise — no flags needed.


@pytest.mark.live
def test_live_list_tools(live_client):
    tools = live_client.mcp_list_tools()
    assert isinstance(tools, list), "tools/list should return a list"
    names = [t["name"] for t in tools]
    assert "ask" in names, f"'ask' tool missing from {names}"


@pytest.mark.live
def test_live_ask(live_client, live_username):
    result = live_client.ask("What is your name?", username=live_username)
    assert isinstance(result, str)
    assert len(result) > 0


@pytest.mark.live
def test_live_ask_with_history(live_client, live_username):
    messages = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"},
        {"role": "user", "content": "What can you tell me about yourself?"},
    ]
    text, conv_id = live_client.ask_with_history(messages, username=live_username)
    assert isinstance(text, str) and len(text) > 0
    assert conv_id is not None


@pytest.mark.live
def test_live_chat_completions_create(live_client, live_username):
    response = live_client.chat.completions.create(
        messages=[{"role": "user", "content": "Hello"}],
        username=live_username,
    )
    assert isinstance(response, ChatCompletion)
    assert isinstance(response.choices[0].message.content, str)
    assert response.choices[0].message.role == "assistant"


@pytest.mark.live
def test_live_mcp_tool_call(live_client, live_username):
    result = live_client.mcp_tool_call("ask", {
        "identifier": live_username,
        "question": "Say hi",
    })
    assert isinstance(result, dict)
    assert "response" in result
