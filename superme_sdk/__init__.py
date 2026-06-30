"""SuperMe SDK - Python client for SuperMe AI API"""

from .client import AsyncSuperMeClient, SuperMeClient
from .auth import load_token, save_token, remove_token, resolve_token
from .exceptions import (
    SuperMeError,
    AuthError,
    RateLimitError,
    NotFoundError,
    APIError,
    MCPError,
)
from .models import (
    StageInfo,
    InterviewStatus,
    ProvisionRecord,
    ProvisionProfile,
    ProvisionInviteOutcome,
    ProvisionCreateResponse,
    ProvisionListResponse,
    ProvisionInviteResponse,
)
from .streaming import (
    PartnerStreamChunk,
    ContentChunk,
    ToolChunk,
    DoneChunk,
    ErrorChunk,
)

__version__ = "0.8.0"
__all__ = [
    "SuperMeClient",
    "AsyncSuperMeClient",
    "load_token",
    "save_token",
    "remove_token",
    "resolve_token",
    "SuperMeError",
    "AuthError",
    "RateLimitError",
    "NotFoundError",
    "APIError",
    "MCPError",
    "StageInfo",
    "InterviewStatus",
    "ProvisionRecord",
    "ProvisionProfile",
    "ProvisionInviteOutcome",
    "ProvisionCreateResponse",
    "ProvisionListResponse",
    "ProvisionInviteResponse",
    "PartnerStreamChunk",
    "ContentChunk",
    "ToolChunk",
    "DoneChunk",
    "ErrorChunk",
]
