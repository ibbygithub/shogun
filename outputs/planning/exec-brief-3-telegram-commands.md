# Execution Brief 3 — Telegram Commands (/bug and /social)

**Agent:** Coding agent on laptop (Windows 11 control plane)
**Target:** shogun-core on brainnode-01
**Estimated time:** 2-2.5 hours
**Dependencies:** Brief 1 (DB schema) must be complete first

---

## Task

Add two new Telegram commands to shogun-core:
1. `/bug <description>` — Report issues, AI-classifies component + severity, stores in `bug_reports`
2. `/social` — Enter capture mode for photos/text with geolocation, stores in `social_notes`

---

## Codebase Patterns to Follow

### Command Registration

Commands are registered in `C:\git\work\shogun\app-services\shogun-core\app\commands\system.py`.

**Sync pattern (used for /bug):**
```python
def handle_command(command: str, user: dict | None) -> str | None:
    cmd = command.strip().lower().split()[0]
    # ... existing commands ...
    if cmd == "/bug":
        if not user:
            return "You're not registered in Shogun. Ask Todd to add you."
        return _cmd_bug(command, user)
    return None
```

**Async pattern (used for /social with AI classification):**
```python
async def handle_async_command(command: str, user: dict | None) -> str | None:
    cmd = command.strip().lower().split()[0]
    # ... existing /brief ...
    if cmd == "/social":
        if not user:
            return "You're not registered in Shogun. Ask Todd to add you."
        return _cmd_social(command, user)
    return None
```

### DB Access Pattern
```python
from app.db import get_connection
import psycopg2

conn = get_connection()  # Returns psycopg2.connect with RealDictCursor
try:
    with conn.cursor() as cur:
        cur.execute("INSERT INTO ... VALUES (%s, %s)", (val1, val2))
    conn.commit()
except psycopg2.Error as exc:
    logger.error("...: %s", exc)
    conn.rollback()
finally:
    conn.close()
```

### Valkey Session Pattern
```python
from app.valkey_client import ...
# Keys use prefix pattern: "shogun:{feature}:{telegram_user_id}"
# TTL: 86400 (24h) for persistent, 300 (5min) for temporary modes
```

### Imports in system.py (existing, line 1-12)
```python
import logging
import psycopg2
from app import db
from app.db import get_connection
from app.valkey_client import clear_context, get_translate_mode, set_translate_mode

logger = logging.getLogger(__name__)
```

---

## Command 1: /bug

### Behavior

User sends: `/bug AI is returning HTML in chat responses`

Bot:
1. Extracts everything after `/bug ` as raw_text
2. AI-classifies the component (core, web-ui, web-api, telegram, data, unknown)
3. Detects severity from keywords ("urgent", "broken", "crash" → urgent)
4. Inserts into `bug_reports`
5. Replies with confirmation + bug ID

### Implementation

**File to modify:** `C:\git\work\shogun\app-services\shogun-core\app\commands\system.py`

Add to `handle_command()` before the final `return None`:

```python
    if cmd == "/bug":
        if not user:
            return "You're not registered in Shogun. Ask Todd to add you."
        args = command.strip().split(maxsplit=1)
        if len(args) < 2 or not args[1].strip():
            return "Usage: /bug <describe the issue>\nExample: /bug AI is returning HTML instead of text"
        return _cmd_bug(args[1].strip(), user)
```

Add the helper function:

```python
def _cmd_bug(description: str, user: dict) -> str:
    """Store a bug report with AI-classified component and severity."""
    # Classify component from description
    desc_lower = description.lower()
    component = "unknown"
    component_keywords = {
        "core": ["ai", "llm", "gemini", "response", "chat", "tool", "search", "location", "brief"],
        "web-ui": ["web", "page", "ui", "button", "display", "calendar", "dashboard", "frontend"],
        "web-api": ["api", "endpoint", "500", "error", "timeout", "backend"],
        "telegram": ["telegram", "bot", "command", "message", "photo", "voice"],
        "data": ["database", "db", "data", "poi", "knowledge", "itinerary", "missing"],
    }
    for comp, keywords in component_keywords.items():
        if any(kw in desc_lower for kw in keywords):
            component = comp
            break

    # Detect severity
    urgent_keywords = ["urgent", "broken", "crash", "down", "critical", "emergency", "blocked"]
    severity = "urgent" if any(kw in desc_lower for kw in urgent_keywords) else "normal"

    # Build AI summary (truncated version of description)
    ai_summary = description[:500]

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO bug_reports
                   (reporter_id, telegram_user_id, raw_text, component, severity, ai_summary, status)
                   VALUES (%s, %s, %s, %s, %s, %s, 'open')
                   RETURNING id""",
                (user["id"], user["telegram_user_id"], description, component, severity, ai_summary),
            )
            bug_id = cur.fetchone()["id"]
        conn.commit()

        sev_icon = "🔴" if severity == "urgent" else "🟡"
        return (
            f"{sev_icon} Bug #{bug_id} reported\n"
            f"Component: {component}\n"
            f"Severity: {severity}\n"
            f"Status: open\n\n"
            f"Thanks {user['display_name']}, I've logged this."
        )
    except psycopg2.Error as exc:
        logger.error("Bug report insert failed: %s", exc)
        conn.rollback()
        return "Failed to record bug report. Please try again."
    finally:
        conn.close()
```

