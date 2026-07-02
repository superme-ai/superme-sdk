"""Terminal SSE event-type set for the partner streaming endpoint.

Shared by the sync and async conversation mixins so the two never drift.

``/partner/ask`` converges on the thin partner contract — a final ``done`` or
``error`` chunk (see :data:`~superme_sdk.streaming.PartnerStreamChunk`).
Whichever terminal arrives first stops the generator, so it never hangs past
the end of a turn.
"""

from __future__ import annotations

ASK_TERMINAL = frozenset({"done", "error"})
