"""Tests for workgroup SDK methods."""

import json

import httpx
import pytest
import respx

from superme_sdk.client import SuperMeClient

MCP_BASE = "https://mcp.superme.ai"

GROUP = {
    "id": "wg_abc",
    "owner_user_id": "user_1",
    "handle": "growth-board",
    "name": "Growth advisory board",
    "description": "",
    "members": [{"user_id": "user_2", "name": "Casey"}],
    "created_at": "2026-04-30T00:00:00+00:00",
    "updated_at": "2026-04-30T00:00:00+00:00",
    "last_used_at": None,
}


def _mock_mcp(payload: dict):
    """Mock POST / returning the given payload as the tool result."""
    rpc = {
        "jsonrpc": "2.0",
        "id": 1,
        "result": {"content": [{"type": "text", "text": json.dumps(payload)}]},
    }
    return respx.post(f"{MCP_BASE}/mcp/").mock(
        return_value=httpx.Response(200, json=rpc)
    )


@respx.mock
def test_list_workgroups_returns_list():
    _mock_mcp({"workgroups": [GROUP], "count": 1})
    client = SuperMeClient(api_key="tok")
    result = client.list_workgroups()
    assert result == [GROUP]
    client.close()


@respx.mock
def test_list_workgroups_empty():
    _mock_mcp({"workgroups": [], "count": 0})
    client = SuperMeClient(api_key="tok")
    assert client.list_workgroups() == []
    client.close()


@respx.mock
def test_get_workgroup_returns_dict():
    _mock_mcp(GROUP)
    client = SuperMeClient(api_key="tok")
    result = client.get_workgroup("wg_abc")
    assert result == GROUP
    client.close()


@respx.mock
def test_get_workgroup_returns_none_on_error():
    _mock_mcp({"error": "Workgroup not found: wg_missing"})
    client = SuperMeClient(api_key="tok")
    assert client.get_workgroup("wg_missing") is None
    client.close()


@respx.mock
def test_create_workgroup_returns_group():
    route = _mock_mcp(GROUP)
    client = SuperMeClient(api_key="tok")
    result = client.create_workgroup(
        name="Growth advisory board",
        handle="growth-board",
        members=[{"user_id": "user_2", "name": "Casey"}],
    )
    assert result == GROUP
    # Verify the tool name + arguments
    body = json.loads(route.calls[0].request.content)
    assert body["params"]["name"] == "create_workgroup"
    args = body["params"]["arguments"]
    assert args["name"] == "Growth advisory board"
    assert args["handle"] == "growth-board"
    assert args["members"] == [{"user_id": "user_2", "name": "Casey"}]
    client.close()


@respx.mock
def test_update_workgroup_only_passes_provided_fields():
    route = _mock_mcp(GROUP)
    client = SuperMeClient(api_key="tok")
    client.update_workgroup("wg_abc", name="renamed")
    body = json.loads(route.calls[0].request.content)
    args = body["params"]["arguments"]
    assert args == {"workgroup_id": "wg_abc", "name": "renamed"}
    client.close()


@pytest.mark.asyncio
@respx.mock
async def test_async_list_workgroups():
    from superme_sdk.client import AsyncSuperMeClient

    _mock_mcp({"workgroups": [GROUP], "count": 1})
    async with AsyncSuperMeClient(api_key="tok") as client:
        result = await client.list_workgroups()
        assert result == [GROUP]
