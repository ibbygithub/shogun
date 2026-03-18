# Reddit Gateway — First Use Validation Report
Date: 2026-03-15
Task: Validate Reddit gateway functionality + retrieve Nara deer park and Osaka restaurant intel
Status: GATEWAY OPERATIONAL — Search behavior documented

---

## Gateway Health

| Check | Result |
|-------|--------|
| Container | platform-reddit-gateway — Up 3+ hours |
| Host port | 8083 → container 8082 |
| Health endpoint | ✅ `{"ok":true}` |
| Version | 2.0.0 |
| DB connected | ✅ true |
| Persistence | ✅ enabled |
| Embeddings | OpenAI text-embedding-3-small |
| Cache TTL | 1 hour |
| Reddit agent | ibbytech-platform-reddit-gateway/2.0 (by /u/ananda-ibby) |

---

## API Endpoints Available

| Endpoint | Description |
|----------|-------------|
| `POST /v1/reddit/search` | Search Reddit (with optional subreddit filter) |
| `POST /v1/reddit/subreddit/posts` | Get top/hot/new posts from a subreddit |
| `GET /v1/reddit/post/{post_id}` | Fetch full post content + comments |
| `GET /v1/reddit/subreddit/{name}/info` | Subreddit metadata |
| `POST /v1/reddit/saved/search` | Search cached/saved content |
| `GET /v1/reddit/feeds` | List saved feeds |

---

## Search Behavior Findings

**Critical finding:** General search (no subreddit) returns globally top-voted posts
regardless of query relevance. A search for "Nara deer park" returns r/lifehacks and
r/MaliciousCompliance viral posts. This is a Reddit API limitation — the default sort
by popularity overwhelms relevance for niche queries.

**Working pattern:** Subreddit-specific search returns on-topic results.
Always use the `subreddit` parameter for travel research queries.

| Pattern | Behavior |
|---------|----------|
| `{"query": "...", "sort": "top"}` (global) | Returns viral posts, ignores topic relevance |
| `{"query": "...", "subreddit": "JapanTravel", "sort": "relevance"}` | Returns relevant Japan travel content |
| `GET /v1/reddit/post/{id}` | Returns full text; comments only populated if gateway has cached them |

**Recommended subreddits for Shogun queries:**
- `JapanTravel` — trip reports, advice, itinerary feedback
- `OsakaTravel` — local Osaka food, events, day trips
- `osaka` — resident/local perspective on food and neighborhoods
- `japan` — broader Japan culture and practical tips

---

## Nara Deer Park — Reddit Intelligence

Compiled from 5+ r/JapanTravel trip reports (all 2023-2025).

### Key Tips from Reddit

**Logistics:**
- Train from Osaka: 45 min (Kintetsu Limited Express from Namba, ¥680). Faster than JR.
- Best timing: Arrive by 9am to beat crowds at Todaiji. Crowds peak 11am-2pm.
- Avoid weekends for smaller crowds at Todaiji temple
- Full experience = half day minimum; full day if doing the park + Nara-machi

**The Deer:**
- Wild Sika deer roam freely through the park — not domesticated
- Senbei crackers (vendor-sold, ~¥200/pack) — deer will bow to ask for them and mob
  you when you hold up the packet. Entertaining and worth doing once.
- **Watch your bags and map printouts** — deer will eat paper, wrappers, anything.
  Multiple posters report deer stealing food, bags, tickets. Keep belongings close.
- Spring (March-April) = deer + cherry blossoms simultaneously = peak experience
- Deer are especially active in the morning

**Main Attractions (walk order):**
1. **Nandaimon Gate** (entrance) — massive wooden gate with guardian statues
2. **Todaiji** (Great Buddha Hall) — world's largest wooden building; ¥600 entry;
   deer graze on the lawn in front; arrive early
3. **Kasuga Taisha Shrine** — 15 min walk from Todaiji; lantern-lined paths through
   ancient cedar forest; atmospheric, less crowded than Todaiji
4. **Isuien Garden** — Japanese strolling garden adjacent to Todaiji; calm refuge
   from deer chaos; modest entry fee; highly recommended by multiple posters
5. **Nara-machi** (merchant district) — 10 min south of park; traditional machiya
   townhouses; good for lunch, local craft shops, mochi sweets

**Food near the park:**
- Sakura Burger mentioned in one trip report — local burger spot near park
- Nara-machi has multiple lunch spots (udon, soba, tofu cuisine — Nara is famous for tofu)
- Nakatanido mochi pounding — famous mochi shop on route to Nara-machi; watch them
  pound mochi by hand, buy fresh. High energy entertainment.

**What Reddit says NOT to do:**
- Don't skip Kasuga Taisha just to leave early — the forest path is a highlight
- Don't expect Nara to be a full-day destination — most posters do it in 4-5 hours
  and combine with Himeji or another stop

