---
name: concierge-brain
description: >
  Defines how Shogun's AI concierge behaves — system prompt architecture, context
  assembly, recommendation patterns, personality, and data coverage strategy. Use
  this skill when modifying AI behavior, adding new data sources to the prompt,
  building function calling tools, or tuning recommendation quality.
user-invocable: true
---

# Shogun Concierge Brain

## Overview

Shogun is an AI travel concierge for a 3-person family trip to Japan (Mar 23 - Apr 9, 2026). It serves two frontends — Telegram (mobile, on-the-ground) and a web UI (planning, itinerary management). Both share the same persona but differ in capability: the web UI has function calling (itinerary CRUD, knowledge search, web search), while Telegram uses keyword-triggered RAG with no tool calling.

**LLM:** Gemini 2.0 Flash via platform LLM gateway (web UI also calls Gemini REST API directly for function calling).

**Reference files:**
- Telegram system prompt: `app-services/shogun-core/app/services/llm.py` (`build_system_prompt`)
- Web UI system prompt: `app-services/shogun-web/shogun-web-api/routers/chat.py` (`build_system_prompt`)
- RAG pipeline (Telegram): `app-services/shogun-core/app/services/rag.py`
- Tavily client (Telegram): `app-services/shogun-core/app/services/tavily.py`
- Tavily client (web): `app-services/shogun-web/shogun-web-api/services/tavily.py`
- Text handler: `app-services/shogun-core/app/handlers/text.py`
- Location handler: `app-services/shogun-core/app/handlers/location.py`
- Voice handler: `app-services/shogun-core/app/handlers/voice.py`
- Photo handler: `app-services/shogun-core/app/handlers/photo.py`
- Morning brief: `app-services/shogun-core/app/services/brief.py`
- Weather service: `app-services/shogun-core/app/services/weather.py`
- Valkey context: `app-services/shogun-core/app/valkey_client.py`
- DB queries: `app-services/shogun-core/app/db.py`
- Web chat handler: `app-services/shogun-web/shogun-web-api/routers/chat.py`

---

## System Prompt Architecture

There are two `build_system_prompt` functions — one per frontend. Both share the same core persona but diverge in structure.

### Telegram System Prompt (`shogun-core/app/services/llm.py`)

Built by `build_system_prompt(user, prefs, weather_str)`. Assembly order:

1. **Persona declaration** — "You are Shogun, an expert Japan travel concierge for the Ibbotson family." Establishes 10 years of living-in-Japan expertise.
2. **Traveler profiles** — Todd (tech/food/culture), Brenda (shopping/skincare/temples), Madeline (anime/vintage/photography). Hardcoded.
3. **Behavioral directives** — Direct, practical, specific. No generic tourism advice. English default. Concise for mobile.
4. **Current JST date and time** — Always injected via `datetime.now(JST)`. The LLM never guesses the time.
5. **Full trip schedule** — Hardcoded city-by-city itinerary with accommodation addresses in English and Japanese, nearest station info, and transit lines.
6. **Accommodation awareness rule** — "When the user asks about 'our place'... use the accommodation above." Prevents the LLM from asking for information it already has.
7. **User identity** — `display_name` from DB if the user is registered.
8. **User preferences** — From `user_preferences` table, grouped by category (dietary, interests, etc.).
9. **Weather** — Pre-fetched from Open-Meteo, cached 30 min in Valkey. Format: "Weather in Osaka: 18C now (high 22C / low 14C), 2.1mm precipitation".
10. **Today's itinerary** — From `trip_itinerary` table for today's `date_local`. Shows leg type, time, title, and truncated notes.
11. **City POIs** — From `trip_pois` table for the current city. Capped at 8 entries. Shows name and best_time_notes or crowd_notes.

### Web UI System Prompt (`shogun-web-api/routers/chat.py`)

Built by `build_system_prompt(city, conversation_context)`. Much more extensive:

