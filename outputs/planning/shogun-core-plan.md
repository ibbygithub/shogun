# Plan: Shogun Core — Japan Trip Companion MVP
Date: 2026-03-12
Status: Approved

## Objective

Build a working AI travel concierge for a 17-day Japan trip departing March 23,
2026. Shogun runs on Telegram, knows where the family is, knows who each person
is, and responds with the kind of local intelligence a 10-year Japan resident
would offer — not a Google Maps wrapper.

The hard constraint: **no ability to fix or modify anything once the trip starts.**
Everything must be battle-tested before departure. Fewer features that work
perfectly beat many features that half-work.

---

## Travelers

| Name | Role | Notifications | Notes |
|:-----|:-----|:-------------|:------|
| Todd Ibbotson | Primary user, experimenter | Active (default) | Driving this build |
| Brenda Loo | Travel architect, built the itinerary | Silent (default) | Expert traveler, likely to ask targeted questions |
| Madeline Ibbotson | Anime / Ghibli enthusiast | Silent (default) | Ikebukuro + Akihabara + Shimokitazawa are her zones |

Users identified by Telegram user ID. Pre-configured mapping at deployment.
Todd administers notification states. Each user can toggle their own.

### Dietary Profiles (trip-long constants — stored in shogun_v1 DB)

**Todd Ibbotson**
- Eats: beef ✅, chicken ✅, some fish ✅
- Restrictions: none
- Preferences: open explorer, beef teriyaki called out as example

**Brenda Loo**
- Eats: fish ✅, dashi/fish-based broths ✅, beef broth soups ✅, vegetarian dishes ✅
- Will NOT eat: red meat as protein ❌ (pork, lamb, beef steak — broth is fine, meat is not)
- Note: Japanese cuisine is naturally well-suited to her profile. Dashi confirmed OK.

**Madeline Ibbotson**
- Eats: chicken katsu ✅ (favourite), beef ✅
- Will NOT eat: fish ❌
- Preferences: chicken katsu specifically

### Group Restaurant Filtering — Core Use Case

When location trigger fires or user asks for food recommendations, Shogun must
find restaurants where ALL THREE profiles are satisfied simultaneously:
- Brenda: vegetarian/fish option available, no red meat
- Madeline: chicken option available (katsu preferred), no fish forced
- Todd: beef or chicken option available

Example output: "3 restaurants within 200m cover the whole group —
Brenda: grilled fish set, Madeline: chicken katsu, Todd: beef teriyaki.
Closest is 80m, currently open."

This is the primary restaurant recommendation mode when the group is together.

### Shopping Profiles

**Todd Ibbotson**
- Vintage point-and-shoot cameras (no DSLR, no large lens)
- ESP32 / maker electronics components (Akihabara-specific)
- Ceramics (Kanazawa Kutani ware is the primary target)
- Personal nail/grooming kit in local Japanese steel (Sakai)
- Robot kits (Akihabara or online)
- Vintage anime figures

**Brenda Loo**
- TBD — capture via preferences questionnaire before departure

**Madeline Ibbotson**
- Vintage point-and-shoot cameras (no DSLR, no large lens)
- Vintage anime figures
- Used/thrift clothing (Harajuku / Shimokitazawa style)
- Handheld retro gaming devices (Gameboy-era)
- Specific anime franchises: TBD — capture via questionnaire

### Named POIs by City (preload targets)

**Osaka base: Tenjinbashi-Rokuchome**
- Den Den Town (Nipponbashi) — Osaka's electronics + anime district (Madeline)
- Dotonbori — group dining hub, group restaurant filtering applies here
- Kuromon Market — seafood and food stalls (Brenda)
- Tenjinbashi shotengai — longest covered shopping street in Japan, local food

**Nara (Mar 25 day trip)**
- Deer park: arrive before 9am to beat tour buses
- Kasugataisha Shrine — 10 min walk from deer park, far less crowded, arguably more impressive
- Naramachi historic district — almost tourist-free before 10am
- Cherry blossom timing: late March = peak. Early morning is essential.

