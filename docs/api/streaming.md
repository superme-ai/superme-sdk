# Streaming events

Typed shapes for the SSE events yielded by `ask(stream=True)` and
`ask_my_agent(stream=True)`. At runtime each event is a plain `dict` —
discriminate on `["type"]` — but these `TypedDict`s give you autocomplete and
tell you exactly which events arrive and what fields each carries.

::: superme_sdk.streaming
    options:
      show_root_heading: false
      show_root_toc_entry: false
      show_source: false
      members_order: source
