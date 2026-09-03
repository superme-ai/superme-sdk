import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def _read_json(relative_path: str) -> dict:
    return json.loads((REPO_ROOT / relative_path).read_text())


def test_cursor_plugin_manifest_references_local_assets():
    manifest = _read_json(".cursor-plugin/plugin.json")

    assert manifest["name"] == "superme"
    assert manifest["mcpServers"] == "./mcp.json"
    assert manifest["logo"] == "assets/superme.svg"
    assert (REPO_ROOT / manifest["mcpServers"]).is_file()
    assert (REPO_ROOT / manifest["logo"]).is_file()


def test_cursor_plugin_declares_its_mcp_token_variable():
    manifest = _read_json(".cursor-plugin/plugin.json")
    mcp_config = _read_json("mcp.json")

    token = "SUPERME_TOKEN"
    assert manifest["variables"]["properties"][token]["type"] == "string"
    assert token in manifest["variables"]["required"]
    assert (
        mcp_config["mcpServers"]["superme"]["headers"]["Authorization"]
        == f"Bearer ${{{token}}}"
    )


def test_cursor_plugin_uses_the_hosted_http_mcp_server():
    mcp_config = _read_json("mcp.json")

    server = mcp_config["mcpServers"]["superme"]
    assert server["type"] == "http"
    assert server["url"] == "https://mcp.superme.ai"
