"""Tests for superme_sdk.client — SuperMeClient."""

import json

import httpx
import pytest
import respx

from superme_sdk.client import SuperMeClient

BASE = "https://api.superme.ai"

# Sample completion response matching the backend schema
COMPLETION_RESPONSE = {
    "id": "chatcmpl-abc123",
    "object": "chat.completion",
    "created": 1700000000,
    "model": "gpt-4",
    "choices": [
        {
            "index": 0,
            "message": {"role": "assistant", "content": "Growth marketing is..."},
            "finish_reason": "stop",
        }
    ],
    "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
    "metadata": {"conversation_id": "conv_123"},
}


# ---- construction ----


def test_client_raises_on_empty_key():
    with pytest.raises(ValueError, match="api_key is required"):
        SuperMeClient(api_key="")


def test_client_explicit_key():
    client = SuperMeClient(api_key="explicit")
    assert client.token == "explicit"
    client.close()


def test_client_explicit_key():
    client = SuperMeClient(api_key="explicit")
    assert client.token == "explicit"
    client.close()


# ---- ask ----


@respx.mock
def test_ask_returns_text():
    respx.post(f"{BASE}/sdk/chat/completions").mock(
        return_value=httpx.Response(200, json=COMPLETION_RESPONSE)
    )
    client = SuperMeClient(api_key="tok")
    result = client.ask("What is PMF?", username="ludo")
    assert result == "Growth marketing is..."
    client.close()


@respx.mock
def test_ask_sends_correct_body():
    route = respx.post(f"{BASE}/sdk/chat/completions").mock(
        return_value=httpx.Response(200, json=COMPLETION_RESPONSE)
    )
    client = SuperMeClient(api_key="tok")
    client.ask("question", username="alice", max_tokens=500, incognito=True)

    body = json.loads(route.calls[0].request.content)
    assert body["username"] == "alice"
    assert body["max_tokens"] == 500
    assert body["incognito"] is True
    assert body["messages"] == [{"role": "user", "content": "question"}]
    client.close()


@respx.mock
def test_ask_sends_auth_header():
    route = respx.post(f"{BASE}/sdk/chat/completions").mock(
        return_value=httpx.Response(200, json=COMPLETION_RESPONSE)
    )
    client = SuperMeClient(api_key="my-jwt")
    client.ask("hi", username="ludo")

    auth = route.calls[0].request.headers["authorization"]
    assert auth == "Bearer my-jwt"
    client.close()


# ---- ask_with_history ----


@respx.mock
def test_ask_with_history_returns_tuple():
    respx.post(f"{BASE}/sdk/chat/completions").mock(
        return_value=httpx.Response(200, json=COMPLETION_RESPONSE)
    )
    client = SuperMeClient(api_key="tok")
    text, conv_id = client.ask_with_history(
        [{"role": "user", "content": "Q1"}], username="ludo"
    )
    assert text == "Growth marketing is..."
    assert conv_id == "conv_123"
    client.close()


@respx.mock
def test_ask_with_history_no_metadata():
    resp = {**COMPLETION_RESPONSE, "metadata": None}
    respx.post(f"{BASE}/sdk/chat/completions").mock(
        return_value=httpx.Response(200, json=resp)
    )
    client = SuperMeClient(api_key="tok")
    text, conv_id = client.ask_with_history(
        [{"role": "user", "content": "Q1"}], username="ludo"
    )
    assert conv_id is None
    client.close()


# ---- chat_completions ----


@respx.mock
def test_chat_completions_returns_dict():
    respx.post(f"{BASE}/sdk/chat/completions").mock(
        return_value=httpx.Response(200, json=COMPLETION_RESPONSE)
    )
    client = SuperMeClient(api_key="tok")
    data = client.chat_completions(
        messages=[{"role": "user", "content": "hi"}], username="ludo"
    )
    assert isinstance(data, dict)
    assert data["choices"][0]["message"]["content"] == "Growth marketing is..."
    client.close()


# ---- raw_request ----


@respx.mock
def test_raw_request():
    respx.post(f"{BASE}/mcp").mock(
        return_value=httpx.Response(200, json={"status": "ok"})
    )
    client = SuperMeClient(api_key="tok")
    resp = client.raw_request("/mcp", json={"method": "initialize"})
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
    client.close()


# ---- error handling ----


@respx.mock
def test_ask_raises_on_http_error():
    respx.post(f"{BASE}/sdk/chat/completions").mock(
        return_value=httpx.Response(401, json={"error": "unauthorized"})
    )
    client = SuperMeClient(api_key="bad-tok")
    with pytest.raises(httpx.HTTPStatusError):
        client.ask("hi", username="ludo")
    client.close()


# ---- context manager ----


@respx.mock
def test_context_manager():
    respx.post(f"{BASE}/sdk/chat/completions").mock(
        return_value=httpx.Response(200, json=COMPLETION_RESPONSE)
    )
    with SuperMeClient(api_key="tok") as client:
        result = client.ask("hi", username="ludo")
        assert result == "Growth marketing is..."