**Kyoto (day trip, date TBD)**
- Fushimi Inari: dawn only — gates never close, tourists arrive after 9am
- Arashiyama bamboo grove: 7am before tour buses
- Philosopher's Path: morning walk during cherry blossom season
- Gion district: dusk is best, avoid midday crowds
- Kyoto International Manga Museum (Madeline)

**Sakai (day trip, date TBD — whole family)**
- Sakai knife district (Sakai-higashi area)
- Kitchen knives (Todd primary interest)
- Nail/grooming kits in local steel (Todd)
- Half day vs. full day: flexible — Brenda decides

**USJ (Mar 26)**
- Nintendo World (Madeline + Todd)
- Depart Airbnb 5:30am, arrive gates ~6:30am
- Route: Tenjinbashisuji-Rokuchome → Osaka Metro Sakaisujisen → Osaka Station → JR Loop → Nishikujo → JR Yumesaki → Universal City

**Kanazawa (Mar 30–Apr 1)**
- Kenroku-en garden
- Higashi Chaya geisha district — also has Kutani ware ceramics shops (Todd)
- Omicho Market — fresh seafood (Brenda excellent fit)
- 21st Century Museum of Contemporary Art
- Kutani ware (九谷焼) — target specific workshop/retail in Higashi Chaya area

**Tokyo base: Sugamo (4-37-6 Sugamo, Toshima-ku)**
- Sugamo Jizo-dori shotengai — traditional local shopping street, worth a morning
- Ikebukuro (1 stop on Yamanote): Animate flagship, Sunshine City, Pokemon Center, Jump Shop (Madeline primary)
- **Nakano Broadway** (Chuo Line, 20 min): Mandarake floors 2-4 (vintage anime figures + cameras + games — covers both Todd and Madeline in one location)
- **Shimokitazawa** (Yamanote → Shibuya → Keio line, ~40 min): Tokyo's vintage/thrift district. Multiple blocks of used clothing, independent boutiques. Best location for Madeline's used clothing interest. Very local, not touristy.
- **Akihabara maker district** (Yamanote): Akizuki Denshi, Marutsu Denki, Aitendo — ESP32 components, sensors, kits (Todd must-visit). Two blocks off main tourist strip.
- **Super Potato Akihabara** (Madeline): landmark retro gaming store, handheld consoles
- Harajuku Takeshita Street (Madeline): alternative/streetwear
- Asakusa Senso-ji temple
- Mitaka — Ghibli Museum (Apr 3 noon, booking 7961560155)
- Map Camera Shinjuku: large vintage camera dealer (Todd + Madeline)
- Tokyo dinner show (TBD — Brenda has details)

---

## Trip Summary

| Leg | City | Dates | Nights | Base |
|:----|:-----|:------|:-------|:-----|
| 1 | Osaka | Mar 24–30 | 6 | Tenjinbashi Queen, 10-12 Namihana-cho, Kita-ku, 530-0022 |
| 2 | Kanazawa | Mar 30–Apr 1 | 2 | Hotel Sanraku, 1-1-1 Owaricho |
| 3 | Tokyo | Apr 1–9 | 8 | 4-37-6 Sugamo, Toshima-ku, 170-0002 |

**Flights:** JL7555 SFO→LAX + JL69 LAX→KIX (Mar 23) | JL2 HND→SFO (Apr 9 4:25pm)
**PNR:** APGNWZ

**Confirmed activities:** Nara (Mar 25), USJ (Mar 26, depart 5:30am),
Kyoto day trip (TBD), Sakai knives (TBD), Ghibli Museum (Apr 3 noon,
booking 7961560155), Tokyo dinner show (TBD — Brenda has details)

---

## Scope

### IN SCOPE — Must work before departure

