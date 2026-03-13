#!/usr/bin/env python3
"""
validate_shogun.py — Phase 3 validation for shogun-core.

Checks:
  1. Process / systemd service running
  2. GET /health endpoint
  3. DB connection (users table accessible)
  4. Valkey connection (set/get/del)
  5. LLM gateway reachable from brainnode-01
  6. POST /telegram/events — text envelope round-trip

Usage (on brainnode-01):
  cd /opt/git/work/shogun/app-services/shogun-core
  source venv/bin/activate
  python tools/validate_shogun.py
"""
import json
import os
import subprocess
import sys
import time

try:
    import requests
except ImportError:
    print("[FATAL] requests not installed — run: pip install requests")
    sys.exit(1)

BASE_URL = os.environ.get("SHOGUN_URL", "http://127.0.0.1:8082")
_results = {}
_start = time.time()


def _ok(msg):  print(f"  [PASS] {msg}")
def _fail(msg): print(f"  [FAIL] {msg}")
def _info(msg): print(f"  [INFO] {msg}")
def _hdr(t):
    print()
    print("=" * 72)
    print(f"  {t}")
    print("=" * 72)


def step1_process():
    _hdr("Step 1 — systemd service status")
    result = subprocess.run(
        ["systemctl", "is-active", "shogun-core"],
        capture_output=True, text=True,
    )
    status = result.stdout.strip()
    if status == "active":
        _ok("shogun-core.service is active")
        _results["step1"] = {"pass": True}
    else:
        _fail(f"shogun-core.service status: {status}")
        _info("Start with: sudo systemctl start shogun-core")
        _results["step1"] = {"pass": False, "status": status}


def step2_health():
    _hdr("Step 2 — GET /health")
    try:
        t0 = time.time()
        r = requests.get(f"{BASE_URL}/health", timeout=5)
        ms = (time.time() - t0) * 1000
        r.raise_for_status()
        data = r.json()
        if data.get("ok"):
            _ok(f"Health OK — version={data.get('version')} ({ms:.0f}ms)")
            _results["step2"] = {"pass": True}
        else:
            _fail(f"Health returned ok=false: {data}")
            _results["step2"] = {"pass": False}
    except Exception as exc:
        _fail(f"GET /health failed: {exc}")
        _results["step2"] = {"pass": False, "error": str(exc)}


def step3_db():
    _hdr("Step 3 — Database connection (users table)")
    try:
        import psycopg2
        from dotenv import load_dotenv
        load_dotenv()
        conn = psycopg2.connect(
            host=os.environ["DB_HOST"], port=int(os.environ.get("DB_PORT", 5432)),
            dbname=os.environ["DB_NAME"], user=os.environ["DB_USER"],
            password=os.environ["DB_PASSWORD"], connect_timeout=5,
        )
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM users")
            count = cur.fetchone()[0]
        conn.close()
        _ok(f"DB connected — users table has {count} row(s)")
        _results["step3"] = {"pass": True, "user_count": count}
    except Exception as exc:
        _fail(f"DB connection failed: {exc}")
        _results["step3"] = {"pass": False, "error": str(exc)}


def step4_valkey():
    _hdr("Step 4 — Valkey connection")
    try:
        import redis
        from dotenv import load_dotenv
        load_dotenv()
        r = redis.Redis(
            host=os.environ["VALKEY_HOST"],
            port=int(os.environ.get("VALKEY_PORT", 6379)),
            password=os.environ["VALKEY_PASSWORD"],
            decode_responses=True, socket_connect_timeout=3,
        )
        r.set("shogun:validate:probe", "ok", ex=30)
        val = r.get("shogun:validate:probe")
        r.delete("shogun:validate:probe")
        if val == "ok":
            _ok("Valkey SET/GET/DEL working")
            _results["step4"] = {"pass": True}
        else:
            _fail(f"Valkey GET returned unexpected value: {val}")
            _results["step4"] = {"pass": False}
    except Exception as exc:
        _fail(f"Valkey connection failed: {exc}")
        _results["step4"] = {"pass": False, "error": str(exc)}


def step5_llm_gateway():
    _hdr("Step 5 — LLM Gateway reachability")
    from dotenv import load_dotenv
    load_dotenv()
    llm_url = os.environ.get("LLM_GATEWAY_URL", "https://llm.platform.ibbytech.com")
    try:
        t0 = time.time()
        r = requests.get(f"{llm_url}/health", timeout=10)
        ms = (time.time() - t0) * 1000
        r.raise_for_status()
        data = r.json()
        _ok(f"LLM gateway reachable ({ms:.0f}ms) — providers: {list(data.get('providers', {}).keys())}")
        _results["step5"] = {"pass": True}
    except Exception as exc:
        _fail(f"LLM gateway unreachable: {exc}")
        _results["step5"] = {"pass": False, "error": str(exc)}


def step6_telegram_events():
    _hdr("Step 6 — POST /telegram/events (text envelope round-trip)")
    # Send a test envelope as Todd (telegram_user_id=204595710)
    envelope = {
        "receipt_id": "validate-001",
        "received_at": "2026-03-13T00:00:00.000Z",
        "kind": "text",
        "update": {"update_id": 1},
        "from": {"user_id": 204595710, "username": "todd_test", "first_name": "Todd"},
        "chat": {"id": 204595710, "type": "private"},
        "message": {"message_id": 1, "date": 1741824000},
        "capabilities": {"can_search": True, "can_scrape": True, "can_fetch_files": False},
        "payload": {"text": "Shogun validation test — say hello in one sentence.", "entities": []},
    }
    try:
        t0 = time.time()
        r = requests.post(f"{BASE_URL}/telegram/events", json=envelope, timeout=30)
        ms = (time.time() - t0) * 1000
        r.raise_for_status()
        data = r.json()
        reply = data.get("reply_text", "")
        if reply:
            _ok(f"Got reply in {ms:.0f}ms: {reply[:80]!r}")
            _results["step6"] = {"pass": True, "reply_preview": reply[:80]}
        else:
            _fail("No reply_text in response — check LLM gateway and user seed")
            _info(f"Response: {data}")
            _results["step6"] = {"pass": False}
    except Exception as exc:
        _fail(f"POST /telegram/events failed: {exc}")
        _results["step6"] = {"pass": False, "error": str(exc)}


def report():
    _hdr("Final Report")
    labels = {
        "step1": "systemd service active",
        "step2": "GET /health",
        "step3": "DB connection (users table)",
        "step4": "Valkey SET/GET/DEL",
        "step5": "LLM gateway reachable",
        "step6": "POST /telegram/events round-trip",
    }
    all_pass = True
    print(f"\n  {'Test':<42} {'Status'}")
    print("  " + "-" * 55)
    for k, label in labels.items():
        r = _results.get(k, {})
        if r.get("pass"):
            print(f"  [✓] {label:<42} PASS")
        else:
            print(f"  [✗] {label:<42} FAIL  {r.get('error', r.get('status', ''))[:30]}")
            all_pass = False
    print(f"\n  Total elapsed: {time.time() - _start:.1f}s")
    print()
    if all_pass:
        _ok("Phase 3 GREEN — shogun-core is live and responding.")
    else:
        _fail("One or more checks failed. Review above.")
    return all_pass


if __name__ == "__main__":
    step1_process()
    step2_health()
    step3_db()
    step4_valkey()
    step5_llm_gateway()
    step6_telegram_events()
    ok = report()
    sys.exit(0 if ok else 1)
