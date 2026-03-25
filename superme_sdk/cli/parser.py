"""Argparse parser definition for the SuperMe CLI."""

from __future__ import annotations

import argparse

from .. import __version__


def build_parser() -> argparse.ArgumentParser:
    """Build and return the top-level argument parser."""
    parser = argparse.ArgumentParser(
        prog="superme",
        description="SuperMe CLI - interact with SuperMe AI from the terminal",
    )
    parser.add_argument(
        "--version", action="version", version=f"superme {__version__}"
    )

    sub = parser.add_subparsers(dest="command", metavar="<command>")

    # --- Auth ---
    lp = sub.add_parser("login", help="Save API token")
    lp.add_argument("--token", type=str, default=None, help="API token (prompted if omitted)")
    sub.add_parser("logout", help="Remove saved API token")
    sub.add_parser("status", help="Show authentication status")

    # --- Conversations ---
    ap = sub.add_parser("ask", help="Ask a one-off question about a user")
    ap.add_argument("question", type=str, help="Question to ask")
    ap.add_argument("--username", type=str, default="ludo", help="Target username (default: ludo)")
    ap.add_argument("--conversation-id", type=str, default=None, help="Continue a conversation")

    chp = sub.add_parser("chat", help="Send a chat message (supports conversation history)")
    chp.add_argument("message", type=str, help="Message to send")
    chp.add_argument("--username", type=str, default="ludo", help="Target username (default: ludo)")
    chp.add_argument("--conversation-id", type=str, default=None, help="Continue a conversation")
    chp.add_argument("--history", type=str, default=None, help='Prior messages as JSON array, e.g. \'[{"role":"user","content":"hi"}]\'')  # noqa: E501

    cp = sub.add_parser("interactive-chat", help="Interactive multi-turn conversation (REPL)")
    cp.add_argument("--username", type=str, default="ludo", help="Target username (default: ludo)")

    aap = sub.add_parser("ask-agent", help="Ask your own SuperMe AI agent")
    aap.add_argument("question", type=str, help="Message to your agent")
    aap.add_argument("--conversation-id", type=str, default=None, help="Continue a conversation")

    clp = sub.add_parser("conversations", help="List recent conversations")
    clp.add_argument("--limit", type=int, default=20, help="Max conversations (default: 20)")

    cgp = sub.add_parser("conversation", help="Get a conversation with all messages")
    cgp.add_argument("conversation_id", type=str, help="Conversation ID")

    # --- Users ---
    pp = sub.add_parser("profile", help="Get a user profile")
    pp.add_argument("identifier", nargs="?", default=None, help="Username, ID, or name (omit for self)")

    fup = sub.add_parser("find-user", help="Search users by name")
    fup.add_argument("name", type=str, help="Full or partial name")
    fup.add_argument("--limit", type=int, default=10, help="Max results (default: 10)")

    # --- Search ---
    sp = sub.add_parser("search", help="Search expert perspectives on a topic")
    sp.add_argument("question", type=str, help="Topic or question")

    # --- Content ---
    acp = sub.add_parser("add-content", help="Add notes to your library")
    acp.add_argument("notes", nargs="+", help="Text blocks to save")
    acp.add_argument("--extended-content", type=str, default=None, help="Longer-form content")
    acp.add_argument("--instructions", type=str, default=None, help="AI usage instructions")

    aup = sub.add_parser("add-urls", help="Add URLs to your knowledge base")
    aup.add_argument("urls", nargs="+", help="URLs to crawl and index")

    cup = sub.add_parser("check-urls", help="Check which URLs are not yet indexed")
    cup.add_argument("urls", nargs="+", help="URLs to check")

    # --- Low-level MCP ---
    sub.add_parser("mcp-tools", help="List all available MCP tools")

    mcp = sub.add_parser("mcp-call", help="Call an MCP tool by name (advanced)")
    mcp.add_argument("tool_name", type=str, help="MCP tool name")
    mcp.add_argument("--args", type=str, default=None, help='Tool arguments as JSON')

    return parser
