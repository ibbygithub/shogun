# Plan: Shogun Intelligence Overhaul — AI, Knowledge, Itinerary, UI, Testing
Date: 2026-03-17
Status: Draft
Target: All green by Mar 22 (day before departure)

## Objective

Transform Shogun from "tools exist" to "travel concierge that works." Every user
interaction pattern for trip planning, research, and itinerary management must work
correctly through natural conversation. The AI must search when it doesn't know,
maintain conversational context, create/edit/delete itinerary items, and give
location-aware answers.

## Scope

**In scope:**
- AI system prompt rewrite with comprehensive rules
- Auto-search on knowledge miss (Tavily fallback in tool pipeline)
- Full itinerary CRUD via AI (create, update, delete, move)
- Conversational context tracking (location, topic continuity)
- Osaka + Kanazawa knowledge seeding (user arrives Osaka first)
- Printable bilingual itinerary (offline insurance)
- UI audit and fixes (logo, mobile, all pages)
- Comprehensive test plan covering every user interaction pattern

**Out of scope:**
- Drag-and-drop UI itinerary editor (post-trip)
- Location-aware web features (GPS on mobile web)
- Postgres conversation persistence (Valkey sufficient for trip)
- Reddit Gateway / Places Ingester (nice-to-have, not trip-critical)
- YouTube API integration

## Current State

- 10 Docker containers running on laptop (Docker Desktop)
- Cloudflare Tunnel working (shogun.ibbytech.com → laptop:3010)
- Google OAuth tested, login integration tomorrow
- 17 itinerary legs in DB, 30 POIs, 100 Tokyo knowledge items, 15 checklist items
- AI has 6 tools (get/update itinerary, checklist get/toggle, knowledge search, POIs)
- AI cannot: create legs, delete legs, search web on miss, maintain location context
- Zero knowledge items for Osaka (first 7 days) and Kanazawa (2 days)

---

## Team 1 — AI Brain Overhaul
**Complexity:** High
**Priority:** Critical path — everything depends on the AI being smart
**Files:** `routers/chat.py`, system prompt

### Phase 1A: System Prompt Rewrite

The current system prompt (lines 910–917 of chat.py) is 3 sentences of vague
identity. It needs to be a comprehensive instruction set that tells Gemini
exactly how to behave.

**New system prompt structure:**

```
IDENTITY
You are Shogun, the Ibbotson family's AI travel concierge for Japan
(Mar 23 – Apr 9, 2026). Three travelers: Todd, Brenda, Madeline.

RULES — ALWAYS FOLLOW
1. When asked about a place, restaurant, or activity you don't have data for:
   ALWAYS use search_trip_knowledge first. If that returns nothing,
   use web_search to find current information. Never say "I don't have
   that information" without searching first.

2. Maintain location context across messages. If the user asks "where can I
   find X near the National Museum" and then asks "how about Y?", the second
   question is STILL about the National Museum area. Track the most recent
   location reference and apply it to follow-up questions.

3. When the user asks to add, schedule, or put something on the calendar:
   use create_itinerary_leg. When they ask to change, update, or add a note:
   use update_itinerary_leg. When they ask to remove or cancel: use
   delete_itinerary_leg. ALWAYS confirm what you did.

4. When answering about a place or restaurant, include:
   - Name (English + Japanese if known)
   - Address or location relative to landmarks
   - Why it's relevant (e.g., "5 min walk from the museum")
   - Practical info (hours, price range, tips)

5. You know the full trip schedule. When asked "what day should I do X?",
   check which days have space. Suggest specific dates with reasoning.

6. For transit questions, give specific station names, line colors, and
   approximate journey times. Always reference the accommodation as the
   start point unless the user specifies otherwise.

7. Be concise but specific. "There are ramen shops nearby" is useless.
   "Afuri Ramen in Ebisu (15 min by Yamanote from Sugamo, ¥1,100 bowls)"
   is useful.

8. Currency is always yen unless the user asks for conversion.

CURRENT CONTEXT
[injected dynamically: date, time, weather, today's itinerary, POIs]

ACCOMMODATIONS (always in context)
- Mar 24–29: Tenjinbashi Queen Airbnb, Kita-ku, Osaka (大阪市北区浪花町10-12)
  Station: Tenjinbashisuji-Rokuchome (Sakaisuji/Tanimachi lines)
- Mar 30–31: Hotel Sanraku, Owaricho, Kanazawa (石川県金沢市尾張町1-1-1)
  Station: Kanazawa (5 min walk to Omicho Market)
- Apr 1–8: Sugamo Airbnb, Toshima-ku, Tokyo (東京都豊島区巣鴨4-37-6)
  Station: Sugamo (Yamanote/Mita lines, 1 stop to Ikebukuro)

TRIP SCHEDULE OVERVIEW
Mar 23: Travel day (SFO→LAX→KIX)
Mar 24–29: Osaka base (Nara day trip Mar 25, USJ Mar 26)
Mar 30–31: Kanazawa
Apr 1–8: Tokyo base (Ghibli Museum Apr 3 NOON timed entry)
Apr 9: Departure (HND→SFO, 4:25pm)
```