1. **Same persona** as Telegram but with expanded behavioral rules (9 numbered rules covering search protocol, location context, itinerary management, answer quality, currency, transit, trip awareness, destructive actions, proactive help).
2. **Search protocol** — Mandatory order: search_trip_knowledge FIRST, then web_search only if knowledge base is empty, then fall back to expertise. Never say "I can't find information."
3. **Location context tracking** — Maintains location awareness across messages. If a user mentions "near the National Museum" and follows up with "how about Y?", the location sticks.
4. **Accommodation block** — Same addresses and stations as Telegram.
5. **Extended trip schedule** — More detailed day-by-day plan including specific activity assignments (Apr 2: Ueno Park + Ameyoko, Apr 5: Shimokitazawa vintage, etc.).
6. **Current context block** — Date, time, city, weather, today's itinerary, POIs, and conversation context (location/topic from recent messages).
7. **Tool inventory** — Lists all 10 available tools with brief descriptions.

### Key Differences Between Frontends

| Aspect | Telegram | Web UI |
|--------|----------|--------|
| System prompt size | ~60-80 lines | ~120 lines |
| Function calling | None | 10 tools via Gemini REST API |
| max_tokens | 600 (200 for location) | 2048 |
| RAG | Keyword-triggered (food/event) | Tool-based (search_trip_knowledge, web_search) |
| Context tracking | Simple Valkey history | Location + topic entity extraction |
| Conversation management | Single thread per user | Multi-conversation with titles |

---

## Context Assembly Strategy

### Data Sources Injected into Every Request

| Source | Code Path | What It Provides | Cache |
|--------|-----------|-------------------|-------|
| JST clock | `datetime.now(JST)` in both `build_system_prompt` | Current date and time | None (computed) |
| User profile | `db.get_user_by_telegram_id()` / web auth | display_name, notification_active | None |
| User preferences | `db.get_user_preferences(user_id)` | Dietary, interests, grouped by category | None |
| Weather | `weather.get_weather_for_city()` via Open-Meteo | Temp, high/low, precipitation | Valkey 30 min |
| Today's itinerary | `db.get_todays_itinerary(date)` | Scheduled legs for today | None |
| Current city | `db.get_city_for_date(date)` | Derived from most recent accommodation leg | None |
| City POIs | `db.get_pois_by_city(city)` | Pre-loaded place intelligence (up to 8) | None |
| Conversation history | `valkey_client.get_context()` | Last 20 messages (10 turns) | Valkey 24h TTL |

### Data Sources Available On-Demand (Web UI Tools)

| Source | Tool Name | What It Provides |
|--------|-----------|-------------------|
| Full itinerary | `get_itinerary_legs` | All trip legs, filterable by city/date |
| Trip overview | `get_trip_overview` | Day-by-day busy/free summary |
| Knowledge base | `search_trip_knowledge` | ILIKE search on `knowledge_items` table |
| POIs | `get_trip_pois` | Points of interest, filterable |
| Web search | `web_search` | Tavily search with auto-save to knowledge_items |
| Packing checklist | `get_checklist_items` | Checklist items by category/status |

---

## Response Personality and Tone

Shogun is NOT a generic chatbot. The persona is:

- **Expert, not enthusiastic.** Speaks like someone who has lived in Japan for a decade. Knows crowd patterns, opening hours, and local customs. Does not say "Oh, what a great question!"
- **Direct and practical.** Gives specific place names, station names, line colors, walking distances, price ranges in yen, and wait time estimates.
- **Concise for Telegram.** Mobile interface demands brevity. 2-4 sentences for most replies. Location triggers get 2-3 sentences max.
- **Richer for web.** Can be more detailed since the web UI is used for planning.
- **Family-aware.** Knows each traveler's interests. When Todd asks about food, lean toward local izakayas. When Brenda asks about shopping, lean toward skincare and temple goods. When Madeline asks, lean toward vintage shops and anime stores.
- **Never asks for information it has.** The accommodation addresses, station names, and trip dates are in the system prompt. The LLM must use them directly.
- **English default.** Only switches to Japanese when explicitly asked or in translate mode.

