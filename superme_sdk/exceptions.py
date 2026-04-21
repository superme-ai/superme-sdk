"""Typed exception hierarchy for SuperMe SDK errors."""

from __future__ import annotations


class SuperMeError(Exception):
    """Base class for all SuperMe SDK errors."""

    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class AuthError(SuperMeError):
    """Authentication or authorisation failed (HTTP 401/403)."""


class RateLimitError(SuperMeError):
    """Request rate limit exceeded (HTTP 429)."""


class NotFoundError(SuperMeError):
    """Requested resource was not found (HTTP 404)."""


class APIError(SuperMeError):
    """Unexpected API error (any other 4xx/5xx)."""


class MCPError(SuperMeError):
    """MCP JSON-RPC protocol error (error response from the MCP server).

    Attributes:
        code: The JSON-RPC error code.
    """

    def __init__(self, message: str, *, code: int | None = None) -> None:
        super().__init__(message)
        self.code = code