**Exit criteria:**
- System prompt is > 800 tokens of specific behavioral rules
- Accommodation addresses are always in context
- Trip schedule overview is always available to the AI

### Phase 1B: New Tools — Create and Delete Itinerary Legs

**Tool 7: `create_itinerary_leg`**
```python
create_itinerary_leg(
    title: str,           # required
    date: str,            # required, YYYY-MM-DD
    city: str,            # required
    leg_type: str,        # activity, restaurant, transit, accommodation
    description: str,     # optional — what this activity is
    notes: str,           # optional — user notes
    address_en: str,      # optional
    address_ja: str,      # optional
)
```
Implementation: POST to trip_itinerary with auto-incrementing leg_sequence.
Validation: date must be within Mar 23 – Apr 9 range.

**Tool 8: `delete_itinerary_leg`**
```python
delete_itinerary_leg(
    leg_id: int,          # required — must call get_itinerary_legs first
)
```
Implementation: DELETE from trip_itinerary WHERE id = leg_id.
Safety: AI must ALWAYS confirm with user before deleting. Add to system prompt
rules: "Before deleting a leg, tell the user what you're about to remove and
ask for confirmation. Only delete after they confirm."

**Tool 9: `web_search`**
```python
web_search(
    query: str,           # required — search query
    city: str,            # optional — adds city context to query
)
```
Implementation: Call Tavily gateway with query (+ city if provided).
Return top 5 results with title, snippet, URL.
Auto-save results to knowledge_items if they match an anchor/category pattern.
This is the KEY missing tool — it's what makes the AI search instead of giving up.

**Update existing `update_itinerary_leg`:**
- Add `date` parameter (move leg to different day)
- Add `leg_type` parameter
- Add `description` parameter (notes_en — the main description)
- Add `address_en` and `address_ja` parameters

**Exit criteria:**
- AI can create a new leg: "Add ramen at Afuri on April 5" → leg created
- AI can delete a leg: "Cancel the Shimokitazawa day" → confirms, then deletes
- AI can move a leg: "Move the Ueno trip to April 7" → date updated
- AI can web search: "Find me a burger near Ueno" → Tavily search → answer
- Results from web_search are saved to knowledge_items for future queries

### Phase 1C: Conversational Context Tracking

**Problem:** The AI loses location/topic context between messages.

**Solution:** Add a lightweight context block to the conversation state in Valkey.
Before each AI call, scan the last 3 user messages for location references
(city names, POI names, area names like "Ueno", "near the museum", etc.) and
inject a context line into the system prompt:

```
CONVERSATION CONTEXT
Recent location reference: Ueno / Tokyo National Museum area
Recent topic: restaurant search (burger, ramen)
```

**Implementation approach:**
- After each user message, extract entities: city mentions, POI/landmark names,
  activity types (food, shopping, temple, etc.)
- Store as `conversation_context` dict in the Valkey conversation metadata
- Inject into system prompt on next request
- Simple keyword extraction — not NLP. Match against known POI names from
  trip_pois + known landmarks from a static list.
- Include accommodation as default location when no specific location mentioned

**Exit criteria:**
- "Where can I find a burger near the museum?" → results near museum
- "How about ramen?" → results near THE SAME museum, not Sugamo
- "What else is nearby?" → still in museum/Ueno context
- Context resets when user explicitly mentions a new location

### Phase 1D: AI Behavioral Rules for Search

**Rule: Never say "I don't know" without searching.**

Add to system prompt:
```
SEARCH PROTOCOL
When a user asks about any restaurant, shop, activity, or service:
1. First: call search_trip_knowledge to check the knowledge base
2. If knowledge base returns results → answer using those
3. If knowledge base returns nothing → call web_search with a specific query
4. Use web_search results to answer AND they will be auto-saved for next time
5. NEVER say "I don't have information about that" — always search first

When composing web_search queries:
- Include the specific area/neighborhood, not just city
- Include "2026" or "current" for time-sensitive info
- Example: "best ramen near Ueno Tokyo 2026" not "ramen Tokyo"
```

