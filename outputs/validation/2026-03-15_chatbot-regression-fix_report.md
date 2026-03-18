# Chatbot Regression Fix Report
**Date:** 2026-03-15
**Agent:** Claude Sonnet 4.6 (Agent A — chatbot fix and enrichment)
**Branch:** feature/20260315-chatbot-fix-ai-enrichment-dashboard

---

## Summary

Both chatbots (shogun-core Telegram and shogun-web-api web chat) were evaluated
for persona correctness, memory, and connectivity. All 6 core checks passed
without requiring any fixes — both services were already operational on this
branch. The regression diagnostic and enrichment changes were applied successfully.

---

## What Was Tested

### Infrastructure state at start of session

| Container | Port | Status |
|-----------|------|--------|
| shogun-core | 127.0.0.1:8082 | Up 5+ hours |
| shogun-web-api | 0.0.0.0:8090 | Up 5+ hours |
| platform-llm-gateway | internal:8080 | Up 5+ hours |
| platform-valkey | 127.0.0.1:6379 | Up 4+ hours |
| platform-postgres | 127.0.0.1:5432 | Up 2+ hours (healthy) |
| platform-tavily | 127.0.0.1:8084 | Up 5+ hours |

### Key findings from inspection

- **LLM_GATEWAY_URL** in shogun-core: `http://platform-llm-gateway:8080` — correct
- **VALKEY_HOST** in shogun-core: `platform-valkey` — correct
- **LLM_GATEWAY_URL** in shogun-web-api: `http://platform-llm-gateway:8080` — correct
- **VALKEY_URL** in shogun-web-api: `redis://:PASSWORD@platform-valkey:6379` — correct
- **Todd's telegram_user_id**: 204595710 (internal DB id=1)
- **shogun-web-api auth**: SHOGUN_BYPASS_AUTH=true — no auth header required
- **DB collation warning**: `shogun_v1` was created with collation 2.41, OS provides
  2.36. Cosmetic warning only — all queries succeed. Out of scope to fix.

---

## Root Cause Analysis

No functional bugs were found in the pre-existing code. Both chatbots were
delivering correct persona responses and maintaining conversation memory.

The system prompt structure in shogun-core was correct:
- System prompt delivered as `role="system"` in the messages array (not a
  separate `system` field). Matches what the LLM gateway expects.
- `build_system_prompt()` correctly handles `None` user (unregistered user path).
- Valkey context save/load working correctly for both services.

---

## verify_chatbot.py Output (before enrichment changes)

```
=== shogun-core checks ===
  [PASS] SHOGUN_CORE_HEALTH: HTTP 200
  [PASS] SHOGUN_CORE_PERSONA: I am Shogun, your Japan travel concierge...
  [PASS] SHOGUN_CORE_MEMORY: You mentioned Ichiran as your favorite ramen shop.

=== shogun-web-api checks ===
  [PASS] SHOGUN_WEB_HEALTH: HTTP 200
  [PASS] SHOGUN_WEB_PERSONA: Greetings, I am Shogun, your AI travel concierge...
  [PASS] SHOGUN_WEB_MEMORY: You mentioned that Kanazawa is your favorite city.

=== connectivity diagnostics (informational) ===
  [INFO] LLM_GATEWAY_REACHABLE: OK: 200
  [INFO] VALKEY_REACHABLE_CORE: OK: OK
  [INFO] VALKEY_REACHABLE_WEB: OK: OK
  [INFO] DB_REACHABLE_CORE: OK: OK

Core checks (1-6): PASSED: 6/6
```

---

## Files Created / Modified

| File | Action |
|------|--------|
| tools/verify_chatbot.py | CREATED — diagnostic script |
| app-services/shogun-core/app/services/llm.py | MODIFIED — time + weather injection |
| app-services/shogun-core/app/services/weather.py | CREATED — Open-Meteo weather service |
| app-services/shogun-core/app/handlers/text.py | MODIFIED — weather pre-fetch |
| app-services/shogun-core/app/services/rag.py | MODIFIED — event/sakura keywords |
| app-services/shogun-web/shogun-web-api/routers/chat.py | MODIFIED — dynamic prompt + Tavily |

---

## Out-of-scope bugs noted (not fixed)

- **DB collation mismatch**: `shogun_v1` collation version 2.41 vs OS 2.36.
  Cosmetic warning. Requires `ALTER DATABASE shogun_v1 REFRESH COLLATION VERSION`
  on dbnode-01. DBA-agent task, deferred.
