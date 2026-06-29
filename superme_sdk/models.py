"""Response model classes (mirror OpenAI SDK objects)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, TypedDict


class Message:
    """A single chat message."""

    def __init__(self, data: dict) -> None:
        self.role: str = data.get("role", "assistant")
        self.content: str = data.get("content", "") or ""


class Choice:
    """One completion choice."""

    def __init__(self, data: dict) -> None:
        self.index: int = data.get("index", 0)
        self.message = Message(data.get("message") or {})
        self.finish_reason: Optional[str] = data.get("finish_reason")


class Usage:
    """Token usage statistics."""

    def __init__(self, data: dict) -> None:
        self.prompt_tokens: int = data.get("prompt_tokens", 0)
        self.completion_tokens: int = data.get("completion_tokens", 0)
        self.total_tokens: int = data.get("total_tokens", 0)


class ChatCompletion:
    """OpenAI-compatible chat completion response.

    SuperMe-specific fields (``metadata``) are preserved as attributes.
    """

    def __init__(self, data: dict) -> None:
        self.id: str = data.get("id", "")
        self.object: str = data.get("object", "chat.completion")
        self.created: int = data.get("created", 0)
        self.model: str = data.get("model", "")
        self.choices: list[Choice] = [Choice(c) for c in data.get("choices", [])]
        self.usage = Usage(data.get("usage") or {})
        self.metadata: Optional[dict] = data.get("metadata")


class ProvisionRecord(TypedDict, total=False):
    """A single provisioned member record."""

    user_id: str
    token: str
    name: str
    linkedin_url: Optional[str]
    contact_email: Optional[str]
    notes: Optional[str]
    claim_url: str
    status: str
    created_at: Optional[str]
    claimed_at: Optional[str]
    invited_at: Optional[str]
    socials: dict[str, str]
    doc_count: int
    audited: bool
    audited_at: Optional[str]
    deletion_requested_at: Optional[str]
    deletion_reason: Optional[str]
    reused: bool


class ProvisionProfile(TypedDict, total=False):
    """Input profile for :meth:`~superme_sdk.SuperMeClient.provision_create_batch`."""

    name: str
    linkedin_url: str
    contact_email: str
    notes: str
    socials: dict[str, str]
    external_urls: list[str]


class ProvisionInviteOutcome(TypedDict, total=False):
    user_id: str
    reason: str


class ProvisionCreateResponse(TypedDict, total=False):
    success: bool
    provision: ProvisionRecord


class ProvisionListResponse(TypedDict, total=False):
    success: bool
    provisions: list[ProvisionRecord]
    count: int


class ProvisionInviteResponse(TypedDict, total=False):
    success: bool
    sent: list[str]
    skipped: list[ProvisionInviteOutcome]
    failed: list[ProvisionInviteOutcome]


class StageInfo(TypedDict, total=False):
    """A single stage from the interview status API."""

    stage_number: int
    name: str
    status: str


class InterviewStatus(TypedDict, total=False):
    """Interview status response from ``get_interview_status``."""

    interview_id: str
    status: str
    stages: list[StageInfo]
    active_stage: int


@dataclass
class StreamEvent:
    """A single event yielded by streaming methods.

    Example::

        for event in client.ask_my_agent_stream("Summarise my last 3 posts"):
            if event.done:
                print("conversation_id:", event.conversation_id)
            else:
                print(event.text, end="", flush=True)

    Attributes:
        text: Text chunk (empty string on the done event).
        done: True on the final event — no more events will follow.
        conversation_id: Populated on the done event so callers can capture the ID
            without making a second API call.
    """

    text: str = field(default="")
    done: bool = field(default=False)
    conversation_id: Optional[str] = field(default=None)