1. **shogun-core** — Telegram bot on brainnode-01 (Python/systemd, no Docker)
2. **Multi-user support** — Todd, Brenda, Madeline with distinct profiles
3. **User profiles** — dietary preferences, likes, dislikes, notification state
4. **Location awareness** — 150m radius trigger, 5-minute cooldown
5. **Notification control** — `/quiet` and `/active` per user, AI-decided group broadcast
6. **Conversation context** — Valkey 24h idle TTL per user
7. **Translation mode** — English ↔ teineigo (丁寧語) Japanese
8. **Voice input** — Telegram voice message → Gemini transcription → validated text
9. **Vision capability** — photo input → Gemini multimodal → translation/identification
10. **Face-to-face translation mode** — ephemeral two-way session, English ↔ Japanese
11. **Itinerary context** — digitized schedule loaded and accessible to Shogun
12. **Preloaded POI data** — by city, with Madeline's layer, crowd intelligence
13. **Tavily platform service** — web search including kanji queries
14. **RAG pipeline** — Tavily → Firecrawl → pgvector → LLM response
15. **Printable itinerary** — standalone bilingual HTML artifact

### OUT OF SCOPE — Post-trip build

- JR train status integration
- Flight status / gate change alerts
- Google Calendar sync
- Web-based dynamic calendar
- Twitter/X feed integration
- Tabelog native API (covered by Tavily domain-restricted search)
- Multi-city group broadcast based on separate locations

---

## Architecture

### Node Assignment

| Component | Node | Runtime | Reason |
|:----------|:-----|:--------|:-------|
| shogun-core | brainnode-01 (192.168.71.222) | Python 3 / systemd | Application tier — not platform infrastructure |
| Tavily service | svcnode-01 (192.168.71.220) | Docker / platform_net | New platform service, joins existing gateway pattern |
| shogun_v1 schema | dbnode-01 (192.168.71.221) | PostgreSQL 17 | Existing application database |
| Valkey context | svcnode-01 (192.168.71.220) | Docker / platform-valkey | Already deployed |

### Service Communication (brainnode-01 → platform)

All platform services reached via FQDN from brainnode-01. DNS confirmed
working on all nodes.

| Service | URL from brainnode-01 |
|:--------|:----------------------|
| LLM Gateway | https://llm.platform.ibbytech.com |
| Places Gateway | https://places.platform.ibbytech.com |
| Telegram Gateway | https://telegram.platform.ibbytech.com |
| Scraper / Firecrawl | https://scrape.platform.ibbytech.com |
| Tavily (new) | https://tavily.platform.ibbytech.com |
| Valkey | redis://valkey.platform.ibbytech.com:6379 |

### RAG Pipeline

```
User input (text / voice / photo)
        ↓
Intent detection  ←  LLM Gateway (Gemini 2.0 Flash)
        ↓
[If web knowledge needed]
Tavily search (kanji or English query)
        ↓
Firecrawl extract (top N URLs from Tavily results)
        ↓
pgvector store (platform_v1, scraper schema)
        ↓
Vector similarity retrieval
        ↓
LLM Gateway — synthesize response with:
  • Retrieved web content
  • User profile (dietary, preferences)
  • Itinerary context (where they are in the trip)
  • Conversation context (Valkey, 24h TTL)
        ↓
Telegram response
```

### Translation Flow

```
[Standard mode]
User speaks into Telegram → voice message
        ↓
Gemini transcribes audio → English text
        ↓
Shogun displays: "I heard: [English text] — correct?"
User confirms or corrects
        ↓
Shogun translates to teineigo (丁寧語)
Displays: English + Japanese kanji

[Face-to-face mode — /translate command]
Activate ephemeral two-way session
User side: records English → transcribed + shown as English → translated to kanji
Japanese speaker side: records Japanese → transcribed as kanji (verification) → translated to English
Session is ephemeral — not stored in conversation history
```

---

## Database Schema (shogun_v1.public)

New tables required:

```
users
  id, telegram_user_id, display_name, full_name,
  notification_active, language_preference, created_utc

user_preferences
  user_id, category (dietary/likes/dislikes/shopping/entertainment),
  preference_key, preference_value, notes, created_utc

trip_itinerary
  id, leg_sequence, leg_type (flight/accommodation/activity/transit),
  date_local, city, title,
  address_en, address_ja,
  contact_phone, confirmation_number,
  notes_en, notes_ja,
  start_time, end_time, created_utc

trip_pois
  id, city, name_en, name_ja, category,
  lat, lng, address_en, address_ja,
  tags (array — e.g. ghibli, anime, knife, food, crowd-warning),
  crowd_notes, best_time_notes,
  source, created_utc
```

---

## Phases

### Phase 1 — Tavily Platform Service
**Goal:** Tavily running on svcnode-01, accessible from brainnode-01 via FQDN
**Entry criteria:** platform develop branch current (done)
**Deliverables:** Tavily Docker service, service doc, validate_tavily.py, _index.md entry
**Exit criteria:** `tavily.platform.ibbytech.com` returns search results for a kanji query
**Complexity:** Low
**Dependencies:** Tavily API key (requires account)

### Phase 2 — Database Schema
**Goal:** shogun_v1 schema ready to receive user profiles and itinerary data
**Entry criteria:** dba-agent access confirmed, approved task plan
**Deliverables:** Migration SQL for users, user_preferences, trip_itinerary, trip_pois
**Exit criteria:** All tables exist, app user has correct grants
**Complexity:** Low
**Dependencies:** Phase 1 not required — parallel

### Phase 3 — shogun-core Foundation
**Goal:** Telegram bot running on brainnode-01, responding to all three users
**Entry criteria:** Phase 2 complete (user profiles needed), Telegram user IDs from Todd
**Deliverables:**
  - FastAPI application on brainnode-01
  - systemd service unit
  - Telegram webhook registration
  - User identification and profile loading
  - Conversation context read/write (Valkey)
  - Notification state management (/quiet, /active)
  - Basic text response via LLM Gateway
**Exit criteria:** Todd, Brenda, and Madeline can each send a message and get a response
**Complexity:** Medium
**Dependencies:** Phase 2

### Phase 4 — Intelligence Layer
**Goal:** Vision, voice, translation, and RAG all working
**Entry criteria:** Phase 3 complete
**Deliverables:**
  - Voice message processing (Telegram audio → Gemini → text)
  - Photo processing (Telegram image → Gemini multimodal)
  - Translation mode (English ↔ teineigo)
  - Face-to-face /translate command
  - Tavily → Firecrawl → pgvector RAG pipeline integrated
  - Location trigger processing (150m / 5min cooldown)
  - AI-decided group broadcast logic
**Exit criteria:**
  - Send a photo of a Japanese menu → Shogun identifies dishes and flags dietary conflicts
  - Send a voice message in English → Shogun returns teineigo translation
  - Ask "what do locals think of Nara deer park in late March" → Shogun returns local-intelligence answer
**Complexity:** High
**Dependencies:** Phase 3, Tavily API key

### Phase 5 — Data Ingest
**Goal:** All pre-trip data loaded before departure
**Entry criteria:** Phase 2 complete (schema exists), itinerary data ready
**Deliverables:**
  - Itinerary ingestion tool (AI parser from emails + template for paper items)
  - Itinerary loaded into trip_itinerary table
  - User profiles loaded (Todd, Brenda, Madeline preferences)
  - Telegram user IDs configured
  - POI data ingested by city:
    - Osaka: Tenjinbashi, Dotonbori, Den Den Town, Sakai knife district
    - Nara: timing intelligence, alternatives to deer park, Kasugataisha, Naramachi
    - Kyoto: crowd-aware timing, Fushimi Inari, Arashiyama, Gion
    - Kanazawa: Kenroku-en, Higashi Chaya, Omicho Market
    - Tokyo: Sugamo/Ikebukuro base, Akihabara, Harajuku, Asakusa, Mitaka/Ghibli,
             Shibuya, Shinjuku, dinner show location (TBD)
  - Madeline layer: Ghibli locations, Ikebukuro anime district, specific franchises (TBD)
  - Crowd intelligence: cherry blossom timing, early-morning strategies
