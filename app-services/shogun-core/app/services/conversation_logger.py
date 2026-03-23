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