**Our trip context:** We arrive Osaka Mar 23. Nara is confirmed Day 1 (per itinerary
reminder: "Nara deer warnings, Todaiji passport reminder"). Early start on Mar 23
recommended — get the senbei crackers before they sell out at peak hour.

---

## Osaka Restaurants near Tenjinbashisuji Airbnb — Reddit Intelligence

Compiled from r/OsakaTravel and r/osaka (2021-2025).

### The Tenjinbashisuji Area

Tenjinbashisuji Shopping Street is Japan's longest covered arcade (2.6km).
This is a locals' district — not the tourist circuit. Prices are significantly
lower than Dotonbori/Namba. Many small family-run izakaya, casual lunch spots,
and local food stalls line the arcade and its side streets.

**This is good news for our Airbnb location** — the immediate area has authentic
local dining without tourist markup.

### Restaurant Recommendations from Reddit (sorted by proximity/type)

**On or near Tenjinbashisuji arcade:**
- The arcade itself has dense food options — walk the stretch, look for shops
  with queues of locals. Takoyaki, kushikatsu, and set-lunch spots are abundant.
- Side streets off the arcade (横丁 *yokocho* alleys): small izakaya, counter
  dining, yakitori — best for evening meal without Dotonbori crowds

**Nakanoshima (~15 min walk/bus):**
- Riverside island between the Dojima and Tosabori rivers
- Described on r/OsakaTravel as Osaka's "sophisticated side" — red brick buildings,
  riverside park, less crowded than tourist zones
- Restaurant variety: French bistros, Japanese kaiseki, casual cafes
- Great for a sit-down dinner or lunch away from the arcade

**Shinsekai (~20-25 min south by subway):**
- Kushikatsu heartland — deep-fried skewers on sticks; the classic Osaka experience
- **Nonkiya** in Shinsekai: local favorite — doteyaki (beef tendon) and oden with drinks
- Full kushikatsu street crawl recommended for Day 1-2 of Osaka stay

**From local taxi driver Taka (r/OsakaTravel regular poster):**
- Gyoza no Ohsho: described as "very popular" chain with quality gyoza, ramen,
  fried rice. Multiple locations. Good for casual lunch or fast dinner.
- Healthy options: konbini (7-Eleven, Lawson) for breakfast and convenience meals
  explicitly called out as surprisingly good and significantly underrated by tourists

**Yakiniku:**
- r/OsakaTravel post lists 10 yakiniku spots under ¥10,000/person near major areas
- North Osaka (near our Airbnb area) has several options in this list

### Primary Recommendation

**First night in Osaka:** Walk Tenjinbashisuji arcade south to north, pick any
izakaya with a visible queue of locals. Ramen, izakaya set meals, and yakitori
are all authentic at local prices.

**Destination dinner:** Nakanoshima for a more planned evening — less crowded,
riverside atmosphere, more variety.

**Day trip food (Nara first day):** Pre-stock senbei crackers for deer engagement.
Lunch in Nara-machi after Todaiji. Return to Osaka for evening meal.

---

## Gateway Assessment for Shogun Integration

| Use Case | Viability |
|----------|-----------|
| Japan travel tips (r/JapanTravel) | ✅ Excellent — rich trip reports, specific advice |
| Local food recommendations (r/osaka, r/OsakaTravel) | ✅ Good — local voices, current (2024-2025) |
| Transit tips (r/JapanTravel) | ✅ Good — many posts on IC cards, train specifics |
| Event/festival info | ⚠️ Moderate — content varies, date-scoping needed |
| General search (no subreddit) | ❌ Broken for relevance — always use subreddit filter |

**Integration recommendation for knowledge_items pipeline:**
When loading Shogun's knowledge base, use the Reddit gateway with:
1. `subreddit: "JapanTravel"` for general Japan tips and city-level content
2. `subreddit: "OsakaTravel"` / `"osaka"` for Osaka-specific local intel
3. `subreddit: "JapanTravel"` + relevant city/POI keyword for anchor-scoped content
4. `sort: "relevance"` with targeted queries for specific POI research
5. Post content (`GET /v1/reddit/post/{id}`) for deep extraction of long trip reports

**NOT suitable for:** Real-time transit disruptions, current cherry blossom status
(Tavily is better for these). Reddit content is 1-3 years old on average.

---

## Open Items / Follow-up

- Reddit gateway comment retrieval: Comments are not populated in search results —
  only available via `GET /v1/reddit/post/{id}` after cache warms up. Full trip
  report comments often have the most specific advice.
- Subreddit: `r/NaraPark` or `r/Nara` may exist — not tested this session
- Consider a dedicated bulk load of r/JapanTravel top-100 posts into knowledge_items
  once the data lake pipeline is built (Tuesday taxonomy session)
- `sort: "relevance", time_filter: "year"` is the best combination for current advice
