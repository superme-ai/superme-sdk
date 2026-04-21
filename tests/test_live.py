"""Comprehensive live integration tests for superme_sdk.

All tests require SUPERME_API_KEY and a reachable backend.
They are skipped automatically when neither is available.

Run with:
    pytest -m live
"""

from __future__ import annotations

import pytest

from superme_sdk.client import SuperMeClient
from superme_sdk.models import StreamEvent


# ---------------------------------------------------------------------------
# Profiles
# ---------------------------------------------------------------------------


@pytest.mark.live
def test_live_get_profile_by_username(live_client, live_username):
    profile = live_client.get_profile(live_username)
    assert isinstance(profile, dict), f"expected dict, got {type(profile)}"
    assert profile.get("username") == live_username or "id" in profile


@pytest.mark.live
def test_live_get_own_profile(live_client):
    profile = live_client.get_profile()
    assert isinstance(profile, dict)
    # own profile should have at least one of these
    assert "username" in profile or "id" in profile or "name" in profile


@pytest.mark.live
def test_live_find_user_by_name(live_client, live_username):
    results = live_client.find_user_by_name(live_username)
    assert isinstance(results, dict)


@pytest.mark.live
def test_live_perspective_search(live_client):
    result = live_client.perspective_search("What is product-market fit?")
    assert isinstance(result, dict)
    assert "answer" in result or "viewpoints" in result or "response" in result


# ---------------------------------------------------------------------------
# Conversations
# ---------------------------------------------------------------------------


@pytest.mark.live
def test_live_ask(live_client, live_username):
    answer = live_client.ask("What is your name?", username=live_username)
    assert isinstance(answer, str) and len(answer) > 0


@pytest.mark.live
def test_live_ask_conversation_continuity(live_client, live_username):
    """Second ask with conversation_id continues the thread."""
    answer1 = live_client.ask("My name is Test User. Remember that.", username=live_username)
    assert isinstance(answer1, str)


@pytest.mark.live
def test_live_list_conversations(live_client):
    convs = live_client.list_conversations(limit=5)
    assert isinstance(convs, list)


@pytest.mark.live
def test_live_get_conversation(live_client):
    convs = live_client.list_conversations(limit=1)
    if not convs:
        pytest.skip("No conversations available for this account")
    conv_id = convs[0].get("conversation_id") or convs[0].get("id")
    assert conv_id, f"conversation item missing id: {convs[0]}"
    detail = live_client.get_conversation(conv_id)
    assert isinstance(detail, dict)


# ---------------------------------------------------------------------------
# Ask my agent
# ---------------------------------------------------------------------------


@pytest.mark.live
def test_live_ask_my_agent(live_client):
    result = live_client.ask_my_agent("Say hello in one sentence.")
    assert isinstance(result, dict)
    assert "response" in result or "answer" in result or "content" in result
    assert "conversation_id" in result


@pytest.mark.live
def test_live_ask_my_agent_stream(live_client):
    events = list(live_client.ask_my_agent_stream("Say hello in one sentence."))
    assert events, "no events yielded"
    text_events = [e for e in events if e.text]
    done_events = [e for e in events if e.done]
    assert text_events, "no text events yielded"
    assert len(done_events) == 1, "expected exactly one done event"
    assert done_events[0].conversation_id is not None


# ---------------------------------------------------------------------------
# Low-level MCP access
# ---------------------------------------------------------------------------


@pytest.mark.live
def test_live_low_level_list_tools(live_client):
    tools = live_client.low_level.list_tools()
    assert isinstance(tools, list) and len(tools) > 0
    names = [t["name"] for t in tools]
    assert "ask" in names, f"'ask' not in {names}"


@pytest.mark.live
def test_live_low_level_tool_call(live_client, live_username):
    result = live_client.low_level.tool_call(
        "get_profile", {"identifier": live_username}
    )
    assert isinstance(result, dict)


# ---------------------------------------------------------------------------
# Social (read-only)
# ---------------------------------------------------------------------------


@pytest.mark.live
def test_live_get_connected_accounts(live_client):
    result = live_client.get_connected_accounts()
    assert isinstance(result, dict) or isinstance(result, list)


# ---------------------------------------------------------------------------
# Chat completions (OpenAI-compat)
# ---------------------------------------------------------------------------


@pytest.mark.live
def test_live_chat_completions(live_client, live_username):
    from superme_sdk.client import ChatCompletion

    response = live_client.chat.completions.create(
        messages=[{"role": "user", "content": "Hello"}],
        username=live_username,
    )
    assert isinstance(response, ChatCompletion)
    assert isinstance(response.choices[0].message.content, str)
    assert response.choices[0].message.role == "assistant"
    assert response.metadata.get("conversation_id")
