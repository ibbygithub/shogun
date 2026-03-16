# Chatbot Enrichment Report
**Date:** 2026-03-15
**Agent:** Claude Sonnet 4.6 (Agent A — chatbot fix and enrichment)
**Branch:** feature/20260315-chatbot-fix-ai-enrichment-dashboard

---

## Enrichments Added

### 1. Current JST time injection — shogun-core (llm.py)

`build_system_prompt()` now computes JST time at call time and injects:
```
Current date and time: 2026-03-16 13:11 JST
```
This prevents the LLM from hallucinating dates and times.

**Implementation:** `datetime.now(_JST)` in `build_system_prompt()`. The
`today_jst` variable that was previously computed twice (once in the function
body for itinerary, once redundantly in the try block) is now computed once
at the top and reused throughout.

---

### 2. Current JST time injection — shogun-web-api (chat.py)

`SYSTEM_PROMPT` constant replaced with `build_system_prompt(city)` function
called at request time. Injects the same `Current date and time: YYYY-MM-DD HH:MM JST`
line into every chat request.

---

### 3. Weather service — shogun-core (weather.py)

New service at `app/services/weather.py`:
- Fetches current conditions + daily forecast from Open-Meteo (free, no API key)
- Caches in Valkey for 30 minutes (`shogun:weather:{city}`, TTL=1800)
- Supports: osaka, nara, kanazawa, tokyo, kyoto
- Returns concise string: `Weather in Osaka: 13.6°C now (high 14.4°C / low 3.3°C)`
- Returns `None` on any failure — callers degrade gracefully

**Wiring:** `text.py` pre-fetches weather asynchronously before calling
`build_system_prompt()`, which accepts `weather_str` as an optional parameter.
This avoids making `build_system_prompt()` async (it uses synchronous psycopg2).

---

### 4. Weather injection — shogun-web-api (chat.py)

`_get_weather_for_city()` function in chat.py:
- First checks Valkey for a cached value from the weather router
  (key: `shogun:web:weather:{city}`) — avoids duplicate Open-Meteo calls if
  the dashboard has already fetched weather
- Falls back to a direct Open-Meteo call if cache is cold
- Injected into `build_system_prompt()` as `Today's weather: {weather_str}`

City selection uses a hardcoded trip schedule (no DB call):
- Mar 23–29: osaka
- Mar 30–31: kanazawa
- Apr 01–09: tokyo

---

### 5. RAG keyword expansion — shogun-core (rag.py)

New `_EVENT_KEYWORDS` set added alongside existing `_FOOD_KEYWORDS`:
```python
{"sakura", "cherry blossom", "hanami", "bloom", "blooming", "blossoms",
 "season", "spring flowers", "weather", "forecast", "what's on",
 "events", "happening", "weekend"}
```

Event queries (non-restaurant) use **unrestricted Tavily search** — the
Tabelog domain restriction is NOT applied. For sakura/bloom queries, the
Tavily query is templated to:
```
cherry blossom forecast {city} 2026 bloom status
```

Food queries continue to use the Tabelog domain restriction unchanged.

---

### 6. Tavily sakura enrichment — shogun-web-api (chat.py)

`_is_sakura_query()` keyword detection added to the chat handler.
When triggered, a Tavily search runs before the LLM call and the results
are prepended to the user message as context. City-aware query templating
matches the shogun-core pattern.

---

## verify_chatbot.py Output (after all enrichments)

```
=== shogun-core checks ===
  [PASS] SHOGUN_CORE_HEALTH: HTTP 200
  [PASS] SHOGUN_CORE_PERSONA: I'm Shogun, your Japan travel concierge...
  [PASS] SHOGUN_CORE_MEMORY: You mentioned Ichiran as your favorite ramen shop.

=== shogun-web-api checks ===
  [PASS] SHOGUN_WEB_HEALTH: HTTP 200
  [PASS] SHOGUN_WEB_PERSONA: I am Shogun, your dedicated AI travel concierge...
  [PASS] SHOGUN_WEB_MEMORY: You mentioned that Kanazawa is your favorite city.

=== connectivity diagnostics (informational) ===
  [INFO] LLM_GATEWAY_REACHABLE: OK: 200
  [INFO] VALKEY_REACHABLE_CORE: OK: OK
  [INFO] VALKEY_REACHABLE_WEB: OK: OK
  [INFO] DB_REACHABLE_CORE: OK: OK

=== enrichment checks ===
  [PASS] ENRICHMENT_TIME_CORE: It is 13:11 JST.
  [PASS] ENRICHMENT_TIME_WEB: Good afternoon! It is 1:11 PM on March 16th in Japan...
  [PASS] ENRICHMENT_WEATHER_CORE: Expect partly cloudy skies in Osaka, high 14.4°C / low 3.3°C
  [PASS] ENRICHMENT_WEATHER_WEB: The weather in Osaka today is 13.6°C. High 14.4°C / low 3.3°C.
  [PASS] ENRICHMENT_SAKURA_CORE: No, not yet blooming. Forecast: blooming around March 25th.
  [PASS] ENRICHMENT_SAKURA_WEB: Not in full bloom yet. Forecast suggests blooming soon...

Core checks (1-6): PASSED: 6/6
All checks (including enrichments): PASSED: 12/12
All checks passing — no action required.
```

---

## Verification: Time is Real (not hallucinated)

Before enrichment, asking "What time is it in Japan?" produced hallucinated times
like "9:03 PM on June 12th" (shogun-core) or "October 26th, 2024" (shogun-web-api).

After enrichment, both services responded with the correct current JST time
(13:11 JST on 2026-03-16), which was injected into the system prompt and
correctly quoted back by the LLM.

---

## Containers Rebuilt

Both containers rebuilt and restarted cleanly after code changes:
```
docker compose up -d --build shogun-core      # from app-services/shogun-core/
docker compose up -d --build shogun-web-api   # from app-services/shogun-web/shogun-web-api/
```
