# Shogun Web Chat — Tool Test Plan
Date: 2026-03-19
Status: Draft

## Purpose

Verify that every tool available to the Shogun AI chat assistant is correctly
invoked by Gemini in response to appropriate user prompts, and that responses
contain the expected content. Tests run against the live chat API at
`http://localhost:8090` with `SHOGUN_BYPASS_AUTH=true`.

A test PASSES only when:
1. The `tool_actions` array in the API response contains the expected tool name
2. The response text contains the expected content elements
3. No fallback to incorrect tools occurred

---

## Test Environment

- **Endpoint:** `POST http://localhost:8090/chat`
- **Auth:** `SHOGUN_BYPASS_AUTH=true` — no token required
- **Containers required:** shogun-web-api, platform-places-google, platform-tavily, platform-postgres, platform-valkey
- **Test runner:** `tools/test_chat_tools.py`
- **Report output:** `outputs/validation/YYYY-MM-DD_chat-tool-tests_report.md`

---

## Test Cases

### TC-01: find_nearby_places — proximity query with anchor

**Prompt:**
```
Find 3 places that sell data SIM cards within 10 minute walk of my osaka airbnb.
Give me the name, address, and a Google Maps link for each.
```

**Expected tool called:** `find_nearby_places`
**Must NOT call:** `web_search` as primary response (web_search is allowed as fallback only)

**Response must contain:**
- At least 2 place names (real business names, not generic "convenience store")
- At least 2 street addresses (must contain "Osaka" or Japanese address characters)
- At least 1 Google Maps URL (`maps.google.com` or `google.com/maps`)

**FAIL conditions:**
- `tool_actions` contains only `web_search` and not `find_nearby_places`
- Response says "I cannot provide Google Maps links" or similar
- Response gives only generic advice ("try Family Mart") without real addresses
- `find_nearby_places` appears in tool_actions but Places gateway returned an error

---

### TC-02: find_nearby_places — implicit current accommodation

**Prompt:**
```
What pharmacies are within 5 minute walk of my hotel?
```

**Expected tool called:** `find_nearby_places`
**Expected anchor resolved:** current city accommodation (osaka-airbnb, kanazawa-hotel, or tokyo-sugamo depending on date)

**Response must contain:**
- At least 1 real pharmacy name
- At least 1 address
- Walking time reference (e.g., "3 min", "5 min")

**FAIL conditions:**
- Tool not called, bot answers from memory alone
- Anchor coordinates resolve to wrong city

---

### TC-03: search_trip_knowledge — knowledge base query

**Prompt:**
```
What ramen restaurants do you have in our knowledge base for Tokyo?
```

**Expected tool called:** `search_trip_knowledge`
**Must NOT call:** `find_nearby_places` or `web_search`

**Response must contain:**
- At least 1 restaurant name (from knowledge_items table)
- City context (Tokyo)

**FAIL conditions:**
- Tool not called
- Returns "no results found" when knowledge_items has Tokyo food records

---

### TC-04: web_search — current event query (no knowledge base hit)

**Prompt:**
```
What is the current sakura bloom status in Osaka right now?
```

**Expected tool called:** `web_search`
**Acceptable:** `search_trip_knowledge` called first, then `web_search`

**Response must contain:**
- Some mention of cherry blossom / sakura status
- Reference to 2026 or current conditions

**FAIL conditions:**
- Neither tool called, bot answers from training data alone
- Response is clearly stale (references wrong year)

---

### TC-05: get_itinerary_legs — calendar read

**Prompt:**
```
What is planned for March 25?
```

**Expected tool called:** `get_itinerary_legs`

**Response must contain:**
- Reference to Nara (the planned activity for Mar 25)
- Specific activity detail (deer park, Todai-ji, or similar)

**FAIL conditions:**
- Tool not called
- Returns empty or "nothing scheduled" when Nara day trip is in the DB

---

### TC-06: get_trip_overview — free days query

**Prompt:**
```
Which days in Tokyo are still open and have nothing planned?
```

**Expected tool called:** `get_trip_overview`

**Response must contain:**
- Reference to April dates
- Identification of open days (Apr 7-8 are expected open)

**FAIL conditions:**
- Tool not called
- Returns incorrect free days

---

### TC-07: create_itinerary_leg — calendar write

**Prompt:**
```
Add "Dotonbori evening walk" to March 28.
```

**Expected tool called:** `create_itinerary_leg`

**Response must contain:**
- Confirmation that the leg was added
- Reference to March 28 and Dotonbori

**FAIL conditions:**
- Tool not called
- Tool called but returns DB error
- Bot says it cannot add to the calendar

**Cleanup:** Test runner must delete this entry after test via direct DB call.

---

### TC-08: update_itinerary_leg — calendar edit

**Prompt:**
```
Add a note to the Nara day trip: bring yen cash for deer crackers
```

**Expected tools called:** `get_itinerary_legs` (to find leg_id), then `update_itinerary_leg`

**Response must contain:**
- Confirmation the note was added
- Reference to Nara

**FAIL conditions:**
- Neither tool called
- update called without get first (no leg_id)
- DB error on update