### Update /help text

In the `/help` response string, add:
```
"/bug [description] — report an issue with Shogun\n"
"/social — save photos and notes for your trip journal\n"
```

---

## Command 2: /social

### Behavior

**Flow 1 — Text note with /social:**
- User sends: `/social Amazing ramen at this tiny shop in Asakusa!`
- Bot saves text note, replies with confirmation
- If location was attached to the message, saves coordinates + reverse geocode

**Flow 2 — Photo capture mode:**
- User sends: `/social`  (no text)
- Bot replies: "Send me a photo or text to save to your trip journal. I'll capture it with your location if you share one."
- Bot sets a Valkey flag `shogun:social:{uid}` with 5-min TTL
- Next photo or text message from that user gets captured as a social note
- Location is captured if attached, otherwise stored without

**Flow 3 — Photo with caption:**
- User sends a photo with caption while social mode is active
- Bot saves photo_file_id + caption + location (if present)

### Implementation

**File to modify:** `C:\git\work\shogun\app-services\shogun-core\app\commands\system.py`

Add to `handle_command()`:

```python
    if cmd == "/social":
        if not user:
            return "You're not registered in Shogun. Ask Todd to add you."
        args = command.strip().split(maxsplit=1)
        if len(args) >= 2 and args[1].strip():
            # Inline text note: /social Great ramen spot!
            return _cmd_social_text(args[1].strip(), user)
        else:
            # Enter capture mode
            return _cmd_social_mode(user)
```

Add helper functions:

```python
def _cmd_social_text(text: str, user: dict) -> str:
    """Save a text-only social note."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO social_notes
                   (user_id, telegram_user_id, note_type, text_content, city)
                   VALUES (%s, %s, 'text', %s, %s)
                   RETURNING id""",
                (user["id"], user["telegram_user_id"], text, _get_current_city()),
            )
            note_id = cur.fetchone()["id"]
        conn.commit()
        return f"📝 Note #{note_id} saved! Send a location to tag it, or keep exploring."
    except psycopg2.Error as exc:
        logger.error("Social note insert failed: %s", exc)
        conn.rollback()
        return "Failed to save note. Please try again."
    finally:
        conn.close()


def _cmd_social_mode(user: dict) -> str:
    """Enter social capture mode — next photo/text gets saved."""
    from app.valkey_client import _get_client
    r = _get_client()
    r.setex(f"shogun:social:{user['telegram_user_id']}", 300, "1")  # 5-min TTL
    return (
        "📸 *Social capture mode active* (5 minutes)\n\n"
        "Send me:\n"
        "• A photo (with optional caption)\n"
        "• A text note\n"
        "• A location to tag your last note\n\n"
        "I'll save everything to your trip journal."
    )


def _get_current_city() -> str | None:
    """Get the current city based on today's itinerary date."""
    from datetime import datetime, timezone, timedelta
    _JST = timezone(timedelta(hours=9))
    today_jst = datetime.now(_JST).strftime("%Y-%m-%d")
    return db.get_city_for_date(today_jst)
```

### Social Mode in Text Handler

**File to modify:** `C:\git\work\shogun\app-services\shogun-core\app\handlers\text.py`

After the command check block (around line 30, after `handle_async_command`), add a check for social capture mode:

```python
    # Check for social capture mode (before normal chat processing)
    if _is_social_mode(telegram_user_id):
        return _handle_social_capture(text, telegram_user_id, user)
```

Add these functions to text.py:

```python
def _is_social_mode(telegram_user_id: int) -> bool:
    """Check if user is in social capture mode."""
    from app.valkey_client import _get_client
    r = _get_client()
    return r.exists(f"shogun:social:{telegram_user_id}") > 0


def _handle_social_capture(text: str, telegram_user_id: int, user: dict) -> str:
    """Handle a text message while in social capture mode."""
    from app.db import get_connection
    from app.valkey_client import _get_client
    import psycopg2

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO social_notes
                   (user_id, telegram_user_id, note_type, text_content, city)
                   VALUES (%s, %s, 'text', %s, %s)
                   RETURNING id""",
                (user["id"], telegram_user_id, text, _get_current_city_for_social()),
            )
            note_id = cur.fetchone()["id"]
        conn.commit()

        # Clear social mode
        r = _get_client()
        r.delete(f"shogun:social:{telegram_user_id}")

        return f"📝 Note #{note_id} saved to your trip journal!"
    except psycopg2.Error as exc:
        logger.error("Social capture failed: %s", exc)
        conn.rollback()
        return "Failed to save. Try again with /social"
    finally:
        conn.close()


def _get_current_city_for_social() -> str | None:
    from datetime import datetime, timezone, timedelta
    _JST = timezone(timedelta(hours=9))
    today_jst = datetime.now(_JST).strftime("%Y-%m-%d")
    return db.get_city_for_date(today_jst)
```