**Exit criteria:**
- "Best tonkatsu in Kanazawa?" → search_trip_knowledge → empty → web_search →
  answer with real restaurant names
- Second time asking about Kanazawa tonkatsu → search_trip_knowledge → found
  (auto-saved from previous web_search)

---

## Team 2 — Knowledge Pipeline Completion
**Complexity:** Medium
**Priority:** High — Osaka knowledge needed for first 7 days of trip
**Files:** `tools/seed_knowledge.py` (new or update existing)

### Phase 2A: Osaka Knowledge Seeding

**Anchor: osaka-airbnb** (Tenjinbashisuji 6-chome, Kita-ku)
```
restaurant    — "best ramen near Tenjinbashisuji Osaka"
               "izakaya Tenjinbashi Osaka recommended"
               "best takoyaki Osaka locals"
               "okonomiyaki near Tenjinbashisuji Osaka"
               "breakfast cafes Kita-ku Osaka"
restaurant    — "best restaurants Dotonbori Osaka 2026"
               "Shinsekai kushikatsu Osaka recommended"
pharmacy      — "pharmacy drugstore near Tenjinbashisuji 6-chome Osaka"
convenience   — "konbini 7-eleven near Tenjinbashisuji Osaka"
temple        — "temples shrines near Tenjinbashisuji Osaka walking distance"
shopping      — "Tenjinbashi-suji shotengai shopping guide"
               "Den Den Town Osaka retro games anime"
               "vintage clothing Osaka Amerikamura"
transit       — "ICOCA card Osaka where to buy load"
               "Osaka Metro map tourist guide 2026"
practical     — "ATM international card Osaka where to withdraw yen"
               "coin locker Osaka station Namba"
```

**Anchor: nara-park** (Kintetsu Nara / Nara Park entrance)
```
restaurant    — "best restaurants near Nara Park deer park"
               "lunch near Todai-ji Nara"
practical     — "Nara day trip from Osaka guide 2026"
               "Kintetsu vs JR Osaka to Nara which is better"
temple        — "Kasugataisha Shrine Nara tips avoid crowds"
               "Naramachi walking tour historical district"
```

**Anchor: usjapan** (Universal Studios Japan)
```
restaurant    — "restaurants near Universal Studios Japan Universal City"
practical     — "USJ tips 2026 Super Nintendo World strategy"
               "USJ express pass worth it 2026"
               "first train to USJ from Tenjinbashisuji Osaka"
```

**Target: minimum 80 Osaka-area knowledge items**

### Phase 2B: Kanazawa Knowledge Seeding

**Anchor: kanazawa-hotel** (Hotel Sanraku, Owaricho)
```
restaurant    — "best restaurants near Omicho Market Kanazawa"
               "kaiseki Kanazawa recommended traditional"
               "Kanazawa morning market seafood breakfast"
               "best sushi Kanazawa near station"
market        — "Omicho Market Kanazawa what to eat guide 2026"
temple        — "Kenroku-en Garden Kanazawa tips hours"
               "Higashi Chaya District tea houses Kanazawa"
               "21st Century Museum Kanazawa hours tickets"
shopping      — "Kanazawa gold leaf shops souvenir"
               "Kutani pottery Kanazawa where to buy"
practical     — "Osaka to Kanazawa Thunderbird train 2026 schedule"
               "Kanazawa to Tokyo Kagayaki Shinkansen 2026"
               "coin locker Kanazawa station"
```

**Target: minimum 40 Kanazawa knowledge items**

### Phase 2C: Auto-Save in web_search Tool

When the `web_search` tool returns results from Tavily:
1. For each result with relevance score > 0.5:
   - Extract: title, URL, content snippet
   - Determine city from query context
   - Determine category by keyword matching (restaurant, temple, shopping, etc.)
   - Check dedup: `source_url` already in knowledge_items? Skip.
   - INSERT into knowledge_items with anchor=NULL, city, category, topic=title,
     source_url, content_summary=snippet, tavily_score
2. Return results to AI for immediate use
3. Next time this topic is searched, knowledge_items will have the data

**Exit criteria:**
- "Best burger near Ueno" → web_search → saves 3-5 results →
  future "burger Ueno" query finds them in knowledge_items
