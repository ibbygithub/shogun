# Execution Brief 4 — Conversation Logger Module + Docker Volume

**Agent:** Coding agent on ibbytech-laptop (Windows 11)
**Target:** shogun-core source code + docker-compose.yml
**Dependencies:** None — run first
**Plan ref:** outputs/planning/conversation-logging-plan.md (Approved)

---

## Task

Create the conversation logger module and update Docker configuration for
persistent log storage. This is the foundation — Briefs 5-6 add instrumentation.

---

## File 1: NEW — `app-services/shogun-core/app/services/conversation_logger.py`

Create this file with the following complete implementation:

```python
"""
Conversation audit logger — JSONL file with daily rotation.

Usage:
    from app.services.conversation_logger import init_loggers, new_log, log_field, flush_log

    # At startup (main.py lifespan):
    init_loggers()

    # Per request:
    new_log("conversation")          # or "voice", "photo", "location", "brief"
    log_field("user_message", text)
    log_field("reply_text", reply)
    flush_log()
"""
import contextvars
import json
import logging
import os
import time
from datetime import datetime, timezone
from logging.handlers import TimedRotatingFileHandler

# Per-request accumulator — each async handler gets its own copy
_current_log: contextvars.ContextVar[dict | None] = contextvars.ContextVar(
    "conversation_log", default=None
)
_current_stream: contextvars.ContextVar[str] = contextvars.ContextVar(
    "log_stream", default="conversation"
)

# One logger per stream — initialized at startup
_loggers: dict[str, logging.Logger] = {}

LOG_DIR = os.environ.get("SHOGUN_LOG_DIR", "/var/log/shogun/conversations")

STREAMS = ("conversation", "voice", "photo", "location", "brief")


def init_loggers():
    """Create daily-rotating JSONL loggers for each stream. Call once at startup."""
    os.makedirs(LOG_DIR, exist_ok=True)

    for stream in STREAMS:
        logger = logging.getLogger(f"shogun.audit.{stream}")
        logger.setLevel(logging.INFO)
        logger.propagate = False  # Don't duplicate to root logger / stdout

        # Daily rotation at midnight UTC, keep 30 days
        handler = TimedRotatingFileHandler(
            filename=os.path.join(LOG_DIR, f"{stream}.jsonl"),
            when="midnight",
            interval=1,
            backupCount=30,
            utc=True,
        )
        handler.suffix = "%Y-%m-%d"
        handler.namer = lambda name: name  # Keep default naming

        # Raw JSON — no formatter prefix (no timestamp/level in the line itself)
        handler.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(handler)
        _loggers[stream] = logger

    # Write a startup marker to the conversation log
    _loggers["conversation"].info(
        json.dumps({
            "event": "startup",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "message": "Conversation audit logger initialized",
        })
    )


def new_log(stream: str = "conversation"):
    """Start a new log record for the current request context."""
    _current_log.set({
        "_t0": time.time(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    _current_stream.set(stream)


def log_field(key: str, value):
    """Add a field to the current log record. No-op if no active log."""
    record = _current_log.get(None)
    if record is None:
        return
    record[key] = value


def log_section(section: str, data: dict):
    """Add a nested section (e.g., 'llm_request_1': {...}). No-op if no active log."""
    record = _current_log.get(None)
    if record is None:
        return
    record[section] = data


def flush_log():
    """Write the accumulated log record as a single JSONL line, then clear context."""
    record = _current_log.get(None)
    if record is None:
        return

    stream = _current_stream.get("conversation")
    logger = _loggers.get(stream)
    if not logger:
        return

    try:
        # Compute total elapsed
        t0 = record.pop("_t0", None)
        if t0 is not None:
            record["total_elapsed_ms"] = round((time.time() - t0) * 1000)

        # Serialize — use default=str for anything not natively serializable
        logger.info(json.dumps(record, default=str, ensure_ascii=False))
    except Exception:
        # Logging must never break the conversation
        pass
    finally:
        _current_log.set(None)
```

---

## File 2: MODIFY — `app-services/shogun-core/app/main.py`

### Change 1: Add import (after existing imports, around line 23)

After the line:
```python
from app.services.brief import send_morning_brief
```

Add:
```python
from app.services.conversation_logger import init_loggers, new_log, log_field, log_section, flush_log
```

### Change 2: Initialize loggers in lifespan (after DB check, before scheduler)

After line 41 (`logger.error("DB connection FAILED at startup: %s", exc)`), after the
try/except block for DB (after line 42), add:

```python
    # Initialize conversation audit loggers (JSONL, daily rotation)
    try:
        init_loggers()
        logger.info("Conversation audit loggers initialized → %s",
                     os.environ.get("SHOGUN_LOG_DIR", "/var/log/shogun/conversations"))
    except Exception as exc:
        logger.error("Conversation audit logger init FAILED: %s", exc)
```

Also add `import os` at the top of the file (after `import time`).

### Change 3: Instrument the `/telegram/events` endpoint

Replace the entire `telegram_events` function body (lines 79-138) with:

```python
@app.post("/telegram/events")
async def telegram_events(request: Request):
    """
    Primary inbound endpoint. Receives all Telegram event envelopes from the gateway.
    Returns {"reply_text": "..."} to trigger a bot reply, or {} to stay silent.
    """
    t0 = time.time()
    try:
        raw = await request.json()
    except Exception:
        logger.warning("Received non-JSON body on /telegram/events")
        return JSONResponse(status_code=400, content={"error": "invalid JSON"})

    # Normalise "from" → "from_" (Python reserved word)
    envelope = TelegramEnvelope.model_validate_json_alias(raw)
    telegram_user_id = envelope.from_.user_id
    kind = envelope.kind

    logger.info(
        "receipt=%s kind=%s user=%s chat=%s",
        envelope.receipt_id, kind, telegram_user_id, envelope.chat.id,
    )

    # Start audit log for this request
    stream = {"text": "conversation", "voice": "voice", "photo": "photo",
              "location": "location"}.get(kind, "conversation")
    new_log(stream)
    log_field("receipt_id", envelope.receipt_id)
    log_field("telegram_user_id", telegram_user_id)
    log_field("chat_id", envelope.chat.id)
    log_field("message_kind", kind)

    # Load user and preferences from DB
    user = None
    prefs = []
    if telegram_user_id:
        try:
            user = db.get_user_by_telegram_id(telegram_user_id)
            if user:
                prefs = db.get_user_preferences(user["id"])
                log_field("user_display_name", user.get("display_name"))
        except Exception as exc:
            logger.error("DB lookup failed for user %s: %s", telegram_user_id, exc)

    # Route to the correct handler
    reply_text = None
    try:
        if kind == "text":
            reply_text = await text_handler.handle(envelope, user, prefs)
        elif kind == "location":
            reply_text = await location_handler.handle(envelope, user, prefs)
        elif kind == "photo":
            reply_text = await photo_handler.handle(envelope, user, prefs)
        elif kind == "voice":
            reply_text = await voice_handler.handle(envelope, user, prefs)
        elif kind == "document":
            reply_text = await media_handler.handle_document(envelope, user, prefs)
        else:
            logger.warning("Unknown envelope kind: %s", kind)

    except Exception as exc:
        logger.error("Handler error kind=%s user=%s: %s", kind, telegram_user_id, exc, exc_info=True)
        log_field("error", str(exc))
        reply_text = "Something went wrong on my end. Please try again."

    elapsed = (time.time() - t0) * 1000
    logger.info("receipt=%s handled in %.0fms reply=%s", envelope.receipt_id, elapsed, bool(reply_text))

    # Finalize audit log
    log_field("reply_text", reply_text)
    flush_log()

    if reply_text:
        return {"reply_text": reply_text}
    return {}
```

---

## File 3: MODIFY — `app-services/shogun-core/docker-compose.yml`

Replace the entire file with:

```yaml
networks:
  platform_net:
    external: true
    name: platform_net

services:
  shogun-core:
    build:
      context: .
      dockerfile: Dockerfile
    image: shogun-core
    container_name: shogun-core
    restart: unless-stopped
    env_file: .env
    ports:
      - "0.0.0.0:8082:8082"    # All interfaces — required for svcnode-01 telegram-gateway to reach this
    volumes:
      - /opt/logs/shogun/conversations:/var/log/shogun/conversations
    networks:
      - platform_net
```

---

## Verification

After making all changes, run:

```bash
cd C:\git\work\shogun\app-services\shogun-core
python -c "from app.services.conversation_logger import init_loggers, new_log, log_field, flush_log; print('Import OK')"
```

This validates the module is syntactically correct and importable.

---

## Done Criteria

- [ ] `conversation_logger.py` created with init_loggers, new_log, log_field, log_section, flush_log
- [ ] `main.py` imports and initializes the logger at startup
- [ ] `main.py` telegram_events creates audit log context and flushes at end
- [ ] `docker-compose.yml` has volume mount for `/opt/logs/shogun/conversations`
- [ ] Python import check passes
