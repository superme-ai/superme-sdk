"""Tests for superme_sdk.client — SuperMeClient (MCP JSON-RPC transport)."""

import json

import httpx
import pytest
import respx

from superme_sdk.client import SuperMeClient, ChatCompletion

BASE = "https://mcp.superme.ai"

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
    return respx.post(f"{BASE}/").mock(
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
    respx.post(f"{BASE}/").mock(
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
    respx.post(f"{BASE}/").mock(
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
    respx.post(f"{BASE}/").mock(
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
    respx.post(f"{BASE}/").mock(
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


def _mock_tool(result: dict):
    """Helper: mock a single MCP tools/call response."""
    return respx.post(f"{BASE}/").mock(
        return_value=httpx.Response(
            200,
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "result": {"content": [{"type": "text", "text": json.dumps(result)}]},
            },
        )
    )


# ---- list_conversations ----


@respx.mock
def test_list_conversations_sends_correct_tool():
    route = _mock_tool([{"id": "c1"}, {"id": "c2"}])
    client = SuperMeClient(api_key="tok")
    client.list_conversations(limit=5)
    body = json.loads(route.calls[0].request.content)
    assert body["params"]["name"] == "list_conversations"
    assert body["params"]["arguments"]["limit"] == 5
    client.close()


# ---- get_conversation ----


@respx.mock
def test_get_conversation_sends_correct_tool():
    route = _mock_tool({"id": "conv_abc", "messages": []})
    client = SuperMeClient(api_key="tok")
    result = client.get_conversation("conv_abc")
    body = json.loads(route.calls[0].request.content)
    assert body["params"]["name"] == "get_conversation"
    assert body["params"]["arguments"]["conversation_id"] == "conv_abc"
    assert result["id"] == "conv_abc"
    client.close()


# ---- ask_my_agent ----


@respx.mock
def test_ask_my_agent_sends_question():
    route = _mock_tool({"response": "Here is my answer", "conversation_id": "c99"})
    client = SuperMeClient(api_key="tok")
    result = client.ask_my_agent("Summarize my notes")
    body = json.loads(route.calls[0].request.content)
    assert body["params"]["name"] == "ask_my_agent"
    assert body["params"]["arguments"]["question"] == "Summarize my notes"
    assert "conversation_id" not in body["params"]["arguments"]
    assert result["response"] == "Here is my answer"
    client.close()


@respx.mock
def test_ask_my_agent_with_conversation_id():
    route = _mock_tool({"response": "Continued", "conversation_id": "c1"})
    client = SuperMeClient(api_key="tok")
    client.ask_my_agent("Follow up", conversation_id="c1")
    body = json.loads(route.calls[0].request.content)
    assert body["params"]["arguments"]["conversation_id"] == "c1"
    client.close()


# ---- get_profile ----


@respx.mock
def test_get_profile_with_identifier():
    route = _mock_tool({"username": "ludo", "name": "Ludo"})
    client = SuperMeClient(api_key="tok")
    result = client.get_profile("ludo")
    body = json.loads(route.calls[0].request.content)
    assert body["params"]["name"] == "get_profile"
    assert body["params"]["arguments"]["identifier"] == "ludo"
    assert result["username"] == "ludo"
    client.close()


@respx.mock
def test_get_profile_without_identifier_sends_empty_args():
    route = _mock_tool({"username": "me"})
    client = SuperMeClient(api_key="tok")
    client.get_profile()
    body = json.loads(route.calls[0].request.content)
    assert body["params"]["arguments"] == {}
    client.close()


# ---- find_user_by_name ----


@respx.mock
def test_find_user_by_name():
    route = _mock_tool({"results": [{"username": "casey"}]})
    client = SuperMeClient(api_key="tok")
    result = client.find_user_by_name("casey", limit=3)
    body = json.loads(route.calls[0].request.content)
    assert body["params"]["name"] == "find_user_by_name"
    assert body["params"]["arguments"]["name"] == "casey"
    assert body["params"]["arguments"]["limit"] == 3
    assert result["results"][0]["username"] == "casey"
    client.close()


# ---- find_users_by_names ----


@respx.mock
def test_find_users_by_names():
    route = _mock_tool({"resolved": {}})
    client = SuperMeClient(api_key="tok")
    client.find_users_by_names(["alice", "bob"], limit_per_name=2)
    body = json.loads(route.calls[0].request.content)
    assert body["params"]["name"] == "find_users_by_names"
    assert body["params"]["arguments"]["names"] == ["alice", "bob"]
    assert body["params"]["arguments"]["limit_per_name"] == 2
    client.close()


# ---- perspective_search ----


@respx.mock
def test_perspective_search():
    route = _mock_tool({"answer": "Many experts say...", "viewpoints": []})
    client = SuperMeClient(api_key="tok")
    result = client.perspective_search("What is PLG?")
    body = json.loads(route.calls[0].request.content)
    assert body["params"]["name"] == "perspective_search"
    assert body["params"]["arguments"]["question"] == "What is PLG?"
    assert result["answer"] == "Many experts say..."
    client.close()


# ---- add_internal_content ----


@respx.mock
def test_add_internal_content_minimal():
    route = _mock_tool({"success": True, "learning_ids": ["l1"]})
    client = SuperMeClient(api_key="tok")
    result = client.add_internal_content(["note 1", "note 2"])
    body = json.loads(route.calls[0].request.content)
    assert body["params"]["name"] == "add_internal_content"
    assert body["params"]["arguments"]["input"] == ["note 1", "note 2"]
    assert "extended_content" not in body["params"]["arguments"]
    assert result["success"] is True
    client.close()


@respx.mock
def test_add_internal_content_with_optional_fields():
    route = _mock_tool({"success": True, "learning_ids": ["l2"]})
    client = SuperMeClient(api_key="tok")
    client.add_internal_content(
        ["note"],
        extended_content="long form",
        past_instructions="use for Q&A only",
    )
    body = json.loads(route.calls[0].request.content)
    args = body["params"]["arguments"]
    assert args["extended_content"] == "long form"
    assert args["past_instructions"] == "use for Q&A only"
    client.close()


# ---- update_internal_content ----


@respx.mock
def test_update_internal_content():
    route = _mock_tool({"success": True})
    client = SuperMeClient(api_key="tok")
    client.update_internal_content("l1", user_input=["updated note"])
    body = json.loads(route.calls[0].request.content)
    assert body["params"]["name"] == "update_internal_content"
    args = body["params"]["arguments"]
    assert args["learning_id"] == "l1"
    assert args["user_input"] == ["updated note"]
    assert "extended_content" not in args
    client.close()


# ---- add_external_content ----


@respx.mock
def test_add_external_content():
    route = _mock_tool({"successful": 2, "existing": 0, "failed": 0})
    client = SuperMeClient(api_key="tok")
    urls = [{"url": "https://example.com/a"}, {"url": "https://example.com/b"}]
    result = client.add_external_content(urls)
    body = json.loads(route.calls[0].request.content)
    assert body["params"]["name"] == "add_external_content"
    assert body["params"]["arguments"]["urls"] == urls
    assert body["params"]["arguments"]["reference"] is True
    assert body["params"]["arguments"]["instant_recrawl"] is True
    assert result["successful"] == 2
    client.close()


# ---- check_uncrawled_urls ----


@respx.mock
def test_check_uncrawled_urls():
    route = _mock_tool({"uncrawled_urls": ["https://example.com/new"], "count": 1})
    client = SuperMeClient(api_key="tok")
    result = client.check_uncrawled_urls(["https://example.com/new", "https://example.com/old"])
    body = json.loads(route.calls[0].request.content)
    assert body["params"]["name"] == "check_uncrawled_urls"
    assert body["params"]["arguments"]["urls"] == ["https://example.com/new", "https://example.com/old"]
    assert result["count"] == 1
    client.close()


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


@pytest.mark.live
def test_live_list_conversations(live_client):
    result = live_client.list_conversations(limit=3)
    assert isinstance(result, (list, dict))


@pytest.mark.live
def test_live_get_conversation(live_client):
    convs = live_client.list_conversations(limit=1)
    if not convs:
        pytest.skip("No conversations to fetch")
    conv_id = convs[0].get("conversation_id") or convs[0].get("id")
    result = live_client.get_conversation(conv_id)
    assert isinstance(result, (dict, list))


@pytest.mark.live
def test_live_ask_my_agent(live_client):
    result = live_client.ask_my_agent("Say hi")
    assert isinstance(result, dict)
    assert "response" in result


@pytest.mark.live
def test_live_get_profile(live_client, live_username):
    result = live_client.get_profile(live_username)
    assert isinstance(result, (dict, list))


@pytest.mark.live
def test_live_get_profile_self(live_client):
    result = live_client.get_profile()
    assert isinstance(result, (dict, list))


@pytest.mark.live
def test_live_find_user_by_name(live_client, live_username):
    result = live_client.find_user_by_name(live_username, limit=3)
    assert isinstance(result, (list, dict))


@pytest.mark.live
def test_live_find_users_by_names(live_client, live_username):
    result = live_client.find_users_by_names([live_username], limit_per_name=2)
    assert isinstance(result, (list, dict))


@pytest.mark.live
def test_live_perspective_search(live_client):
    result = live_client.perspective_search("What is product-market fit?")
    assert isinstance(result, (dict, list))


@pytest.mark.live
def test_live_check_uncrawled_urls(live_client):
    result = live_client.check_uncrawled_urls(["https://example.com/does-not-exist-xyz"])
    assert isinstance(result, (dict, list))