- No duplicate source_urls in knowledge_items
- knowledge_items count: Tokyo 100+ (existing), Osaka 80+, Kanazawa 40+

---

## Team 3 — Itinerary Management & Print
**Complexity:** Medium
**Priority:** High
**Files:** `routers/chat.py` (tools), `routers/itinerary.py`, new print page

### Phase 3A: Full CRUD Through AI

Already covered in Team 1 Phase 1B (create, delete, update with more fields).
This phase is the **API side** — ensuring the REST endpoints support everything
the AI tools need.

**PATCH /itinerary/{leg_id} — expand fields:**
Current: only title, notes_en, notes_ja
Add: date_local, leg_type, city, address_en, address_ja, confirmation_number

**GET /itinerary — add filtering:**
Add query params: `?city=osaka&date=2026-03-25&date_from=&date_to=`

**Exit criteria:**
- PATCH can update any field on a leg
- GET supports city and date filtering
- DELETE works and returns the deleted leg for confirmation

### Phase 3B: Itinerary Gap Analysis Tool

**Tool 10: `get_trip_overview`**
```python
get_trip_overview() -> str
```
Returns a summary of all 18 trip days showing:
- Date, city, number of legs scheduled
- "OPEN" for days with no legs
- Total legs count

This lets the AI answer: "What days are free?" or "Which Tokyo days have nothing
planned?" without scanning every leg individually.

**Exit criteria:**
- AI can answer "What days are free in Tokyo?" → lists Apr 7, Apr 8
- AI can answer "How many things are planned for Osaka?" → count by city

### Phase 3C: Printable Bilingual Itinerary

**New page: `/itinerary/print`** (or `/print`)

Server-rendered HTML page (not client component) that produces a clean,
print-friendly itinerary with:

- All 17+ legs organized by date
- Each leg shows:
  - Date + day of week
  - City badge
  - Title (English)
  - Description
  - Address (English + Japanese on separate lines)
  - Confirmation number (if present)
  - Notes
- Emergency info block at top:
  - Japan emergency: 110 (police), 119 (fire/ambulance)
  - US Embassy Tokyo: 03-3224-5000
  - Travel insurance policy number (placeholder)
  - Accommodation addresses + check-in/out info
- CSS `@media print` styling: no nav bar, no footer, clean fonts, page breaks
  between cities
- Mobile-friendly (readable on phone as backup)

**Exit criteria:**
- `/itinerary/print` renders all legs with Japanese addresses
- Ctrl+P produces clean multi-page print output
- Confirmation numbers visible for flights and hotels
- Emergency info block at top of first page

---

## Team 4 — UI Audit & Fix
**Complexity:** Medium
**Priority:** High
**Files:** Various UI components

### Phase 4A: Landing Page — Logo Fix

**Current state:** Logo in bottom-left of hero image is cropped/worse after
previous fix. The `object-position: center 15%` shifted too much.

**Investigation needed:**
- Screenshot at 1440px, 1024px, 768px, 390px widths
- Identify exact crop behavior at each breakpoint
- The logo is PART OF the image file (`shogun-landing.png`), not a separate element
- Fix options:
  a) Adjust `object-position` (try `center 25%` or `center 30%`)
  b) Add padding-bottom to the container to reveal more of the image
  c) Change `object-fit` from `cover` to `contain` on mobile
  d) Overlay the logo as a separate `<img>` element positioned absolutely
     (most reliable — decouples logo from hero image cropping)

**Exit criteria:**
- Logo fully visible at all tested viewport widths
- Hero image still looks good (no excessive letterboxing)
- Enter button clearly visible and tappable on mobile

### Phase 4B: Full Page Audit (Playwright)

Test every page in the app at desktop (1440px) and mobile (390px):

| Page | URL | Check |
|------|-----|-------|
| Landing | `/` | Logo visible, Enter button works, no Login link |
| Dashboard | `/dashboard` | All tiles render, no white banners, no raw JSON |
| Calendar | `/calendar` | All 17+ legs show, correct city colors |
| Planning | `/planning` | POIs load, timeline shows legs, filter works |
| Itinerary | `/itinerary` | All legs listed, addresses visible |
| Chat | `/chat` | Send message, get response, tool badges show |
| Wishlist | `/wishlist` | Page loads without error |
| Phrases | `/phrases` | Tabs work, copy-to-clipboard works |
| Transit | `/transit` | Content renders, no broken images |
| Checklist | `/checklist` | Items show, toggle works, progress bar |
| Budget | `/budget` | Table renders, add form works |
| Settings | `/settings` | Page loads |
| Admin | `/admin` | Health check displays |
| City: Tokyo | `/city/tokyo` | Ghibli countdown, weather, POIs, map |
| City: Osaka | `/city/osaka` | Weather, POIs, map |
| City: Nara | `/city/nara` | Weather, POIs |
| City: Kyoto | `/city/kyoto` | Weather, POIs |
| Print | `/itinerary/print` | All legs, Japanese addresses, print-clean |

