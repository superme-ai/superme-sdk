"""Typed shapes for the SSE chunks yielded by streaming calls.

``ask(..., stream=True)`` yields these four partner chunk types — see the
partner API docs (the source of truth):
https://api.superme.ai/partner/docs

These are ``TypedDict``s: at runtime each chunk is a plain ``dict`` (zero
behavior change), but type checkers and IDEs can tell you the exact shape.
Discriminate on ``type``; the stream stops after ``done`` or ``error``.
"""

from __future__ import annotations

from typing import Literal, TypedDict, Union


class ContentChunk(TypedDict):
    """A piece of the answer text."""

    type: Literal["content"]
    text: str


class ToolChunk(TypedDict):
    """A tool the agent is calling (human-readable label, e.g. "Searching the web")."""

    type: Literal["tool"]
    label: str


class DoneChunk(TypedDict):
    """Terminal: finished. Use ``conversation_id`` to continue the thread."""

    type: Literal["done"]
    conversation_id: str


class ErrorChunk(TypedDict):
    """Terminal: the turn failed."""

    type: Literal["error"]
    message: str


PartnerStreamChunk = Union[ContentChunk, ToolChunk, DoneChunk, ErrorChunk]
"""Every chunk a partner stream can yield. Stops after ``done`` or ``error``."""
