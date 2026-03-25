"""Tests for superme_sdk.cli — CLI commands (TDD)."""

import json
from io import StringIO
from unittest.mock import patch

import httpx
import pytest
import respx

from superme_sdk.auth import save_token, load_token
from superme_sdk.cli import main, run

BASE = "https://mcp.superme.ai"

ASK_RESULT = {
    "conversation_id": "conv_123",
    "target_user": "ludo",
    "target_user_id": "uid_456",
    "question": "What is PMF?",
    "response": "Product-market fit is...",
    "status": "success",
}

MCP_TOOL_RESPONSE = {
    "jsonrpc": "2.0",
    "id": 1,
    "result": {
        "content": [
            {"type": "text", "text": json.dumps(ASK_RESULT)},
        ],
    },
}


@pytest.fixture()
def token_file(tmp_path):
    return tmp_path / "token"


# ---- login ----


def test_login_saves_token(token_file, capsys):
    run(["login", "--token", "my-api-key"], token_file=token_file)
    assert load_token(token_file) == "my-api-key"
    out = capsys.readouterr().out
    assert "Logged in" in out


def test_login_prompts_when_no_token_flag(token_file, capsys):
    with patch("superme_sdk.cli.commands.read_token_input", return_value="prompted-key"):
        run(["login"], token_file=token_file)
    assert load_token(token_file) == "prompted-key"


def test_login_rejects_empty_token(token_file, capsys):
    code = run(["login", "--token", ""], token_file=token_file)
    assert code != 0
    assert load_token(token_file) is None
    out = capsys.readouterr().out
    assert "empty" in out.lower() or "required" in out.lower()


def test_login_overwrites_existing_token(token_file, capsys):
    save_token("old-key", token_file)
    run(["login", "--token", "new-key"], token_file=token_file)
    assert load_token(token_file) == "new-key"


# ---- logout ----


def test_logout_removes_token(token_file, capsys):
    save_token("my-key", token_file)
    run(["logout"], token_file=token_file)
    assert load_token(token_file) is None
    out = capsys.readouterr().out
    assert "Logged out" in out


def test_logout_when_not_logged_in(token_file, capsys):
    run(["logout"], token_file=token_file)
    out = capsys.readouterr().out
    assert "not logged in" in out.lower() or "no token" in out.lower()


# ---- status ----


def test_status_when_logged_in(token_file, capsys):
    save_token("my-key", token_file)
    run(["status"], token_file=token_file)
    out = capsys.readouterr().out
    assert "logged in" in out.lower() or "authenticated" in out.lower()
    # should mask the token
    assert "my-key" not in out


def test_status_when_not_logged_in(token_file, capsys):
    run(["status"], token_file=token_file)
    out = capsys.readouterr().out
    assert "not logged in" in out.lower() or "no token" in out.lower()


# ---- ask ----


@respx.mock
def test_ask_uses_saved_token(token_file, capsys):
    save_token("saved-tok", token_file)
    respx.post(f"{BASE}/").mock(
        return_value=httpx.Response(200, json=MCP_TOOL_RESPONSE)
    )
    run(["ask", "What is PMF?", "--username", "ludo"], token_file=token_file)
    out = capsys.readouterr().out
    assert "Product-market fit is..." in out


@respx.mock
def test_ask_sends_auth_header(token_file, monkeypatch):
    monkeypatch.delenv("SUPERME_API_KEY", raising=False)
    save_token("my-bearer", token_file)
    route = respx.post(f"{BASE}/").mock(
        return_value=httpx.Response(200, json=MCP_TOOL_RESPONSE)
    )
    run(["ask", "hi", "--username", "ludo"], token_file=token_file)
    auth = route.calls[0].request.headers["authorization"]
    assert auth == "Bearer my-bearer"


def test_ask_fails_without_token(token_file, capsys, monkeypatch):
    monkeypatch.delenv("SUPERME_API_KEY", raising=False)
    code = run(["ask", "What is PMF?"], token_file=token_file)
    assert code != 0
    out = capsys.readouterr().out
    assert "login" in out.lower() or "token" in out.lower()


@respx.mock
def test_ask_default_username(token_file, capsys):
    save_token("tok", token_file)
    route = respx.post(f"{BASE}/").mock(
        return_value=httpx.Response(200, json=MCP_TOOL_RESPONSE)
    )
    run(["ask", "hello"], token_file=token_file)
    body = json.loads(route.calls[0].request.content)
    assert body["params"]["arguments"]["identifier"] == "ludo"


@respx.mock
def test_ask_with_conversation_id(token_file, capsys):
    save_token("tok", token_file)
    route = respx.post(f"{BASE}/").mock(
        return_value=httpx.Response(200, json=MCP_TOOL_RESPONSE)
    )
    run(
        ["ask", "follow up", "--conversation-id", "conv_abc"],
        token_file=token_file,
    )
    body = json.loads(route.calls[0].request.content)
    assert body["params"]["arguments"]["conversation_id"] == "conv_abc"


# ---- no args / help ----


def test_no_args_shows_help(capsys):
    code = run([])
    out = capsys.readouterr().out
    assert "usage" in out.lower() or "superme" in out.lower()


# ---- version ----


def test_version_flag(capsys):
    with pytest.raises(SystemExit, match="0"):
        run(["--version"])
    out = capsys.readouterr().out
    assert "0." in out  # version string like 0.2.0