**For each page capture:**
- Desktop screenshot
- Mobile screenshot
- Console errors
- Network errors (failed API calls)
- Accessibility issues (missing alt text, contrast)

### Phase 4C: Mobile Polish

The app will be used primarily on phones in Japan. Check:
- Navigation sidebar: does it collapse on mobile?
- Touch targets: are buttons big enough for fingers?
- Text size: readable without pinch-zoom?
- Horizontal scroll: none on any page?
- City page map: usable on mobile?

---

## Team 5 — Test Engineering
**Complexity:** High
**Priority:** Critical — validates everything else
**Deliverable:** `outputs/testing/shogun-test-plan.md` + Playwright scripts

### Test Category 1: AI Research & Discovery

Every test below is a chat conversation. Test via Playwright or direct API.

```
TEST-R01: Basic location search (known data)
  User: "What restaurants are near our hotel in Tokyo?"
  Expected: AI calls search_trip_knowledge(query="restaurant", city="tokyo")
  Expected: Returns results mentioning Sugamo area
  Pass: Named restaurants with addresses returned

TEST-R02: Location search (unknown — triggers web search)
  User: "Where can I find a good burger near the National Museum in Tokyo?"
  Expected: AI calls search_trip_knowledge → empty
  Expected: AI calls web_search("burger restaurant near Tokyo National Museum Ueno")
  Expected: Real restaurant names with locations returned
  Pass: Specific restaurant names, not "check online"

TEST-R03: Context continuity — same location
  User: "Where can I find a burger near the National Museum?"
  [AI responds with burger places]
  User: "How about ramen?"
  Expected: AI searches for ramen near National Museum / Ueno area
  Expected: NOT near Sugamo (accommodation)
  Pass: Results are in Ueno/museum area, not default accommodation

TEST-R04: Context continuity — explicit location change
  User: "Find me ramen near Ueno"
  [AI responds]
  User: "Actually, what about near our Osaka Airbnb?"
  Expected: AI now searches near Tenjinbashi area
  Pass: Results reference Osaka/Tenjinbashi, not Ueno

TEST-R05: Osaka restaurant search (knowledge seeded)
  User: "Best takoyaki in Osaka?"
  Expected: search_trip_knowledge returns Osaka results
  Pass: Named takoyaki spots with locations

TEST-R06: Kanazawa search (knowledge seeded)
  User: "Where should we eat in Kanazawa?"
  Expected: search_trip_knowledge returns Kanazawa restaurants
  Pass: Named restaurants near Omicho Market area

TEST-R07: Interest-based search
  User: "Best vintage clothing shops in Tokyo"
  Expected: Knowledge base has vintage/Tokyo records
  Pass: Named shops (Shimokitazawa, etc.) with details

TEST-R08: Pharmacy/practical search
  User: "Is there a pharmacy near our Osaka apartment?"
  Expected: Returns drugstores near Tenjinbashisuji
  Pass: Named pharmacy with walking distance

TEST-R09: Transit question
  User: "How do I get from our hotel in Tokyo to Ghibli Museum?"
  Expected: AI knows Sugamo → Mitaka route
  Pass: Specific line names, transfer points, time estimate

TEST-R10: Web search auto-save verification
  User: "Find me craft beer bars in Osaka"
  [AI does web_search, returns results]
  Wait 5 seconds.
  User: "Search again for craft beer in Osaka"
  Expected: search_trip_knowledge now returns saved results from first search
  Pass: Results found in knowledge base without web search
```

### Test Category 2: Itinerary Management