### Answer Quality Standard

**BAD:** "There are some good ramen shops in the area."
**GOOD:** "Afuri Ramen in Ebisu (阿夫利) -- 15 min by Yamanote from Sugamo, known for yuzu shio ramen, 1,100 yen/bowl, usually 10-20 min wait."

Every recommendation should include: name (EN + JA if known), location relative to accommodation or landmarks, why it matters, and practical info (hours, price, tips).

---

## RAG Pipeline

### Telegram RAG (`shogun-core/app/services/rag.py`)

Keyword-triggered, no function calling. Two paths:

1. **Food queries** — Matches against `_FOOD_KEYWORDS` (restaurant, ramen, sushi, etc.). Searches Tavily with `include_domains: ["tabelog.com"]`. Injects results as `[Web search results -- Tabelog/local sources:]` block appended to the user message.

2. **Event/sakura queries** — Matches against `_EVENT_KEYWORDS` (sakura, cherry blossom, weather, events, etc.). Searches Tavily with no domain restriction. Injects results as `[Web search results -- current 2026 data:]` block.

3. **All other queries** — Skip Tavily, send directly to LLM with system prompt context only.

**Fallback:** If Tavily returns empty results for either path, falls back to plain LLM (no RAG augmentation).

### Web UI RAG (`shogun-web-api/routers/chat.py`)

Tool-based, two-tier:

1. **Step 1: search_trip_knowledge** — ILIKE search on `knowledge_items` table (topic + content_summary). If results found, answer from those.
2. **Step 2: web_search** — Tavily search with auto-save. Results above score 0.3 are automatically inserted into `knowledge_items` with deduplication on `source_url`. This means the knowledge base grows over time.
3. **Step 3: Expertise fallback** — If both return empty, the system prompt instructs: "use your Japan expertise: name specific places, give practical details, never say 'I'm having trouble'."

**Sakura/event queries** (web) — Detected by `_is_sakura_query()` and augmented via inline Tavily search BEFORE the tool-calling loop starts.

### Auto-Save Pattern (Web UI Only)

The `web_search` tool automatically categorizes results (restaurant, shopping, temple, transit, practical, museum, skincare) using keyword matching and saves them to `knowledge_items`. This creates a self-improving knowledge base: the first search for "ramen near Sugamo" hits Tavily, but subsequent queries hit the local knowledge base first.

---

## Time-Awareness Patterns

The current JST time is always in the system prompt. The LLM uses this for:

- **Morning brief** — Sent at 7:00 AM JST (22:00 UTC) via APScheduler cron job in `main.py`. Contains: date header, trip day counter, current city, today's scheduled activities, weather forecast, and a call-to-action.
- **Pre-trip countdown** — Morning brief activates 1 week before departure (Mar 16) with "Japan in X days!" messaging.
- **Time-appropriate recommendations** — The LLM sees the current time and should suggest morning activities in the morning, lunch spots around noon, evening activities in the evening.
- **City POI best_time_notes** — POIs in the system prompt include timing hints like "best before 10am" or "sunset viewing spot" that the LLM should use contextually.

---

## Location-Awareness Patterns

### Telegram Location Handler (`shogun-core/app/handlers/location.py`)

Proactive recommendations triggered by physical movement:

- **Threshold:** 150 meters from last trigger point AND 5 minutes cooldown.
- **Haversine distance** calculation using `_haversine_meters()`.
- **Trigger prompt:** "The user has just moved to coordinates X, Y in Japan. Give a brief, practical tip: what's worth stopping for nearby?"
- **Max tokens:** 200 (enforced brevity for on-the-move context).
- **History management:** Location exchange is stored in context (as `[Location update: lat, lng]`) so follow-up questions like "tell me more about that" work naturally.
- **Notification control:** Users can `/quiet` to disable location triggers, `/active` to re-enable.
- **First location:** When a user shares location for the first time, Shogun acknowledges and sets up the trigger system.

