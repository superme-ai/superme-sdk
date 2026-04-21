"""SuperMe SDK - Python client for SuperMe AI API"""

from .client import SuperMeClient
from .auth import load_token, save_token, remove_token, resolve_token
from .exceptions import (
    SuperMeError,
    AuthError,
    RateLimitError,
    NotFoundError,
    APIError,
    MCPError,
)
from .models import StreamEvent

__version__ = "0.2.0"
__all__ = [
    "SuperMeClient",
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
]
