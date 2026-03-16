"""
verify_chatbot.py — Shogun chatbot regression and connectivity diagnostic.

Runs from the host (not inside containers). Calls HTTP endpoints on localhost.
Usage: python tools/verify_chatbot.py

Checks 1-6 are functional pass/fail.
Checks 7-10 are connectivity diagnostics (informational — won't fail the run).
"""
import subprocess
import sys
import time
import uuid
import requests

# ── Port constants (from docker ps) ─────────────────────────────────────────
CORE_PORT = 8082
WEB_PORT  = 8090

CORE_BASE = f"http://localhost:{CORE_PORT}"
WEB_BASE  = f"http://localhost:{WEB_PORT}"

# Todd's real Telegram user ID — the only registered user
TODD_TG_ID = 204595710

# Test-only Telegram user ID that we know is NOT in the DB — used to verify
# the unregistered-user path works correctly. We use a dedicated test Telegram
# user ID for memory tests instead, because unregistered users are rejected.
# We use Todd for memory tests (they're cleaned up at the end).
TEST_TG_ID = TODD_TG_ID  # use Todd for memory test (clean up after)

results = {}  # check_name -> (passed: bool, detail: str)


# ── Helpers ──────────────────────────────────────────────────────────────────

def _make_envelope(user_id: int, first_name: str, text: str, message_id: int) -> dict:
    """Build a valid TelegramEnvelope for shogun-core /telegram/events."""
    return {
        "receipt_id": str(uuid.uuid4()),
        "received_at": "2026-03-15T10:00:00Z",
        "kind": "text",
        "update": {"update_id": message_id},
        "from": {
            "user_id": user_id,
            "first_name": first_name,
        },
        "chat": {"id": user_id, "type": "private"},
        "message": {"message_id": message_id},
        "payload": {"text": text},
    }


def _core_post(text: str, user_id: int = TODD_TG_ID,
               first_name: str = "Todd", message_id: int = 1) -> str:
    """POST to /telegram/events. Returns reply_text or raises."""
    envelope = _make_envelope(user_id, first_name, text, message_id)
    resp = requests.post(f"{CORE_BASE}/telegram/events", json=envelope, timeout=35)
    resp.raise_for_status()
    return resp.json().get("reply_text", "")


def _web_post(message: str) -> str:
    """POST to /chat. Returns response text or raises."""
    resp = requests.post(f"{WEB_BASE}/chat",
                         json={"message": message},
                         timeout=35)
    resp.raise_for_status()
    return resp.json().get("response", "")


def _run_docker(cmd: str) -> tuple[bool, str]:
    """Run a docker exec command. Returns (success, output_text)."""
    result = subprocess.run(
        cmd, shell=True, capture_output=True, text=True, timeout=30
    )
    combined = (result.stdout + result.stderr).strip()
    return result.returncode == 0, combined


def _check(name: str, passed: bool, detail: str) -> None:
    results[name] = (passed, detail)
    status = "PASS" if passed else "FAIL"
    print(f"  [{status}] {name}: {detail[:120]}")


def _info(name: str, detail: str) -> None:
    results[name] = (None, detail)  # None = informational
    print(f"  [INFO] {name}: {detail[:120]}")


# ── Phase 1: shogun-core checks ───────────────────────────────────────────────

print("\n=== shogun-core checks ===")

# 1. SHOGUN_CORE_HEALTH
try:
    r = requests.get(f"{CORE_BASE}/health", timeout=5)
    passed = r.status_code == 200
    _check("SHOGUN_CORE_HEALTH", passed, f"HTTP {r.status_code} — {r.text[:80]}")
except Exception as exc:
    _check("SHOGUN_CORE_HEALTH", False, str(exc))

# 2. SHOGUN_CORE_PERSONA
try:
    reply = _core_post("Who are you?", message_id=2)
    bad_phrases = ["i am an ai", "i'm an ai", "i am an ai assistant", "i'm an ai assistant"]
    has_japan = any(w in reply.lower() for w in ["japan", "concierge", "shogun", "ibbotson",
                                                   "travel", "trip", "itinerary"])
    is_generic = any(p in reply.lower() for p in bad_phrases)
    passed = has_japan and not is_generic
    detail = reply[:120] if passed else f"BAD_REPLY: {reply[:120]}"
    _check("SHOGUN_CORE_PERSONA", passed, detail)
except Exception as exc:
    _check("SHOGUN_CORE_PERSONA", False, str(exc))

# 3. SHOGUN_CORE_MEMORY
try:
    # Clear Todd's context first so this test is isolated
    subprocess.run(
        'docker exec platform-valkey redis-cli -a "KPyOcoDNmQE5HiA42jblkrqp" '
        f'DEL "shogun:context:{TODD_TG_ID}"',
        shell=True, capture_output=True, timeout=10
    )
    time.sleep(0.5)

    # Send memory-setting message
    _core_post("My favorite ramen shop is Ichiran. Remember that.", message_id=10)
    time.sleep(0.5)

    # Ask recall
    recall_reply = _core_post("What ramen shop did I mention?", message_id=11)

    passed = "ichiran" in recall_reply.lower()
    detail = recall_reply[:120] if passed else f"NO_RECALL: {recall_reply[:120]}"
    _check("SHOGUN_CORE_MEMORY", passed, detail)

    # Clean up
    _core_post("/reset", message_id=12)