### Web UI Location Context (`shogun-web-api/routers/chat.py`)

Entity-based location tracking (no GPS):

- **`_KNOWN_LOCATIONS`** — Dictionary of ~45 landmark/area names mapped to area descriptions. Covers Tokyo, Osaka, Nara, and Kanazawa neighborhoods.
- **`_extract_conversation_context()`** — Scans current message + last 3 user messages for location references. Extracts location, topic, and city_override.
- **Location persistence** — Extracted context is merged with previous context in Valkey (1h TTL). New context overrides previous, but previous fills gaps. This means "near the National Museum" sticks across follow-up messages.
- **Accommodation resolution** — Generic references ("hotel", "airbnb", "our place") resolve dynamically to the current city's accommodation.

---

## Conversation Memory

### Telegram (Valkey)

- **Key pattern:** `shogun:context:{telegram_user_id}`
- **Format:** JSON list of `{role, content}` dicts
- **Window:** Last 20 messages (10 turns), trimmed after each exchange
- **TTL:** 24 hours idle, reset on every write
- **Reset:** `/reset` command clears context via `clear_context()`

### Web UI (Valkey)

- **Multi-conversation:** Each user can have multiple named conversations
- **Key patterns:**
  - `shogun:web:{user_id}:conversations` — List of conversation metadata (30-day TTL)
  - `shogun:web:{user_id}:chat:{conv_id}` — Message history per conversation (24h TTL)
  - `shogun:web:{user_id}:current_conv` — Active conversation ID (30-day TTL)
  - `shogun:web:{user_id}:conv_context` — Location/topic context (1h TTL)
- **Auto-titling:** Conversations are titled from the first user message (truncated to 60 chars)
- **Legacy migration:** On first access, migrates any single-thread history to the multi-conversation model

---

## Function Calling (Web UI Only)

### Tool Definitions (`CALENDAR_TOOLS` in `chat.py`)

10 tools declared in Gemini's native `functionDeclarations` format:

| Tool | Purpose | DB Table | Mutating |
|------|---------|----------|----------|
| `get_itinerary_legs` | Read trip calendar | `trip_itinerary` | No |
| `update_itinerary_leg` | Modify leg fields | `trip_itinerary` | Yes |
| `create_itinerary_leg` | Add new activity | `trip_itinerary` | Yes |
| `delete_itinerary_leg` | Remove activity | `trip_itinerary` | Yes |
| `get_trip_overview` | Day-by-day summary | `trip_itinerary` | No |
| `search_trip_knowledge` | Search knowledge base | `knowledge_items` | No |
| `web_search` | Tavily + auto-save | `knowledge_items` | Yes (insert) |
| `get_trip_pois` | Browse POIs | `trip_pois` | No |
| `get_checklist_items` | Read packing list | `checklist_items` | No |
| `toggle_checklist_item` | Pack/unpack item | `checklist_items` | Yes |

### Tool-Calling Loop (`_run_chat_with_tools`)

- **Max rounds:** 5 (configurable via `MAX_TOOL_ROUNDS`)
- **Deduplication:** Identical tool+args combinations are skipped in subsequent rounds
- **Safety exit:** After max rounds without text, a final call with empty tools forces a text response
- **Action tracking:** Each tool call produces a `tool_actions` list returned to the frontend for UI display
- **Fallback:** If Gemini REST API fails, falls through to LLM gateway (no tools)

### Design Principles for New Tools

When adding a function calling tool:
- Declare it in `CALENDAR_TOOLS` using Gemini's native format
- Implement `_exec_{tool_name}(args)` returning a plain string
- Add to `_TOOL_EXECUTORS` dispatch table
- Add a case to `_tool_action_summary()` for UI display
- Read tools should be called before write tools (the system prompt enforces "ALWAYS call get_itinerary_legs first")
- Destructive tools must include confirmation language in their description
- Tool results are plain text strings -- Gemini synthesizes the final user-facing response

---

