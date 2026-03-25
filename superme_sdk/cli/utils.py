"""Shared utilities for the SuperMe CLI."""

from __future__ import annotations

import getpass


def read_token_input() -> str:
    """Prompt the user for an API token without echoing it to the terminal."""
    return getpass.getpass("Enter your SuperMe API key: ")


def mask_token(token: str) -> str:
    """Return a redacted view of *token* for safe display.

    Shows the first 4 and last 4 characters separated by '...'.
    Tokens shorter than 9 characters show only 2 chars on each side.

    Examples:
        >>> mask_token("sk-abcdefgh1234")
        'sk-a...1234'
        >>> mask_token("short")
        'sh...rt'
    """
    if len(token) <= 8:
        return token[:2] + "..." + token[-2:]
    return token[:4] + "..." + token[-4:]
