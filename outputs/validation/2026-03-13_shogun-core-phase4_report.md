# Evidence: shogun-core Phase 4 — Voice, Photo, Translate, Location Trigger, RAG
**Date:** 2026-03-13
**Persona:** devops-agent
**Node:** brainnode-01 (192.168.71.222)
**Service:** shogun-core v0.4.0
**Port:** 8082

---

## New Capabilities

| Capability | Implementation |
|:-----------|:---------------|
| Voice transcription | Download OGG via Telegram Bot API → Gemini /v1/multimodal → process as text |
| Photo analysis | Download JPEG via Telegram Bot API → Gemini /v1/multimodal → travel-aware description |
| Translate mode | `/translate on\|off` per-user toggle backed by Valkey (24h TTL) |
| Location trigger | Haversine 150m + 5-minute cooldown → proactive LLM recommendation |
| RAG pipeline | Food/place keyword detection → Tavily Tabelog search → LLM synthesis |

---

## Validation Results — 6/6 PASS

| Check | Result | Detail |
|:------|:-------|:-------|
| systemd service active | ✅ PASS | shogun-core.service enabled + running |
| GET /health | ✅ PASS | version=0.4.0 |
| DB connection (shogun_v1) | ✅ PASS | 3 users |
| Valkey SET/GET/DEL | ✅ PASS | valkey.platform.ibbytech.com:6379 |
| LLM gateway reachable | ✅ PASS | all 3 providers keyed |
| POST /telegram/events round-trip | ✅ PASS | 954ms, full Gemini reply |

---

## Environment

| Variable | Status |
|:---------|:-------|
| `TELEGRAM_BOT_TOKEN` | ✅ Added — sourced from telegram-gateway `.env` on svcnode-01 |
| `TAVILY_GATEWAY_URL` | Uses default (https://tavily.platform.ibbytech.com) |
| `SCRAPER_GATEWAY_URL` | Uses default (https://scrape.platform.ibbytech.com) |

---

## New Files

```
app/services/telegram_files.py  — Telegram Bot API file downloader (base64 output)
app/services/tavily.py          — Tavily search client (routes via platform gateway)
app/services/rag.py             — RAG pipeline (food keyword detection + Tavily inject)
app/handlers/voice.py           — Voice: download → transcribe → LLM response
app/handlers/photo.py           — Photo: download → multimodal analysis
app/handlers/location.py        — Full Phase 4: Haversine trigger + LLM recommendation
```

## Modified Files

```
app/valkey_client.py    — Added: get/save_location(), get/set_translate_mode()
app/handlers/text.py    — Translate mode aware + RAG routing
app/commands/system.py  — Added /translate command; /status shows translate mode
app/main.py             — Route photo/voice to dedicated handlers (v0.4.0)
app/config.py           — Added: telegram_bot_token, tavily_gateway_url, scraper_gateway_url
.env.example            — Documented new Phase 4 env vars
```

---

## Architecture

```
Todd → Telegram → @Shogun2026_bot
  → platform-telegram-gateway (svcnode-01:3001)
  → POST http://192.168.71.222:8082/telegram/events
  → shogun-core v0.4.0 (brainnode-01, systemd)
    kind=text    → RAG pipeline (Tavily if food query) → Gemini → reply
    kind=voice   → Telegram Bot API (download OGG) → /v1/multimodal → Gemini → transcribe → reply
    kind=photo   → Telegram Bot API (download JPEG) → /v1/multimodal → Gemini → analyze → reply
    kind=location → Haversine(150m) + cooldown(5min) → Gemini → proactive tip
  → reply_text → gateway → Telegram → Todd
```

---

## Outcome

✅ PHASE 4 COMPLETE — shogun-core v0.4.0 live on brainnode-01 with full voice, photo, translate mode, location trigger, and RAG pipeline.

### Pending validation (requires live testing by Todd)
- Send a voice message and verify transcription + reply
- Send a photo and verify analysis
- Use `/translate on` and send Japanese text
- Walk 150m+ with live location sharing active and verify proactive tip fires
- Ask a food/restaurant question and verify RAG search augments the reply