## Multimodal Handling

### Voice Messages (`shogun-core/app/handlers/voice.py`)

- Downloads OGG from Telegram Bot API via `download_file_b64()`
- Transcribes via LLM gateway `/v1/multimodal` endpoint (Gemini multimodal)
- Processes transcription as a text message through the normal chat flow
- Returns response prefixed with transcription so user can verify accuracy
- Translate mode: voice transcription is routed through the translation path

### Photo Analysis (`shogun-core/app/handlers/photo.py`)

- Downloads largest photo size from Telegram
- Analyzes via LLM gateway `/v1/multimodal` with travel-focused prompt
- Default prompt focuses on: landmarks, food, menus, signs (translate Japanese), products, places
- Caption-driven: if user includes a caption, the analysis prompt answers their specific question
- Analysis is saved to conversation context for follow-up questions

---

## The 25-Second Telegram Timeout Constraint

The Telegram gateway has a ~30s timeout. Shogun-core sets `TIMEOUT = 25.0` for LLM calls, leaving 5s buffer for network overhead. This constraint shapes AI response design:

- **max_tokens = 600** for Telegram text replies (keeps generation time down)
- **max_tokens = 200** for location triggers (minimal generation)
- **Tavily timeout = 15.0s** — if Tavily is slow, the RAG path may exceed 25s total
- **Sequential pipeline:** Tavily search + LLM call must both complete within 25s
- **No tool calling on Telegram** — multi-round tool loops would exceed timeout
- **Timeout error message:** "Sorry, I'm taking too long to respond. Please try again."
- **Web UI uses 30s timeout** and 2048 max_tokens since it's not bound by Telegram limits

---

## Multi-User Awareness

Three registered users with distinct interests:

| User | Interests | Recommendation Lean |
|------|-----------|---------------------|
| Todd | Tech, food, culture | Local izakayas, tech districts, cultural sites |
| Brenda | Shopping, skincare, temples | Drugstore beauty, temple visits, shopping streets |
| Madeline | Anime, vintage, photography | Vintage shops, anime stores, photogenic spots |

The system prompt includes the user's `display_name` and their `user_preferences` grouped by category. The LLM should tailor recommendations based on who is asking. Preferences are stored in `user_preferences` table with `category`, `preference_key`, `preference_value`, and `notes` columns.

Notification preferences are per-user: each user can independently `/quiet` or `/active` location alerts.

---

## Fallback Behavior When Data Is Sparse

The system prompt and code enforce a clear fallback chain:

1. **Knowledge base first** (web UI) — `search_trip_knowledge` searches the `knowledge_items` table
2. **Web search** — Tavily search with auto-save for future queries
3. **LLM expertise** — The system prompt explicitly instructs: "use your Japan expertise: name specific places, give practical details, never say 'I'm having trouble' or 'I cannot find'."
4. **Tavily empty on Telegram** — Falls back to plain LLM with system prompt context only (no RAG augmentation)
5. **Weather unavailable** — Silently omitted from system prompt (non-fatal)
6. **Itinerary/POI DB failure** — Caught by try/except, logged as warning, prompt continues without trip context
7. **Valkey failure** — Context functions return empty lists, conversations start fresh

The key principle: **never tell the user you can't help.** Always produce a useful answer, even if the data sources are empty.

---

## System Commands (Telegram Only)

Handled by `app/commands/system.py`, bypassing the LLM entirely:

| Command | Effect |
|---------|--------|
| `/help` | Lists available commands |
| `/quiet` | Disables proactive location alerts |
| `/active` | Re-enables location alerts |
| `/translate on/off` | Toggles Japanese-English translation mode |
| `/status` | Shows current settings (notification state, translate mode) |
| `/reset` | Clears conversation memory in Valkey |

### Translate Mode

When active (Valkey flag `shogun:translate:{uid}`), appends to system prompt:
"For any Japanese text they send: translate to English. For any English text they send: translate to Japanese and show both. Keep translations natural and note any cultural context where useful."