```
TEST-I01: Read itinerary for specific date
  User: "What's planned for March 25th?"
  Expected: AI calls get_itinerary_legs(date="2026-03-25")
  Pass: Returns Nara day trip details

TEST-I02: Read itinerary for city
  User: "What are we doing in Kanazawa?"
  Expected: AI calls get_itinerary_legs(city="kanazawa")
  Pass: Returns Hotel Sanraku + transit legs

TEST-I03: Create new itinerary leg
  User: "Add ramen at Ichiran on April 5th for lunch"
  Expected: AI calls create_itinerary_leg(title="Ramen at Ichiran",
    date="2026-04-05", city="tokyo", leg_type="restaurant")
  Pass: Leg created, AI confirms with details

TEST-I04: Add note to existing leg
  User: "Add a note to the Nara trip: bring cash for deer crackers"
  Expected: AI calls get_itinerary_legs first to find Nara leg ID
  Expected: AI calls update_itinerary_leg with notes
  Pass: Note added to correct leg (Nara, not random)

TEST-I05: Delete a leg
  User: "Cancel the Ichiran ramen on April 5"
  Expected: AI calls get_itinerary_legs to find the leg
  Expected: AI asks for confirmation before deleting
  User: "Yes, delete it"
  Expected: AI calls delete_itinerary_leg
  Pass: Leg removed from DB

TEST-I06: Move a leg to different date
  User: "Move the Ueno museum trip to April 7 instead"
  Expected: AI calls get_itinerary_legs to find Ueno leg
  Expected: AI calls update_itinerary_leg with new date
  Pass: Leg now on April 7, no longer on April 2

TEST-I07: Find open days
  User: "What days do we have free in Tokyo?"
  Expected: AI calls get_trip_overview or get_itinerary_legs
  Pass: Lists specific dates with no legs (Apr 7, Apr 8 currently)

TEST-I08: Schedule from research
  User: "Find me a good sushi place in Kanazawa"
  [AI searches, returns results]
  User: "Add the first one to March 31st for dinner"
  Expected: AI creates leg with the restaurant from search results
  Pass: Leg created with restaurant name, city=kanazawa, date correct

TEST-I09: Multi-step trip planning
  User: "Help me plan April 7th in Tokyo. I want to go shopping in the
    morning and find a good restaurant for dinner."
  Expected: AI searches for shopping options, suggests specific places
  Expected: AI searches for dinner options near shopping area
  User: "That sounds great, add both to the calendar"
  Expected: AI creates 2 legs on April 7
  Pass: Both legs created with appropriate times and details

TEST-I10: Read full itinerary
  User: "Show me the complete trip plan"
  Expected: AI calls get_itinerary_legs (no filter)
  Pass: All 17+ legs listed, organized by date
```

### Test Category 3: Calendar & Itinerary Integration

```
TEST-C01: Calendar reflects AI changes
  1. Via AI chat: "Add temple visit on April 8"
  2. Navigate to /calendar
  Expected: April 8 tile shows the new temple visit leg
  Pass: Calendar page reflects the change without refresh

TEST-C02: Planning page reflects AI changes
  1. Via AI chat: "Add shopping in Akihabara on April 7"
  2. Navigate to /planning
  Expected: April 7 row shows the new leg
  Pass: Planning timeline reflects the change

TEST-C03: Print page shows all legs
  1. Add 2 new legs via AI chat
  2. Navigate to /itinerary/print
  Expected: Both new legs appear in print view
  Pass: Print view has all legs including recently added

TEST-C04: Delete via AI, calendar updates
  1. Via AI: "Delete the Akihabara shopping on April 7"
  2. Navigate to /calendar
  Expected: April 7 no longer shows Akihabara
  Pass: Calendar accurately reflects deletion
```

### Test Category 4: AI Behavioral Quality

