"""Pre-hardening contract tests for superme_sdk.client.

Tests the public API that was available BEFORE the SDK hardening commit (b04aab7).
Pre-hardening SDK was an OpenAI-compatible wrapper with:
  - client.token
  - client.ask(question, username, ...)
  - client.ask_with_history(messages, username, ...) -> (str, conv_id)
  - client.chat.completions.create(messages, extra_body={"username": ...})
  - client.low_level.raw_request(method, params)

These tests expose backward compatibility regressions in the hardened SDK.
No live backend required — all HTTP is mocked with respx.
"""

from __future__ import annotations

import json

import httpx
import pytest
import respx

from superme_sdk.client import SuperMeClient

# Latest SDK default MCP base URL
MCP_BASE = "https://mcp.superme.ai"

# MCP response for a successful "ask" tool call
_ASK_PAYLOAD = {
    "conversation_id": "conv_abc",
    "target_user": "alice",
    "target_user_id": "uid_999",
    "question": "What is PMF?",
    "response": "Growth marketing is...",
    "status": "success",
}

MCP_TOOL_RESPONSE = {
    "jsonrpc": "2.0",
    "id": 1,
    "result": {
        "content": [{"type": "text", "text": json.dumps(_ASK_PAYLOAD)}],
    },
}


def _mock_ask():
    return respx.post(f"{MCP_BASE}/mcp/").mock(
        return_value=httpx.Response(200, json=MCP_TOOL_RESPONSE)
    )


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------


def test_client_token_property():
    """Pre-hardening: client.token should return the api_key."""
    client = SuperMeClient(api_key="pre-hardening-key")
    assert client.token == "pre-hardening-key"
    if hasattr(client, "close"):
        client.close()


def test_client_base_url_stored():
    """Pre-hardening: client.base_url should be accessible."""
    client = SuperMeClient(api_key="key", base_url="https://api.superme.ai")
    assert "api.superme.ai" in client.base_url
    if hasattr(client, "close"):
        client.close()


# ---------------------------------------------------------------------------
# ask()
# ---------------------------------------------------------------------------


@respx.mock
def test_ask_returns_string():
    """Pre-hardening: ask() returns a plain str."""
    _mock_ask()
    client = SuperMeClient(api_key="tok")
    result = client.ask("What is PMF?", username="alice")
    assert isinstance(result, str)
    assert result == "Growth marketing is..."
    if hasattr(client, "close"):
        client.close()


@respx.mock
def test_ask_passes_username_as_identifier():
    """Pre-hardening: ask(username="alice") routes the question to alice."""
    route = _mock_ask()
    client = SuperMeClient(api_key="tok")
    client.ask("question", username="alice")

    body = json.loads(route.calls[0].request.content)
    assert body["params"]["arguments"]["identifier"] == "alice"
    if hasattr(client, "close"):
        client.close()


@respx.mock
def test_ask_incognito_flag():
    """Pre-hardening: ask(incognito=True) passes incognito to the backend."""
    route = _mock_ask()
    client = SuperMeClient(api_key="tok")
    client.ask("q", username="alice", incognito=True)

    body = json.loads(route.calls[0].request.content)
    assert body["params"]["arguments"].get("incognito") is True
    if hasattr(client, "close"):
        client.close()


@respx.mock
def test_ask_conversation_id():
    """Pre-hardening: ask(conversation_id=...) forwards the ID."""
    route = _mock_ask()
    client = SuperMeClient(api_key="tok")
    client.ask("q", username="alice", conversation_id="conv_xyz")

    body = json.loads(route.calls[0].request.content)
    assert body["params"]["arguments"].get("conversation_id") == "conv_xyz"
    if hasattr(client, "close"):
        client.close()


@respx.mock
def test_ask_auth_header():
    """Pre-hardening: ask() sends Authorization: Bearer <token>."""
    route = _mock_ask()
    client = SuperMeClient(api_key="my-secret-token")
    client.ask("q", username="alice")

    auth = route.calls[0].request.headers["authorization"]
    assert auth == "Bearer my-secret-token"
    if hasattr(client, "close"):
        client.close()


# ---------------------------------------------------------------------------
# ask_with_history()
# ---------------------------------------------------------------------------


@respx.mock
def test_ask_with_history_returns_tuple():
    """Pre-hardening: ask_with_history() returns (str, conv_id)."""
    _mock_ask()
    client = SuperMeClient(api_key="tok")
    result = client.ask_with_history(
        [{"role": "user", "content": "Hello"}], username="alice"
    )
    assert isinstance(result, tuple), "should return a tuple"
    text, conv_id = result
    assert isinstance(text, str)
    assert text == "Growth marketing is..."
    if hasattr(client, "close"):
        client.close()