Voice messages in translate mode are specifically routed through translation.

---

## Morning Brief (`app/services/brief.py`)

Proactive daily message sent at 7:00 AM JST to all users with `notification_active = True`:

- **Active window:** Mar 16 (1 week pre-trip) through Apr 9 (departure)
- **Pre-trip:** Shows countdown ("Japan in X days!")
- **During trip:** Shows trip day counter ("Day 5 of 18"), current city with emoji, today's scheduled activities, weather forecast
- **Free days:** Explicitly noted as "Free day -- no scheduled activities"
- **Call to action:** "Ask me anything about today's plans!"

---

## Platform Service Integration Points

| Service | FQDN | Timeout | Used By |
|---------|------|---------|---------|
| LLM Gateway | `llm.platform.ibbytech.com` | 25s (Telegram), 30s (web) | Chat completions, multimodal |
| Tavily | `tavily.platform.ibbytech.com` | 15s | RAG search (food, events, web) |
| Telegram Gateway | `platform-telegram-gateway:3001` | 10s | Outbound message sending |
| Open-Meteo | `api.open-meteo.com` (external) | 5s | Weather data |
| Valkey | `valkey.platform.ibbytech.com:6379` | 3s connect | Context, location, translate mode, weather cache |
| PostgreSQL | `192.168.71.221:5432` (shogun_v1) | 5s connect | Users, preferences, itinerary, POIs, knowledge |
| Telegram Bot API | `api.telegram.org` (external) | 30s | Voice/photo file downloads |
| Gemini REST API | `generativelanguage.googleapis.com` (external) | 30s | Function calling (web UI only) |
| Google Places Gateway | `http://192.168.71.220:8081` (internal IP) | 10s | `find_nearby_places` tool |

---

## Gemini LLM Constraints and Architectural Workarounds

**This section documents hard-won lessons. Do not skip it when modifying AI behavior.**

### The Fundamental Limitation: Gemini Reformats Everything

Gemini 2.0 Flash will **always** rewrite tool result text into its own prose. You cannot instruct it to output specific URLs, structured lists, or pre-formatted content verbatim through system prompt instructions alone — no matter how strong the wording. Instructions like "copy these links exactly" or "use this text verbatim" are ignored in practice.

This is not a prompt engineering problem. It is fundamental LLM behavior. Attempting to fix it by iterating on system prompt wording wastes tokens and time with no result.

### The Bypass Pattern: `##FORMATTED_BLOCK##`

The architectural solution is to prevent Gemini from ever seeing the pre-formatted content, then append it to the final response after Gemini generates its text.

How it works in `_run_chat_with_tools` (in `chat.py`):

```
_BLOCK_START = "##FORMATTED_BLOCK_START##"
_BLOCK_END   = "##FORMATTED_BLOCK_END##"
```

1. A tool returns: `[plain text context for Gemini]\n##FORMATTED_BLOCK_START##\n[pre-built markdown]\n##FORMATTED_BLOCK_END##`
2. `_run_chat_with_tools` detects the block markers
3. The block content is extracted and stored in `formatted_blocks[]`
4. Only the plain text (before `##FORMATTED_BLOCK_START##`) is sent to Gemini as the tool result
5. After Gemini produces its text response, the formatted blocks are appended verbatim

**When to use this pattern:**
- Pre-built Google Maps direction links (URLs must be exact)
- Numbered place cards with distances, walking times, and links
- Any content where the exact format is load-bearing (not just informational)

**When NOT to use this pattern:**
- General text answers where Gemini's synthesis is desirable
- Search results where Gemini should summarize and contextualize
- Conversational responses

### Place Data Architecture

The `find_nearby_places` tool uses the formatted block pattern to deliver place cards. The tool:

