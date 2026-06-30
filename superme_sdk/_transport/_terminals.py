"""Terminal SSE event-type sets for the partner streaming endpoints.

Shared by the sync and async conversation mixins so the two never drift.
Values mirror the backend ``Literal``s: ``/partner/ask`` emits a final
``done``/``error`` chunk; ``/partner/agent`` ends on a turn lifecycle event.
"""

from __future__ import annotations

ASK_TERMINAL = frozenset({"done", "error"})
AGENT_TERMINAL = frozenset({"turn_completed", "turn_failed", "turn_interrupted"})
