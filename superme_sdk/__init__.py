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
from .models import StreamEvent, StageInfo, InterviewStatus

__version__ = "0.1.0"
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
    "StreamEvent",
    "StageInfo",
    "InterviewStatus",
]