1. Calls Google Places gateway `searchNearby` endpoint at `http://192.168.71.220:8081`
2. Gets lat/lng from the API response (`places.location`) for every result
3. Calculates real haversine distance from the anchor coordinate to each place
4. Sorts all results closest-first — **no hard filter** (hard filtering caused critical data loss in testing when shops were just outside the requested radius)
5. Labels results beyond the requested radius so the user can decide
6. Builds two Google Maps links per place:
   - **Walk from [Anchor]**: uses the anchor's exact lat/lng as origin — shows walking directions from the trip accommodation
   - **Navigate from here**: no `origin=` param — Google Maps uses device GPS automatically
7. Returns plain summary for Gemini + formatted block with full place cards

**Critical: never generate Google Maps direction URLs manually.** The tool builds them from real lat/lng coordinates. Any manually-constructed URL that doesn't use real coordinates will be wrong.

### Tool Inventory (Web UI) — Current State

11 tools as of 2026-03-20:

| Tool | Purpose | DB Table | Mutating |
|------|---------|----------|----------|
| `get_itinerary_legs` | Read trip calendar | `trip_itinerary` | No |
| `update_itinerary_leg` | Modify leg fields | `trip_itinerary` | Yes |
| `create_itinerary_leg` | Add new activity | `trip_itinerary` | Yes |
| `delete_itinerary_leg` | Remove activity | `trip_itinerary` | Yes |
| `get_trip_overview` | Day-by-day summary | `trip_itinerary` | No |
| `search_trip_knowledge` | Search knowledge base | `knowledge_items` | No |
| `web_search` | Tavily + auto-save + `include_domains` support | `knowledge_items` | Yes (insert) |
| `get_trip_pois` | Browse POIs | `trip_pois` | No |
| `get_checklist_items` | Read packing list | `checklist_items` | No |
| `toggle_checklist_item` | Pack/unpack item | `checklist_items` | Yes |
| `find_nearby_places` | Google Places nearby search with direction links | `knowledge_items` | Yes (insert) |

The original `CALENDAR_TOOLS` section above documents 10 tools — the `find_nearby_places` tool was added 2026-03-20 and must be included in any tool audit.

### `web_search` — `include_domains` Parameter

`web_search` accepts an optional `include_domains` array to restrict Tavily results to specific domains. Key usage:

```
include_domains: ["tabelog.com"]   → Tabelog restaurant reviews only
include_domains: []                → Unrestricted search (default)
```

Gemini should pass `include_domains: ["tabelog.com"]` when the user asks for restaurant reviews, ratings, or Tabelog-specific info.

### Source Transparency: `tool_actions` Pipeline

Every AI response in the web UI carries a `tool_actions` list. This list is the source of the green "✓ tool used" badges the user sees in the chat.

Key behavioral rules:
- `tool_actions` is **always stored** in Valkey with the assistant message, even when it is an empty list `[]`
- An empty `[]` means "AI answered without calling any tool" → renders as gray "No tools called — answered from conversation context" badge
- `undefined` tool_actions (old messages before this feature) → no badge rendered
- The Valkey history endpoint returns `tool_actions` even for empty lists (`if "tool_actions" in h:` not `if h.get("tool_actions"):`)

This is the user's primary way to see "how the AI got its answer." It must never be silently dropped.

### System Prompt Behavioral Rules (Web UI) — Current State

The system prompt in `_build_system_prompt()` in `chat.py` enforces 10 numbered rules (as of 2026-03-20). When adding new behavior, add it as a numbered rule or to the relevant section:

- Rule 1–3: Search protocol (knowledge base → web search → expertise fallback)
- Rule 4: Location context persistence
- Rule 5: Itinerary management discipline (read before write)
- Rule 6: Answer quality standard (specific, never vague)
- Rule 7: Currency in yen, transit with line names
- Rule 8: Full trip context available
- Rule 9: No destructive actions without explicit confirmation
- Rule 10: Links and maps — deliver in the same response, never say "I will provide," copy pre-built direction links exactly

Key: Rule 10 exists because Gemini would sometimes say "I'll get those links for you" and then not include them. The rule reinforces the behavior but is backed by the formatted block architecture for reliable delivery.