**Exit criteria:** Shogun can answer "what should we do near the Osaka Airbnb tonight" with specific, profile-aware recommendations
**Complexity:** Medium
**Dependencies:** Phase 2, Phase 4 (RAG pipeline for ongoing enrichment)

### Phase 6 — Printable Itinerary
**Goal:** Standalone bilingual HTML document covering full trip
**Entry criteria:** Phase 5 complete (itinerary data in DB)
**Deliverables:**
  - Single HTML file, printable, no external dependencies
  - All lodging with English + Japanese address and phone
  - Flight details, confirmation numbers, PNRs
  - Activity schedule with timing
  - Emergency contacts
  - Print-optimized CSS (fits standard paper)
**Exit criteria:** Prints cleanly on A4/Letter, all addresses readable in Japanese
**Complexity:** Low
**Dependencies:** Phase 5

### Phase 7 — Hardening and Pre-departure Testing
**Goal:** Everything works under conditions resembling Japan — confirmed no fixes possible on trip
**Entry criteria:** Phases 1–6 complete
**Deliverables:**
  - End-to-end test for each user (Todd, Brenda, Madeline)
  - Voice input test (English → teineigo translation verified)
  - Photo test (Japanese menu photo → correct interpretation)
  - Location trigger test (simulate movement)
  - Group broadcast test
  - Graceful degradation test (Tavily down → Shogun still responds from preloaded data)
  - systemd auto-restart verified (shogun-core restarts after crash)
  - Valkey context survives shogun-core restart
**Exit criteria:** All three users interact successfully. Todd signs off.
**Complexity:** Medium
**Dependencies:** All phases

---

## Dependencies

| Dependency | Owner | Status |
|:-----------|:------|:-------|
| Tavily API key | Todd (sign up at tavily.com) | Not yet obtained |
| Telegram user IDs (all 3) | Todd | Not yet obtained |
| Tokyo Airbnb address | ✅ 4-37-6 Sugamo, Toshima-ku, 170-0002 | Confirmed |
| Itinerary from Brenda | Brenda | Partially captured — Kyoto/Sakai dates TBD |
| Madeline anime franchises beyond Ghibli | Todd/Madeline | TBD — needed before Phase 5 |
| Sakai scope (Todd only vs. family, half/full day) | Todd | TBD |
| USJ ticket confirmation | Brenda | Likely purchased — confirm |
| JL69 seat assignments | Todd | Unassigned |
| Osaka Airbnb passport photos | Todd | Send to host Mayu via Airbnb |

---

## Risks

See `outputs/planning/shogun-risks.md` — will be updated as phases progress.

Key risks for this build:
- **Timeline** — 10 days to departure. Phase 7 hardening cannot be skipped.
  If Phase 4 slips, Phase 6 (printable itinerary) can be produced independently.
- **No in-trip fixes** — Every failure mode must be handled gracefully.
  Shogun must degrade to "I don't know" rather than crash or hang.
- **Gemini API limits** — Multimodal calls (vision + audio) are heavier.
  Must test under realistic usage before departure.
- **brainnode-01 first workload** — This is the first service on brainnode-01.
  systemd deployment pattern needs to be established and verified.

---

## Open Items

- Sakai: Todd only or full family? Half day or full day?
- Madeline: Anime franchises beyond Ghibli (affects Ikebukuro/Akihabara preload quality)
- Kanazawa → Tokyo train details (Brenda)
- Tokyo dinner show details (Brenda)
- Specific days for Kyoto and Sakai within Osaka week

---

## Out of Scope (Confirmed)

- JR train status
- Flight delay/gate alerts
- Google Calendar integration
- Dynamic web calendar
- Twitter/X feed
- Post-trip features and Phase 2 enhancements