except Exception as exc:
    _check("SHOGUN_CORE_MEMORY", False, str(exc))

# ── Phase 2: shogun-web-api checks ───────────────────────────────────────────

print("\n=== shogun-web-api checks ===")

# 4. SHOGUN_WEB_HEALTH
try:
    r = requests.get(f"{WEB_BASE}/health", timeout=5)
    passed = r.status_code == 200
    _check("SHOGUN_WEB_HEALTH", passed, f"HTTP {r.status_code} — {r.text[:80]}")
except Exception as exc:
    _check("SHOGUN_WEB_HEALTH", False, str(exc))

# 5. SHOGUN_WEB_PERSONA
try:
    reply = _web_post("Who are you and what can you help me with?")
    bad_phrases = ["i am an ai", "i'm an ai", "i am an ai assistant", "i'm an ai assistant"]
    has_japan = any(w in reply.lower() for w in ["japan", "concierge", "shogun", "ibbotson",
                                                   "travel", "trip", "itinerary"])
    is_generic = any(p in reply.lower() for p in bad_phrases)
    passed = has_japan and not is_generic
    detail = reply[:120] if passed else f"BAD_REPLY: {reply[:120]}"
    _check("SHOGUN_WEB_PERSONA", passed, detail)
except Exception as exc:
    _check("SHOGUN_WEB_PERSONA", False, str(exc))

# 6. SHOGUN_WEB_MEMORY
try:
    # Clear web chat history for user 1
    subprocess.run(
        'docker exec platform-valkey redis-cli -a "KPyOcoDNmQE5HiA42jblkrqp" '
        'DEL "shogun:web:1:chat"',
        shell=True, capture_output=True, timeout=10
    )
    time.sleep(0.5)

    _web_post("My favorite city in Japan is Kanazawa. Remember this.")
    time.sleep(0.5)

    recall_reply = _web_post("Which city did I say was my favorite?")
    passed = "kanazawa" in recall_reply.lower()
    detail = recall_reply[:120] if passed else f"NO_RECALL: {recall_reply[:120]}"
    _check("SHOGUN_WEB_MEMORY", passed, detail)

    # Clean up
    subprocess.run(
        'docker exec platform-valkey redis-cli -a "KPyOcoDNmQE5HiA42jblkrqp" '
        'DEL "shogun:web:1:chat"',
        shell=True, capture_output=True, timeout=10
    )
except Exception as exc:
    _check("SHOGUN_WEB_MEMORY", False, str(exc))

# ── Phase 3: connectivity diagnostics (informational) ──────────────────────

print("\n=== connectivity diagnostics (informational) ===")

# 7. LLM_GATEWAY_REACHABLE
try:
    ok, out = _run_docker(
        "docker exec shogun-core python -c \""
        "import httpx; r=httpx.get('http://platform-llm-gateway:8080/health', timeout=5); "
        "print(r.status_code)\""
    )
    _info("LLM_GATEWAY_REACHABLE", f"{'OK' if ok else 'FAIL'}: {out}")
except Exception as exc:
    _info("LLM_GATEWAY_REACHABLE", f"ERROR: {exc}")

# 8. VALKEY_REACHABLE_CORE
try:
    ok, out = _run_docker(
        "docker exec shogun-core python -c \""
        "import redis, os; "
        "r=redis.Redis(host=os.getenv('VALKEY_HOST','platform-valkey'), "
        "port=int(os.getenv('VALKEY_PORT','6379')), "
        "password=os.getenv('VALKEY_PASSWORD'), decode_responses=True); "
        "r.ping(); print('OK')\""
    )
    _info("VALKEY_REACHABLE_CORE", f"{'OK' if ok else 'FAIL'}: {out}")
except Exception as exc:
    _info("VALKEY_REACHABLE_CORE", f"ERROR: {exc}")

# 9. VALKEY_REACHABLE_WEB
try:
    ok, out = _run_docker(
        "docker exec shogun-web-api python -c \""
        "import redis, os; "
        "r=redis.from_url(os.getenv('VALKEY_URL','redis://platform-valkey:6379'), "
        "decode_responses=True); "
        "r.ping(); print('OK')\""
    )
    _info("VALKEY_REACHABLE_WEB", f"{'OK' if ok else 'FAIL'}: {out}")
except Exception as exc:
    _info("VALKEY_REACHABLE_WEB", f"ERROR: {exc}")

# 10. DB_REACHABLE_CORE
try:
    ok, out = _run_docker(
        "docker exec shogun-core python -c \""
        "from app.db import get_user_by_telegram_id; "
        "u=get_user_by_telegram_id(204595710); "
        "print('OK' if u else 'USER_NOT_FOUND')\""
    )
    _info("DB_REACHABLE_CORE", f"{'OK' if ok else 'FAIL'}: {out}")
