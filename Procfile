# --workers 1 is REQUIRED, not a default. The LangGraph checkpointer is MemorySaver
# (in-process), and the briefing job map and rate-limit counters are plain dicts. With
# more than one worker, a session started on worker A cannot be confirmed on worker B,
# and rate limits become per-worker. Moving to multiple workers means moving the
# checkpointer to Postgres/Redis first.
web: uvicorn backend.server:app --host 0.0.0.0 --port $PORT --workers 1