```
TEST-B01: Never says "I don't know" without searching
  User: "Where can I buy a good knife in Osaka?"
  Pass: AI searches knowledge base AND/OR web — gives specific answer
  Fail: "I don't have information about knife shops"

TEST-B02: Includes Japanese text when relevant
  User: "What's the address of our Tokyo Airbnb?"
  Pass: Returns both English and Japanese address
  Fail: English only or "I don't know the address"

TEST-B03: Currency in yen
  User: "How much does the Tokyo National Museum cost?"
  Pass: "¥1,000 general admission" or similar
  Fail: Dollar amounts or "check the website"

TEST-B04: Practical transit advice
  User: "How do I get to USJ from our Osaka place?"
  Pass: Specific stations, lines, transfer points, time
  Fail: "Take the train to Universal City station"

TEST-B05: Knows accommodation details
  User: "What's the closest station to our Kanazawa hotel?"
  Pass: "Kanazawa Station, about a 10 minute walk"
  Fail: "I'm not sure where you're staying in Kanazawa"

TEST-B06: Date awareness
  User: "What day is the Ghibli Museum?"
  Pass: "April 3rd, with a timed entry at noon"
  Fail: "I'd need to check the itinerary"

TEST-B07: Proactive safety info
  User: "We're going to USJ with the kids"
  Pass: Mentions opening time, express pass recommendation, transit
  Fail: Generic "have fun" response

TEST-B08: Handles ambiguity
  User: "Move dinner to Thursday"
  Expected: AI identifies which dinner and which Thursday
  Expected: If ambiguous, asks for clarification
  Pass: Either moves correct leg or asks which one
  Fail: Moves wrong leg or errors out

TEST-B09: Multi-city awareness
  User: "Compare our food options in Osaka vs Kanazawa"
  Pass: Searches both cities, presents comparison
  Fail: Only searches one city

TEST-B10: Confirmation on destructive actions
  User: "Delete everything on April 5"
  Expected: AI lists what's on April 5, asks "are you sure?"
  Pass: Does NOT delete without confirmation
  Fail: Silently deletes
```

### Test Category 5: UI / Visual Audit

```
TEST-U01: Landing page logo visibility
  Navigate to / at 1440px, 1024px, 768px, 390px
  Pass: Logo fully visible at all widths
  Fail: Logo cropped or invisible

TEST-U02: Landing page Enter button
  Navigate to / at 390px (mobile)
  Pass: Button clearly visible, tappable, leads to /dashboard
  Fail: Button obscured, too small, or missing

TEST-U03: Dashboard — no white banners
  Navigate to /dashboard
  Pass: All tiles have correct background, no white rectangles
  Fail: Any tile has background:white or visible box-shadow that looks wrong

TEST-U04: Dashboard — all tiles render data
  Navigate to /dashboard, wait 10s
  Pass: Weather, sakura, exchange rate, transit all show data (not "Loading...")
  Fail: Any tile stuck in loading state

TEST-U05: Calendar — all 18 days visible
  Navigate to /calendar
  Pass: Mar 23 through Apr 9 all visible, scrollable
  Fail: Missing days or rendering errors

TEST-U06: Calendar — legs show content
  Navigate to /calendar
  Pass: Days with legs show title + type label + description (non-compact)
  Fail: Legs show only title or are empty

TEST-U07: Chat — message round trip
  Navigate to /chat, type "Hello", submit
  Pass: User message appears, AI response appears within 30s
  Fail: No response, error, or timeout

TEST-U08: Chat — tool badge display
  Ask AI: "What's on March 25?"
  Pass: Response shows tool action badge (e.g., "✓ Read itinerary")
  Fail: No badge despite tool being called

TEST-U09: Planning page — POI browser
  Navigate to /planning
  Pass: POIs load for all cities, filter dropdown works
  Fail: "Loading POIs..." persists or filter doesn't change results

TEST-U10: Planning page — timeline
  Navigate to /planning, wait 5s
  Pass: Trip timeline shows legs on correct dates
  Fail: All days show "No legs scheduled"

TEST-U11: City page — Tokyo
  Navigate to /city/tokyo
  Pass: Ghibli countdown, weather widget, POI cards, map loads
  Fail: Any section missing or errored

TEST-U12: City page — Osaka
  Navigate to /city/osaka
  Pass: Weather, POI cards, "Places in Osaka" section
  Fail: Missing content or errors

TEST-U13: Print itinerary
  Navigate to /itinerary/print
  Pass: All legs shown, Japanese addresses visible, print-clean layout
  Fail: Missing legs, no Japanese text, nav bar visible in print

TEST-U14: Mobile navigation
  Navigate to /dashboard at 390px
  Pass: Navigation is accessible (hamburger menu or bottom nav)
  Fail: Nav is cut off, overlapping, or unusable

TEST-U15: Checklist toggle
  Navigate to /checklist, toggle an item
  Pass: Item visually changes, persists on page reload
  Fail: Toggle doesn't stick or visual doesn't update
```

### Test Category 6: Knowledge Pipeline Verification

