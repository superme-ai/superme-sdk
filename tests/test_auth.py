"""Tests for superme_sdk.auth — token persistence."""

import os
from pathlib import Path

import pytest

from superme_sdk.auth import load_token, save_token, remove_token, resolve_token


@pytest.fixture()
def token_file(tmp_path):
    """Return a temporary token file path."""
    return tmp_path / "token"


# ---- load_token ----


def test_load_token_returns_none_when_missing(token_file):
    assert load_token(token_file) is None


def test_load_token_returns_none_when_empty(token_file):
    token_file.write_text("")
    assert load_token(token_file) is None


def test_load_token_strips_whitespace(token_file):
    token_file.write_text("  abc123\n  ")
    assert load_token(token_file) == "abc123"


def test_load_token_reads_value(token_file):
    token_file.write_text("my-jwt-token\n")
    assert load_token(token_file) == "my-jwt-token"


# ---- save_token ----


def test_save_token_creates_file(token_file):
    save_token("tok_abc", token_file)
    assert token_file.read_text().strip() == "tok_abc"


def test_save_token_creates_parent_dirs(tmp_path):
    nested = tmp_path / "a" / "b" / "token"
    save_token("tok_nested", nested)
    assert nested.read_text().strip() == "tok_nested"


def test_save_token_sets_permissions(token_file):
    save_token("tok_perms", token_file)
    assert oct(token_file.stat().st_mode & 0o777) == "0o600"


def test_save_token_overwrites(token_file):
    save_token("old", token_file)
    save_token("new", token_file)
    assert load_token(token_file) == "new"


# ---- remove_token ----


def test_remove_token_deletes_file(token_file):
    save_token("tok_del", token_file)
    assert remove_token(token_file) is True
    assert not token_file.exists()


def test_remove_token_returns_false_when_missing(token_file):
    assert remove_token(token_file) is False


# ---- resolve_token ----


def test_resolve_token_explicit_wins(token_file, monkeypatch):
    save_token("file-tok", token_file)
    monkeypatch.setenv("SUPERME_API_KEY", "env-tok")
    result = resolve_token(api_key="explicit-tok", token_file=token_file)
    assert result == "explicit-tok"


def test_resolve_token_env_over_file(token_file, monkeypatch):
    save_token("file-tok", token_file)
    monkeypatch.setenv("SUPERME_API_KEY", "env-tok")
    result = resolve_token(token_file=token_file)
    assert result == "env-tok"


def test_resolve_token_falls_back_to_file(token_file, monkeypatch):
    monkeypatch.delenv("SUPERME_API_KEY", raising=False)
    save_token("file-tok", token_file)
    result = resolve_token(token_file=token_file)
    assert result == "file-tok"


def test_resolve_token_returns_none_when_nothing(token_file, monkeypatch):
    monkeypatch.delenv("SUPERME_API_KEY", raising=False)
    assert resolve_token(token_file=token_file) is None
