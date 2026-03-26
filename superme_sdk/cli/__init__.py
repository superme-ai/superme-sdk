"""SuperMe CLI package — command-line interface backed by superme_sdk.

Usage:
    superme login [--token TOKEN]
    superme logout
    superme status
    superme ask QUESTION [--username USER] [--conversation-id ID]

Public API
----------
run(argv, token_file)   Parse *argv* and dispatch to the matching command.
main()                  Console-script entry point (calls ``sys.exit(run())``).

Internal layout
---------------
cli/
    utils.py    — token masking and interactive input helpers
    parser.py   — argparse parser construction
    commands.py — one handler per subcommand
    __init__.py — public entry points (this file)
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Sequence

from ..auth import DEFAULT_TOKEN_FILE
from .commands import COMMANDS
from .parser import build_parser

# Re-export for backwards-compat with tests that do:
#   from superme_sdk.cli import _read_token_input
from .utils import read_token_input as _read_token_input  # noqa: F401


def run(argv: Sequence[str] | None = None, token_file: Path | None = None) -> int:
    """Parse *argv* and dispatch to the matching subcommand handler.

    Args:
        argv: Command-line arguments.  Defaults to ``sys.argv[1:]`` when
            ``None``.
        token_file: Override the default token file path.  Useful in tests
            to keep tokens isolated in a temporary directory.

    Returns:
        Shell exit code — ``0`` on success, non-zero on failure.
    """
    token_file = token_file or DEFAULT_TOKEN_FILE
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 1

    handler = COMMANDS.get(args.command)
    if handler is None:
        parser.print_help()
        return 1

    return handler(args, token_file)


def main() -> None:
    """Entry point for the ``superme`` console script (see pyproject.toml)."""
    sys.exit(run())