**Cleanup:** Test runner must revert the note after test.

---

### TC-09: delete_itinerary_leg — requires confirmation

**Prompt (turn 1):**
```
Delete the Nara day trip from the calendar.
```

**Expected behavior turn 1:** Bot asks for confirmation. Must NOT call `delete_itinerary_leg` yet.

**Prompt (turn 2):**
```
Yes, delete it.
```

**Expected tool called on turn 2:** `delete_itinerary_leg`

**FAIL conditions:**
- Bot deletes without asking first
- Bot refuses to delete even after confirmation
- Wrong leg deleted

**Cleanup:** Test runner must re-insert Nara leg after test.

---

### TC-10: get_checklist_items — packing list read

**Prompt:**
```
Show me my packing checklist
```

**Expected tool called:** `get_checklist_items`

**Response must contain:**
- At least 3 checklist item names
- Some indication of packed/unpacked status

**FAIL conditions:**
- Tool not called
- Returns empty list when checklist_items has 15 seeded records

---

### TC-11: toggle_checklist_item — packing list update

**Prompt:**
```
Mark passport as packed
```

**Expected tool called:** `toggle_checklist_item`

**Response must contain:**
- Confirmation that passport is now marked packed

**FAIL conditions:**
- Tool not called
- Item not found (passport should be in checklist_items)
- DB error

**Cleanup:** Test runner must reset packed status after test.

---

### TC-12: get_trip_pois — POI browse

**Prompt:**
```
Show me points of interest in Tokyo
```

**Expected tool called:** `get_trip_pois`

**Response must contain:**
- At least 2 Tokyo POI names
- City reference

**FAIL conditions:**
- Tool not called
- Empty result when trip_pois has tokyo records

---

### TC-13: Google Maps link construction — no tool needed

**Prompt:**
```
Send me a Google Maps link for Kenroku-en garden in Kanazawa
```

**Expected behavior:** Bot constructs and includes a Google Maps URL directly.
**No tool call required** — bot should know the URL formula.

**Response must contain:**
- A URL containing `maps.google.com` or `google.com/maps`
- Reference to Kenroku-en

**FAIL conditions:**
- Bot says "I cannot provide Google Maps links"
- Bot says it lacks the capability

---

### TC-14: find_nearby_places — non-Osaka anchor

**Prompt:**
```
Find a convenience store within 5 minute walk of our Tokyo accommodation
```

**Expected tool called:** `find_nearby_places`
**Expected anchor:** `tokyo-sugamo`

**Response must contain:**
- At least 1 real convenience store name
- Tokyo/Sugamo area address
- Google Maps link

---

### TC-15: Tool fallback chain — Places fails, web_search covers

**Setup:** Temporarily stop the places gateway
**Prompt:**
```
Find a drugstore near my osaka airbnb
```

**Expected behavior:**
- `find_nearby_places` called first, returns error
- `web_search` called as fallback
- Response gives some useful answer (not an error message to the user)

**Restore:** Restart places gateway after test.

---

## Pass/Fail Criteria

| # | Test | Tool Required | Maps Link | Min Results |
|---|------|--------------|-----------|-------------|
| TC-01 | SIM card near Osaka Airbnb | find_nearby_places | YES | 2 places |
| TC-02 | Pharmacy near accommodation | find_nearby_places | optional | 1 place |
| TC-03 | Tokyo ramen in knowledge base | search_trip_knowledge | NO | 1 result |
| TC-04 | Sakura status | web_search | NO | current info |
| TC-05 | March 25 itinerary | get_itinerary_legs | NO | Nara |
| TC-06 | Free days in Tokyo | get_trip_overview | NO | Apr 7-8 |
| TC-07 | Create Dotonbori leg | create_itinerary_leg | NO | confirmation |
| TC-08 | Update Nara note | get_legs + update_leg | NO | confirmation |
| TC-09 | Delete with confirmation | delete (after confirm) | NO | no premature delete |
| TC-10 | Show checklist | get_checklist_items | NO | 3+ items |
| TC-11 | Mark passport packed | toggle_checklist_item | NO | confirmation |
| TC-12 | Tokyo POIs | get_trip_pois | NO | 2+ POIs |
| TC-13 | Maps link Kenroku-en | none | YES | URL present |
| TC-14 | Convenience store Tokyo | find_nearby_places | YES | 1 place |
| TC-15 | Places fallback to web | web_search fallback | NO | useful answer |

**GREEN:** All 15 tests pass.
**YELLOW:** TC-01, TC-02, TC-13, TC-14 pass (the broken ones). Remainder may be deferred.
**RED:** TC-01 or TC-13 fail (core feature broken).

---

## Test Runner Design

`tools/test_chat_tools.py`

- Calls `POST http://localhost:8090/chat` for each prompt
- Extracts `tool_actions` from response to verify tool selection
- Checks `response` text for required content strings
- Clears conversation history between tests via `DELETE http://localhost:8090/chat/history`
- Reports PASS/FAIL per test with actual vs expected tool_actions
- Writes results to `outputs/validation/YYYY-MM-DD_chat-tool-tests_report.md`
- Returns exit code 1 if any test fails (RED conditions above)
