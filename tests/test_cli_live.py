"""Live CLI tests — run against the real SuperMe API.

These tests require SUPERME_API_KEY in .env (or environment).
They are auto-skipped when the backend is not reachable.

Run with:
    pytest tests/test_cli_live.py -v
"""

import json

import pytest

from superme_sdk.cli import run


pytestmark = pytest.mark.live


@pytest.fixture()
def token_file(tmp_path, live_api_key):
    """Write the live API key to a temp token file for CLI commands."""
    if not live_api_key:
        pytest.skip("SUPERME_API_KEY not set")
    tf = tmp_path / "token"
    tf.write_text(live_api_key)
    return tf


# ------------------------------------------------------------------
# conversations
# ------------------------------------------------------------------


def test_conversations(token_file, backend_alive, capsys):
    if not backend_alive:
        pytest.skip("Backend offline")
    code = run(["conversations", "--limit", "5"], token_file=token_file)
    out = capsys.readouterr().out
    assert code == 0, f"Exit {code}: {out}"
    # Should be valid JSON (list or dict)
    parsed = json.loads(out.strip())
    assert isinstance(parsed, (list, dict))


# ------------------------------------------------------------------
# profile
# ------------------------------------------------------------------


def test_profile_self(token_file, backend_alive, capsys):
    if not backend_alive:
        pytest.skip("Backend offline")
    code = run(["profile"], token_file=token_file)
    out = capsys.readouterr().out
    assert code == 0, f"Exit {code}: {out}"


def test_profile_by_username(token_file, backend_alive, live_username, capsys):
    if not backend_alive:
        pytest.skip("Backend offline")
    code = run(["profile", live_username], token_file=token_file)
    out = capsys.readouterr().out
    # Either success with JSON or "No profile found."
    assert code == 0 or "No profile found" in out


# ------------------------------------------------------------------
# ask
# ------------------------------------------------------------------


def test_ask(token_file, backend_alive, live_username, capsys):
    if not backend_alive:
        pytest.skip("Backend offline")
    code = run(
        ["ask", "What do you work on?", "--username", live_username],
        token_file=token_file,
    )
    out = capsys.readouterr().out
    assert code == 0, f"Exit {code}: {out}"
    assert len(out.strip()) > 0


# ------------------------------------------------------------------
# chat (single-shot)
# ------------------------------------------------------------------


def test_chat_single(token_file, backend_alive, live_username, capsys):
    if not backend_alive:
        pytest.skip("Backend offline")
    code = run(
        ["chat", "Hello, what do you do?", "--username", live_username],
        token_file=token_file,
    )
    out = capsys.readouterr().out
    assert code == 0, f"Exit {code}: {out}"
    assert len(out.strip()) > 0


def test_chat_with_history(token_file, backend_alive, live_username, capsys):
    if not backend_alive:
        pytest.skip("Backend offline")
    history = json.dumps([{"role": "user", "content": "Hi"}, {"role": "assistant", "content": "Hello!"}])
    code = run(
        ["chat", "Tell me more", "--username", live_username, "--history", history],
        token_file=token_file,
    )
    out = capsys.readouterr().out
    assert code == 0, f"Exit {code}: {out}"


# ------------------------------------------------------------------
# find-user
# ------------------------------------------------------------------


def test_find_user(token_file, backend_alive, capsys):
    if not backend_alive:
        pytest.skip("Backend offline")
    code = run(["find-user", "duy"], token_file=token_file)
    out = capsys.readouterr().out
    assert code == 0, f"Exit {code}: {out}"


# ------------------------------------------------------------------
# search
# ------------------------------------------------------------------


def test_search(token_file, backend_alive, capsys):
    if not backend_alive:
        pytest.skip("Backend offline")
    code = run(["search", "product market fit"], token_file=token_file)
    out = capsys.readouterr().out
    assert code == 0, f"Exit {code}: {out}"


# ------------------------------------------------------------------
# mcp-tools
# ------------------------------------------------------------------


def test_mcp_tools(token_file, backend_alive, capsys):
    if not backend_alive:
        pytest.skip("Backend offline")
    code = run(["mcp-tools"], token_file=token_file)
    out = capsys.readouterr().out
    assert code == 0, f"Exit {code}: {out}"
    assert len(out.strip()) > 0