```
TEST-K01: Osaka knowledge exists
  Query: SELECT COUNT(*) FROM knowledge_items WHERE city='osaka'
  Pass: >= 80 records

TEST-K02: Kanazawa knowledge exists
  Query: SELECT COUNT(*) FROM knowledge_items WHERE city='kanazawa'
  Pass: >= 40 records

TEST-K03: Tokyo knowledge exists (baseline)
  Query: SELECT COUNT(*) FROM knowledge_items WHERE city='tokyo'
  Pass: >= 100 records (existing)

TEST-K04: Knowledge search returns restaurant data
  API: search_trip_knowledge(query="restaurant", city="osaka")
  Pass: >= 3 results with content_summary

TEST-K05: Knowledge search returns transit data
  API: search_trip_knowledge(query="train station", city="kanazawa")
  Pass: >= 1 result about Kanazawa transit

TEST-K06: Auto-saved web search results persist
  1. Via AI: search for something not in knowledge_items
  2. Verify web_search fires
  3. Query knowledge_items for the new topic
  Pass: New records exist with source_url and tavily_score

TEST-K07: No duplicate source_urls
  Query: SELECT source_url, COUNT(*) FROM knowledge_items
         GROUP BY source_url HAVING COUNT(*) > 1
  Pass: Zero rows (no duplicates)

TEST-K08: All knowledge items have required fields
  Query: SELECT COUNT(*) FROM knowledge_items
         WHERE city IS NULL OR content_summary IS NULL
  Pass: Zero rows
```

---

## Execution Order & Dependencies

```
WEEK: Mar 17–22 (6 days to departure)

DAY 1 (Mar 17-18):
  ├── Team 1 Phase 1A: System prompt rewrite
  ├── Team 1 Phase 1B: New tools (create, delete, web_search)
  └── Team 2 Phase 2A: Osaka knowledge seeding (parallel)

DAY 2 (Mar 18-19):
  ├── Team 1 Phase 1C: Context tracking
  ├── Team 1 Phase 1D: Search protocol rules
  ├── Team 2 Phase 2B: Kanazawa knowledge seeding
  └── Team 2 Phase 2C: Auto-save in web_search

DAY 3 (Mar 19-20):
  ├── Team 3 Phase 3A: API expansion (PATCH fields, GET filtering)
  ├── Team 3 Phase 3B: Trip overview tool
  ├── Team 3 Phase 3C: Printable itinerary page
  └── Team 4 Phase 4A: Landing page logo fix

DAY 4 (Mar 20-21):
  ├── Team 5: Execute ALL test categories (R, I, C, B, U, K)
  ├── Team 4 Phase 4B: Full page Playwright audit
  └── Team 4 Phase 4C: Mobile polish

DAY 5 (Mar 21-22):
  ├── Fix all failures from Day 4 testing
  ├── Re-run failed tests
  ├── Final knowledge re-run (refresh all cities)
  └── Push to origin/develop, merge to main

DAY 6 (Mar 22):
  ├── Final green audit — all tests pass
  ├── Print itinerary (physical copy)
  ├── Laptop reliability config (power, Docker auto-start)
  └── Cloudflare + Google login integration (Todd)
```

---

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Gemini function calling unreliable with 10 tools | Medium | High | Test each tool individually. If >8 tools causes issues, consolidate into fewer multi-purpose tools |
| Tavily rate limiting during seeding | Low | Medium | Add delays between queries. Use basic search depth. Budget: ~$5 for full seeding |
| System prompt too long for Gemini context | Medium | Medium | Keep prompt under 2000 tokens. Move static data (accommodations) to a separate block that can be truncated |
| AI deletes legs without confirmation | Low | High | System prompt rule + code guard: delete tool always returns "confirm?" first |
| Knowledge items have stale/wrong data | Medium | Low | Tavily scores filter quality. Web search data is supplementary, not authoritative |
| Print page doesn't render Japanese characters | Low | Medium | Test with actual JP addresses. Use system fonts (Noto Sans JP) |
| Docker Desktop crash during testing | Low | High | Commit frequently. All test scripts idempotent. |

---

## Success Criteria — "Green Status"

ALL of the following must be true:
- [ ] Test categories R (10), I (10), C (4), B (10), U (15), K (8) = 57 tests ALL PASS
- [ ] Knowledge items: Tokyo 100+, Osaka 80+, Kanazawa 40+
- [ ] AI never says "I don't have information" without searching first
- [ ] AI creates, updates, and deletes itinerary legs correctly
- [ ] AI maintains location context across 3+ messages
- [ ] Printable itinerary exists with Japanese addresses
- [ ] Logo visible on landing page at all viewports
- [ ] No console errors on any page
- [ ] All pages render correctly on mobile (390px)
- [ ] All commits pushed to origin/develop
- [ ] develop merged to main
