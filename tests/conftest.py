"""conftest.py — session-scoped fixtures for superme-sdk tests.

Strategy
--------
- Load SUPERME_API_KEY (and optional overrides) from .env at the package root.
- Probe the backend once per session with a lightweight tools/list call.
- Provide a `live_client` fixture that is a real SuperMeClient when the
  backend is reachable, or auto-skips the test otherwise.
- Existing mock tests are unaffected — they never request `live_client`.
"""

import os
from pathlib import Path
from typing import Optional

import httpx
import pytest

# ---------------------------------------------------------------------------
# Load .env from package root (parent of tests/) without requiring dotenv
# ---------------------------------------------------------------------------

_env_file = Path(__file__).parent.parent / ".env"
if _env_file.exists():
    for _line in _env_file.read_text().splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _, _v = _line.partition("=")
            os.environ.setdefault(_k.strip(), _v.strip())


# ---------------------------------------------------------------------------
# Backend probe
# ---------------------------------------------------------------------------


def _probe_backend(api_key: str, base_url: str) -> bool:
    """Return True if the backend is reachable and accepts the key."""
    try:
        resp = httpx.post(
            f"{base_url}/",
            json={"jsonrpc": "2.0", "id": 0, "method": "tools/list", "params": {}},
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            timeout=5.0,
        )
        # Any non-5xx response means the server is up
        return resp.status_code < 500
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Pytest markers
# ---------------------------------------------------------------------------


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "live: marks tests that require a live backend (auto-skipped when offline)",
    )


# ---------------------------------------------------------------------------
# Session-scoped fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def backend_url() -> str:
    return os.getenv("SUPERME_BASE_URL", "https://mcp.superme.ai")


@pytest.fixture(scope="session")
def live_api_key() -> Optional[str]:
    return os.getenv("SUPERME_API_KEY") or None


@pytest.fixture(scope="session")
def backend_alive(live_api_key, backend_url) -> bool:
    """True when SUPERME_API_KEY is set and the backend responds."""
    if not live_api_key:
        return False
    alive = _probe_backend(live_api_key, backend_url)
    status = "LIVE" if alive else "OFFLINE"
    print(f"\n[conftest] Backend probe → {status} ({backend_url})")
    return alive


@pytest.fixture(scope="session")
def live_client(live_api_key, backend_url, backend_alive):
    """Real SuperMeClient — skips automatically when backend is not reachable."""
    if not backend_alive:
        pytest.skip(
            "Backend not reachable or SUPERME_API_KEY not set — skipping live tests"
        )
    from superme_sdk.client import SuperMeClient

    client = SuperMeClient(api_key=live_api_key, base_url=backend_url)
    yield client
    client.close()


@pytest.fixture(scope="session")
def live_username() -> str:
    """SuperMe username to use in live tests (override with SUPERME_TEST_USERNAME)."""
    return os.getenv("SUPERME_TEST_USERNAME", "ludo")


@pytest.fixture(scope="session")
def async_live_client(live_api_key, backend_url, backend_alive):
    """Real AsyncSuperMeClient — skips automatically when backend is not reachable.

    Sync fixture so teardown uses a fresh event loop via ``asyncio.run()`` —
    avoids "Event loop is closed" errors that occur when session-scoped async
    fixtures outlive the test event loop.
    """
    import asyncio

    if not backend_alive:
        pytest.skip(
            "Backend not reachable or SUPERME_API_KEY not set — skipping live tests"
        )
    from superme_sdk.client import AsyncSuperMeClient

    client = AsyncSuperMeClient(api_key=live_api_key, base_url=backend_url)
    yield client
    asyncio.run(client.aclose())


# ---------------------------------------------------------------------------
# SSE test helpers
# ---------------------------------------------------------------------------


def make_sse_body(*json_objects) -> bytes:
    """Encode dicts as ``data: <json>\\n\\n`` SSE lines."""
    import json as _json

    lines = []
    for obj in json_objects:
        lines.append(f"data: {_json.dumps(obj)}\n\n")
    return "".join(lines).encode()
