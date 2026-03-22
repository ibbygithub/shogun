# Execution Brief 6 — Voice, Photo, Location, Brief Handler Instrumentation

**Agent:** Coding agent on ibbytech-laptop (Windows 11)
**Target:** shogun-core source code
**Dependencies:** Exec Brief 4 must be complete (conversation_logger.py exists)
**Plan ref:** outputs/planning/conversation-logging-plan.md (Approved)

---

## Task

Instrument the non-text handlers (voice, photo, location, brief) so each
produces a JSONL audit record in its respective log stream.

Note: main.py already selects the correct stream based on `kind` (done in Brief 4).
These handlers just need to emit fields into the active log context.

---

## File 1: MODIFY — `app-services/shogun-core/app/handlers/voice.py`

### Change 1: Add import

After line 11 (`from app.config import settings`), add:

```python
from app.services.conversation_logger import log_field, log_section
```

### Change 2: Log transcription and LLM exchange

After line 59 (`logger.info("Voice transcribed for %s: %r", user["display_name"], transcription[:80])`), add:

```python
    log_field("user_display_name", user["display_name"])
    log_field("transcription", transcription)
    log_field("mime_type", mime_type)
    log_field("translate_mode", bool(translate))
```

After line 76 (`reply = await chat(history, system_prompt)`), add:

```python
    log_field("system_prompt", system_prompt)
    log_field("reply_text", reply)
```

---

## File 2: MODIFY — `app-services/shogun-core/app/handlers/photo.py`

### Change 1: Add import

After line 14 (`from app.config import settings`), add:

```python
from app.services.conversation_logger import log_field, log_section
```

### Change 2: Log photo analysis

After line 89 (`logger.info("Photo analyzed for %s", user["display_name"])`), add:

```python
    log_field("user_display_name", user["display_name"])
    log_field("caption", caption)
    log_field("prompt", prompt)
    log_field("analysis", analysis)
    log_field("system_prompt", build_system_prompt(user, prefs))
```

---

## File 3: MODIFY — `app-services/shogun-core/app/handlers/location.py`

### Change 1: Add import

After line 12 (`from app.valkey_client import get_context, save_context, get_location, save_location`), add:

```python
from app.services.conversation_logger import log_field, log_section
```

### Change 2: Log location data and trigger decision

After line 73 (`logger.info("Location delta for %s: %.0fm moved, %ds elapsed...")`), add:

```python
    log_field("user_display_name", user["display_name"])
    log_field("lat", lat)
    log_field("lng", lng)
    log_field("is_live", is_live)
    log_section("location_delta", {
        "distance_m": round(distance),
        "elapsed_s": elapsed,
        "trigger_threshold_m": TRIGGER_METERS,
        "cooldown_s": COOLDOWN_SECONDS,
        "triggered": distance >= TRIGGER_METERS and elapsed >= COOLDOWN_SECONDS,
    })
```

After line 85 (`reply = await location_triggered_places(lat, lng, system_prompt, history)`), add:

```python
    log_field("reply_text", reply)
```

---

## File 4: MODIFY — `app-services/shogun-core/app/services/brief.py`

### Change 1: Add import

After line 11 (`from app.services.sender import send_message`), add:

```python
from app.services.conversation_logger import new_log, log_field, flush_log
```

### Change 2: Log brief content and delivery

In `send_morning_brief()`, after line 51 (`brief_text = await _build_brief(today_jst)`), add:

```python
    # Audit: log the generated brief content
    new_log("brief")
    log_field("date", str(today_jst))
    log_field("brief_text", brief_text)
    log_field("recipient_count", len(users))
```

After the `for` loop that sends to each user (after line 57), add:

```python
    flush_log()
```

Note: The brief handler runs from the scheduler, not from a Telegram event,
so it needs its own `new_log()` / `flush_log()` lifecycle (unlike the other
handlers which inherit from main.py's telegram_events).

---

## Verification

After making all changes, run:

```bash
cd C:\git\work\shogun\app-services\shogun-core
python -c "
from app.handlers.voice import handle
from app.handlers.photo import handle
from app.handlers.location import handle
from app.services.brief import send_morning_brief
print('All imports OK')
"
```

---

## Done Criteria

- [ ] voice.py logs transcription, mime_type, system_prompt, reply
- [ ] photo.py logs caption, analysis prompt, analysis result, system_prompt
- [ ] location.py logs GPS, distance delta, trigger decision, reply
- [ ] brief.py logs generated brief content, recipient count, with own log lifecycle
- [ ] Python import check passes
- [ ] No changes to function signatures or return types