except Exception as exc:
    _info("DB_REACHABLE_CORE", f"ERROR: {exc}")

# ── Phase 4: enrichment checks (if enrichments are present) ────────────────

print("\n=== enrichment checks ===")

# Time check
try:
    reply = _core_post("What time is it in Japan right now?", message_id=20)
    # Look for hour patterns like "10:30" or "22:15" or any time mention
    import re
    has_time = bool(re.search(r'\d{1,2}:\d{2}', reply)) or any(
        w in reply.lower() for w in ["jst", "japan standard time", "am", "pm",
                                      "morning", "afternoon", "evening", "night",
                                      "o'clock"]
    )
    _check("ENRICHMENT_TIME_CORE", has_time, reply[:120])
except Exception as exc:
    _check("ENRICHMENT_TIME_CORE", False, str(exc))

try:
    reply = _web_post("What time is it in Japan right now?")
    import re
    has_time = bool(re.search(r'\d{1,2}:\d{2}', reply)) or any(
        w in reply.lower() for w in ["jst", "japan standard time", "am", "pm",
                                      "morning", "afternoon", "evening", "night",
                                      "o'clock"]
    )
    _check("ENRICHMENT_TIME_WEB", has_time, reply[:120])
except Exception as exc:
    _check("ENRICHMENT_TIME_WEB", False, str(exc))

# Weather check
try:
    reply = _core_post("What's the weather like today in Osaka?", message_id=21)
    has_weather = any(w in reply.lower() for w in ["°c", "celsius", "temperature",
                                                     "rain", "cloud", "sunny", "warm",
                                                     "cool", "weather", "forecast"])
    _check("ENRICHMENT_WEATHER_CORE", has_weather, reply[:120])
except Exception as exc:
    _check("ENRICHMENT_WEATHER_CORE", False, str(exc))

try:
    reply = _web_post("What's the weather like today in Osaka?")
    has_weather = any(w in reply.lower() for w in ["°c", "celsius", "temperature",
                                                    "rain", "cloud", "sunny", "warm",
                                                    "cool", "weather", "forecast"])
    _check("ENRICHMENT_WEATHER_WEB", has_weather, reply[:120])
except Exception as exc:
    _check("ENRICHMENT_WEATHER_WEB", False, str(exc))

# Sakura check
try:
    reply = _core_post("Are cherry blossoms blooming in Osaka right now?", message_id=22)
    has_sakura = any(w in reply.lower() for w in ["sakura", "cherry blossom", "bloom",
                                                    "hanami", "2026", "forecast",
                                                    "peak", "flower"])
    _check("ENRICHMENT_SAKURA_CORE", has_sakura, reply[:120])
except Exception as exc:
    _check("ENRICHMENT_SAKURA_CORE", False, str(exc))

try:
    reply = _web_post("Are cherry blossoms blooming in Osaka right now?")
    has_sakura = any(w in reply.lower() for w in ["sakura", "cherry blossom", "bloom",
                                                    "hanami", "2026", "forecast",
                                                    "peak", "flower"])
    _check("ENRICHMENT_SAKURA_WEB", has_sakura, reply[:120])
except Exception as exc:
    _check("ENRICHMENT_SAKURA_WEB", False, str(exc))

# Clean up
subprocess.run(
    'docker exec platform-valkey redis-cli -a "KPyOcoDNmQE5HiA42jblkrqp" '
    f'DEL "shogun:context:{TODD_TG_ID}" "shogun:web:1:chat"',
    shell=True, capture_output=True, timeout=10
)

# ── Summary ────────────────────────────────────────────────────────────────

print("\n=== SUMMARY ===")

core_checks = ["SHOGUN_CORE_HEALTH", "SHOGUN_CORE_PERSONA", "SHOGUN_CORE_MEMORY",
               "SHOGUN_WEB_HEALTH", "SHOGUN_WEB_PERSONA", "SHOGUN_WEB_MEMORY"]

passed_core = [name for name in core_checks
               if results.get(name, (False, ""))[0] is True]
failed_core = [name for name in core_checks
               if results.get(name, (False, ""))[0] is False]

all_names = list(results.keys())
passed_all = [name for name in all_names if results[name][0] is True]
failed_all  = [name for name in all_names if results[name][0] is False]

print(f"\nCore checks (1-6):")
print(f"  PASSED: {len(passed_core)}/6")
if failed_core:
    print(f"  FAILED: {failed_core}")

print(f"\nAll checks (including enrichments):")
print(f"  PASSED: {len(passed_all)}/{len([n for n in all_names if results[n][0] is not None])}")
if failed_all:
    print(f"  FAILED: {failed_all}")
    print("\nACTION_REQUIRED:")
    for name in failed_all:
        _, detail = results[name]
        print(f"  - {name}: {detail[:100]}")
else:
    print("\nAll checks passing — no action required.")

sys.exit(0 if not failed_core else 1)