### Social Mode in Photo Handler

**File to modify:** `C:\git\work\shogun\app-services\shogun-core\app\handlers\photo.py`

At the beginning of the `handle()` function, before the existing photo analysis logic, add a social mode check:

```python
async def handle(envelope: TelegramEnvelope, user: dict | None, prefs: list[dict]) -> str | None:
    if not user:
        return None

    telegram_user_id = envelope.from_.user_id

    # Check for social capture mode — save photo to journal instead of analyzing
    from app.valkey_client import _get_client
    r = _get_client()
    if r.exists(f"shogun:social:{telegram_user_id}"):
        return _save_social_photo(envelope, user)

    # ... rest of existing photo handler ...
```

Add the social photo handler:

```python
def _save_social_photo(envelope: TelegramEnvelope, user: dict) -> str:
    """Save a photo to the social journal."""
    from app.db import get_connection
    from app.valkey_client import _get_client
    import psycopg2

    photos = envelope.payload.get("photos") or []
    largest = photos[-1] if photos else {}
    file_id = largest.get("file_id") if isinstance(largest, dict) else None
    caption = envelope.payload.get("caption", "").strip()

    # Check for attached location
    loc = envelope.payload.get("location") or {}
    lat = loc.get("latitude")
    lng = loc.get("longitude")

    telegram_user_id = envelope.from_.user_id

    conn = get_connection()
    try:
        note_type = "photo_text" if caption else "photo"
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO social_notes
                   (user_id, telegram_user_id, note_type, text_content,
                    photo_file_id, latitude, longitude, city)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                   RETURNING id""",
                (user["id"], telegram_user_id, note_type,
                 caption or None, file_id, lat, lng,
                 _get_current_city()),
            )
            note_id = cur.fetchone()["id"]
        conn.commit()

        # Clear social mode
        r = _get_client()
        r.delete(f"shogun:social:{telegram_user_id}")

        loc_text = f" (📍 location tagged)" if lat else ""
        caption_text = f"\n📝 \"{caption[:60]}\"" if caption else ""
        return f"📸 Photo #{note_id} saved to your trip journal!{loc_text}{caption_text}"
    except psycopg2.Error as exc:
        logger.error("Social photo save failed: %s", exc)
        conn.rollback()
        return "Failed to save photo. Try /social again."
    finally:
        conn.close()


def _get_current_city():
    from datetime import datetime, timezone, timedelta
    from app import db
    _JST = timezone(timedelta(hours=9))
    today_jst = datetime.now(_JST).strftime("%Y-%m-%d")
    return db.get_city_for_date(today_jst)
```

### Valkey Client Access

The existing `valkey_client.py` creates Redis connections internally. Some functions import `_get_client` from within. Check the existing pattern:

**File:** `C:\git\work\shogun\app-services\shogun-core\app\valkey_client.py`

If `_get_client()` is not exported, you may need to add a simple helper or use the existing redis connection pattern:

```python
import redis
from app.config import settings

def _get_client():
    return redis.Redis(
        host=settings.valkey_host,
        port=settings.valkey_port,
        password=settings.valkey_password,
        decode_responses=True,
    )
```

Check if this function already exists in valkey_client.py. If not, add it. If there's a different pattern (like a module-level `_r` variable), use that instead.

---

## Deployment

After code changes are committed and pushed:

```bash
# SSH to brainnode-01
ssh -i ~/.ssh/devops-agent_ed25519_clean devops-agent@192.168.71.222

# Pull and rebuild
cd /home/devops-agent/git-work/shogun
git pull
cd app-services/compose
docker compose -f docker-compose.shogun.yml build shogun-core
docker compose -f docker-compose.shogun.yml up -d shogun-core
```

---

## Files Modified Summary

| File | Change |
|------|--------|
| `app-services/shogun-core/app/commands/system.py` | Add /bug and /social commands + helpers |
| `app-services/shogun-core/app/handlers/text.py` | Add social capture mode check |
| `app-services/shogun-core/app/handlers/photo.py` | Add social photo capture |
| `app-services/shogun-core/app/valkey_client.py` | Ensure _get_client() is available (may already exist) |

---

## Done Criteria

- [ ] `/bug <description>` stores a bug report with AI-classified component and severity
- [ ] `/bug` with no description returns usage instructions
- [ ] `/social <text>` saves a text note immediately
- [ ] `/social` with no args enters 5-min capture mode via Valkey
- [ ] Photo sent during capture mode saves to social_notes with file_id
- [ ] Photo with caption saves both
- [ ] Location attached to photo/text is saved if present
- [ ] Social mode auto-expires after 5 minutes (Valkey TTL)
- [ ] `/help` shows the new commands
- [ ] Code committed to develop branch
- [ ] Container rebuilt on brainnode-01
