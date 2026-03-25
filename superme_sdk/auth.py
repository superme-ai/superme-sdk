"""Token persistence for SuperMe SDK.

Reads/writes API tokens from ~/.superme/token (same location used by mcp-install.sh).
"""

import os
from pathlib import Path

# Default token file location (shared with mcp-install.sh)
DEFAULT_CONFIG_DIR = Path.home() / ".superme"
DEFAULT_TOKEN_FILE = DEFAULT_CONFIG_DIR / "token"


def load_token(token_file: Path | str | None = None) -> str | None:
    """Load API token from disk.

    Args:
        token_file: Path to token file. Defaults to ~/.superme/token.

    Returns:
        Token string or None if not found.
    """
    path = Path(token_file) if token_file else DEFAULT_TOKEN_FILE
    if path.is_file():
        token = path.read_text().strip()
        return token if token else None
    return None


def save_token(token: str, token_file: Path | str | None = None) -> Path:
    """Save API token to disk.

    Args:
        token: The API token to save.
        token_file: Path to token file. Defaults to ~/.superme/token.

    Returns:
        Path where token was saved.
    """
    path = Path(token_file) if token_file else DEFAULT_TOKEN_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(token.strip() + "\n")
    # chmod 600
    path.chmod(0o600)
    return path


def remove_token(token_file: Path | str | None = None) -> bool:
    """Remove saved API token.

    Args:
        token_file: Path to token file. Defaults to ~/.superme/token.

    Returns:
        True if token was removed, False if it didn't exist.
    """
    path = Path(token_file) if token_file else DEFAULT_TOKEN_FILE
    if path.is_file():
        path.unlink()
        return True
    return False


def resolve_token(
    api_key: str | None = None,
    env_var: str = "SUPERME_API_KEY",
    token_file: Path | str | None = None,
) -> str | None:
    """Resolve API token from multiple sources (priority order):

    1. Explicit api_key argument
    2. Environment variable (SUPERME_API_KEY)
    3. Token file (~/.superme/token)

    Args:
        api_key: Explicitly provided API key.
        env_var: Environment variable name to check.
        token_file: Path to token file.

    Returns:
        Resolved token string or None.
    """
    if api_key:
        return api_key
    env_token = os.environ.get(env_var)
    if env_token:
        return env_token
    return load_token(token_file)