@respx.mock
def test_ask_with_history_conv_id_from_response():
    """Pre-hardening: conversation_id comes from the backend response."""
    _mock_ask()
    client = SuperMeClient(api_key="tok")
    _, conv_id = client.ask_with_history(
        [{"role": "user", "content": "q"}], username="alice"
    )
    assert conv_id == "conv_abc"
    if hasattr(client, "close"):
        client.close()


@respx.mock
def test_ask_with_history_sends_last_user_message():
    """Pre-hardening: only the last user message is sent as the question."""
    route = _mock_ask()
    client = SuperMeClient(api_key="tok")
    client.ask_with_history(
        [
            {"role": "user", "content": "first message"},
            {"role": "assistant", "content": "some reply"},
            {"role": "user", "content": "follow-up question"},
        ],
        username="alice",
    )
    body = json.loads(route.calls[0].request.content)
    assert body["params"]["arguments"]["question"] == "follow-up question"
    if hasattr(client, "close"):
        client.close()


# ---------------------------------------------------------------------------
# chat.completions.create() with extra_body (pre-hardening canonical usage)
# ---------------------------------------------------------------------------


@respx.mock
def test_chat_completions_create_with_extra_body_username():
    """Pre-hardening: extra_body={"username": "alice"} must route to alice.

    Old SDK: client.chat was the raw OpenAI client; username was not a
    first-class kwarg, so callers tunnelled it through extra_body.
    """
    route = _mock_ask()
    client = SuperMeClient(api_key="tok")
    client.chat.completions.create(
        messages=[{"role": "user", "content": "hi"}],
        extra_body={"username": "alice"},
    )
    body = json.loads(route.calls[0].request.content)
    assert body["params"]["arguments"]["identifier"] == "alice", (
        "COMPAT FAILURE: extra_body username not forwarded to identifier"
    )
    if hasattr(client, "close"):
        client.close()


@respx.mock
def test_chat_completions_create_extra_body_incognito():
    """Pre-hardening: extra_body={"incognito": True} must be forwarded."""
    route = _mock_ask()
    client = SuperMeClient(api_key="tok")
    client.chat.completions.create(
        messages=[{"role": "user", "content": "hi"}],
        extra_body={"username": "alice", "incognito": True},
    )
    body = json.loads(route.calls[0].request.content)
    assert body["params"]["arguments"].get("incognito") is True, (
        "COMPAT FAILURE: extra_body incognito not forwarded"
    )
    if hasattr(client, "close"):
        client.close()


@respx.mock
def test_chat_completions_create_extra_body_conversation_id():
    """Pre-hardening: extra_body={"conversation_id": ...} must be forwarded."""
    route = _mock_ask()
    client = SuperMeClient(api_key="tok")
    client.chat.completions.create(
        messages=[{"role": "user", "content": "hi"}],
        extra_body={"username": "alice", "conversation_id": "conv_old"},
    )
    body = json.loads(route.calls[0].request.content)
    assert body["params"]["arguments"].get("conversation_id") == "conv_old", (
        "COMPAT FAILURE: extra_body conversation_id not forwarded"
    )
    if hasattr(client, "close"):
        client.close()


@respx.mock
def test_chat_completions_create_returns_response_with_content():
    """Pre-hardening: create() response exposes .choices[0].message.content."""
    _mock_ask()
    client = SuperMeClient(api_key="tok")
    response = client.chat.completions.create(
        messages=[{"role": "user", "content": "hi"}],
        extra_body={"username": "alice"},
    )
    assert hasattr(response, "choices")
    assert len(response.choices) > 0
    assert hasattr(response.choices[0], "message")
    assert response.choices[0].message.content == "Growth marketing is..."
    assert response.choices[0].message.role == "assistant"
    if hasattr(client, "close"):
        client.close()




# ---------------------------------------------------------------------------
# close() and context manager
# ---------------------------------------------------------------------------


@respx.mock
def test_close_is_idempotent():
    """Pre-hardening: close() (if present) must not raise on double-call."""
    _mock_ask()
    client = SuperMeClient(api_key="tok")
    client.ask("hi", username="alice")
    if hasattr(client, "close"):
        client.close()
        client.close()  # must not raise


@respx.mock
def test_context_manager_if_supported():
    """Context manager is optional pre-hardening; skip if absent."""
    if not hasattr(SuperMeClient, "__enter__"):
        pytest.skip("Context manager not supported in this SDK version")
    _mock_ask()
    with SuperMeClient(api_key="tok") as client:
        result = client.ask("hi", username="alice")
    assert result == "Growth marketing is..."
