"""Terminal SSE event-type sets for the partner streaming endpoints.

Shared by the sync and async conversation mixins so the two never drift.

Both endpoints converge on the thin partner contract — a final ``done`` or
``error`` chunk (see :data:`~superme_sdk.streaming.PartnerStreamChunk`).
``/partner/agent`` historically ended instead on a turn-lifecycle event
(``turn_completed``/``turn_failed``/``turn_interrupted``); backend PR #5643
collapses it to the thin ``done``/``error`` shape. We keep the legacy names in
the agent set so the stream still terminates against a backend that hasn't
deployed #5643 yet — whichever terminal arrives first stops the generator, so
it never hangs past the end of a turn. The public type catalog only documents
the thin ``done``/``error`` terminals.
"""

from __future__ import annotations

ASK_TERMINAL = frozenset({"done", "error"})
# Thin terminals (post-#5643) plus the legacy turn-lifecycle events, so the
# agent stream terminates correctly whether or not #5643 has shipped.
AGENT_TERMINAL = ASK_TERMINAL | frozenset(
    {"turn_completed", "turn_failed", "turn_interrupted"}
)
