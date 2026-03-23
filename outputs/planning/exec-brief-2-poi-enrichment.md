# Execution Brief 2 — POI Enrichment Pipeline

**Agent:** Coding agent on laptop (Windows 11 control plane)
**Target execution:** Script runs inside `shogun-web-api` container on brainnode-01 via `docker cp` + `docker exec`
**Estimated time:** 2.5 hours coding + 30 min execution
**Dependencies:** Brief 1 (DB schema) must be complete first

---

## Task

Build `tools/enrich_poi_guides.py` — a script that enriches ALL trip_pois with rich guide data by calling Google Places, Tavily, and Gemini LLM, then storing results in the `poi_guides` table.

Then update the Web UI and API to display the enriched guides.

---

## Part A: Enrichment Script

### File to create: `C:\git\work\shogun\tools\enrich_poi_guides.py`

### Architecture

For each of the ~111 trip_pois:
1. **Classify** POI type from name + category
2. **Google Places** — search by name + city → get hours, photos, rating, URL
3. **Tavily** — search for "[name] [city] guide tips" → web context + images
4. **Gemini LLM** — synthesize all data into structured guide sections
5. **Store** in poi_guides table

### Environment Variables (available in shogun-web-api container)

```
DATABASE_URL=postgresql://shogun_app:PASSWORD@192.168.71.221/shogun_v1
TAVILY_GATEWAY_URL=http://platform-tavily:8084        # Container name on platform_net
PLACES_GATEWAY_URL=http://192.168.71.220:8081          # svcnode-01 direct IP (not on same Docker network)
LLM_GATEWAY_URL=http://platform-llm-gateway:8080       # Container name on platform_net
```

**IMPORTANT:** The shogun-web-api container is on brainnode-01 but connects to svcnode-01 gateways. Platform container names (platform-tavily, platform-llm-gateway) are NOT resolvable from brainnode-01. Use FQDNs or direct IPs instead:
- Tavily: `https://tavily.platform.ibbytech.com/v1/search` OR `http://192.168.71.220:8084/v1/search`
- LLM: `https://llm.platform.ibbytech.com/v1/chat` OR `http://192.168.71.220:8080/v1/chat`
- Places: `http://192.168.71.220:8081/v1/places/search_text`

### API Endpoint Formats

#### Tavily Search
```python
resp = httpx.post(
    "http://192.168.71.220:8084/v1/search",
    json={
        "query": "Senso-ji Asakusa Tokyo visitor guide hours tips 2026",
        "max_results": 5,
        "search_depth": "basic",
        "include_images": True,
    },
    timeout=30,
)
# Response: {"results": [{"title": "...", "content": "...", "url": "...", "score": 0.92}], "images": ["url1", ...]}
```

#### Google Places Text Search
```python
resp = httpx.post(
    "http://192.168.71.220:8081/v1/places/search_text",
    json={
        "text_query": "Senso-ji Temple Asakusa Tokyo",
        "lat": 35.7148,    # Optional but improves results
        "lng": 139.7967,
        "radius_m": 500,
        "max_results": 1,  # We want the canonical result
        "language_code": "en",
        "region_code": "JP",
    },
    timeout=10,
)
# Response: {"ok": true, "data": {"places": [{"displayName": {"text": "..."}, "formattedAddress": "...",
#   "rating": 4.5, "googleMapsUri": "...", "regularOpeningHours": {...},
#   "photos": [{"name": "places/...", "heightPx": 4032, "widthPx": 3024}],
#   "location": {"latitude": 35.7148, "longitude": 139.7967}}]}}
```

#### LLM Gateway (Gemini 2.0 Flash)
```python
resp = httpx.post(
    "http://192.168.71.220:8080/v1/chat",
    json={
        "provider": "google",
        "model": "gemini-2.0-flash",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "max_output_tokens": 1200,
    },
    timeout=25,
)
# Response: {"output_text": "...", "provider": "google", "model": "gemini-2.0-flash"}
```

### POI Type Classification

Classify each POI into one of these types based on name + category:

```python
TYPE_KEYWORDS = {
    "museum":             ["museum", "gallery", "art"],
    "shrine":             ["shrine", "jinja"],
    "temple":             ["temple", "ji", "dera", "kannon"],
    "shopping_district":  ["shopping", "street", "market", "mall", "store", "shop", "dori", "yokocho"],
    "park":               ["park", "garden", "gyoen", "koen"],
    "landmark":           ["tower", "building", "castle", "observatory", "crossing", "billboard"],
    "neighborhood":       ["district", "area", "neighborhood", "chaya", "town"],
    "restaurant":         ["restaurant", "cafe", "bakery", "ramen", "food", "cream puff"],
    "event":              ["studios", "samurai", "chiikawa"],
}
```

### LLM Prompt Templates

Use a type-specific system prompt. Example for museums:

```python
SYSTEM_PROMPT_MUSEUM = """You are a Japan travel expert writing a concise visitor guide.
Write in a warm, practical tone. Be specific — include real details, not generic advice.
Output EXACTLY this JSON structure (no markdown, no code fences):
{
  "overview": "2-3 sentences: what this place is and why it matters",
  "why_go": "Who should visit and what interests it serves (art, history, family, anime, etc.)",
  "whats_there": "Key exhibits, floors, areas, or highlights visitors should know about",
  "hours_info": "Operating hours, closed days, seasonal variations. Say 'Unknown' if not available.",
  "admission_info": "Entry cost, ticket types, reservations needed. Say 'Unknown' if not available.",
  "time_estimate": "One of: quick_stop (under 30min), standard_visit (1-2hr), deep_visit (2-4hr)",
  "transit_info": "Nearest station(s), walk time, useful train lines",
  "tips": "2-3 practical tips: best time to visit, crowd avoidance, cash/card, photo spots",
  "trip_context": "Why this fits a March-April 2026 Japan trip for a family of 3 (tech-lover dad, shopping/skincare mom, anime-fan teen)"
}"""
```

Create similar prompts for each type. The key difference per type:
- **shrine/temple**: Add etiquette notes, seasonal events, prayer customs
- **shopping_district**: Emphasize store highlights, what to buy, price ranges, opening times
- **park/garden**: Seasonal features (sakura late March!), walking routes, photo spots
- **restaurant/cafe**: Signature dishes, reservation needs, wait times, menu language
- **landmark**: Viewing times, free vs paid, night vs day, photo angles
- **neighborhood**: Walking route, hidden gems, atmosphere, pairing with nearby POIs

### User Prompt for LLM

```python
user_prompt = f"""Generate a visitor guide for: {poi_name}
City: {city}
Category: {category}

Here is what Google Places knows about it:
{places_json_snippet}

Here is what web search found:
{tavily_snippets}

Date context: The family visits on {visit_date} (late March / early April 2026).
Write the guide as the JSON structure specified in your instructions."""
```

### Database Insert

```python
INSERT_SQL = """
INSERT INTO poi_guides (
    trip_poi_id, poi_type, overview, why_go, whats_there,
    hours_info, admission_info, time_estimate, transit_info,
    tips, trip_context, photos, official_url, sources,
    hours_verified, completeness
) VALUES (
    %s, %s, %s, %s, %s,
    %s, %s, %s, %s,
    %s, %s, %s::jsonb, %s, %s::jsonb,
    %s, %s
)
ON CONFLICT (trip_poi_id) DO UPDATE SET
    poi_type = EXCLUDED.poi_type,
    overview = EXCLUDED.overview,
    why_go = EXCLUDED.why_go,
    whats_there = EXCLUDED.whats_there,
    hours_info = EXCLUDED.hours_info,
    admission_info = EXCLUDED.admission_info,
    time_estimate = EXCLUDED.time_estimate,
    transit_info = EXCLUDED.transit_info,
    tips = EXCLUDED.tips,
    trip_context = EXCLUDED.trip_context,
    photos = EXCLUDED.photos,
    official_url = EXCLUDED.official_url,
    sources = EXCLUDED.sources,
    hours_verified = EXCLUDED.hours_verified,
    completeness = EXCLUDED.completeness,
    generated_utc = now()
"""
```

### Script Structure

```python
#!/usr/bin/env python3
"""
enrich_poi_guides.py — Generate rich guide content for all trip_pois.

Usage (on brainnode-01):
    docker cp tools/enrich_poi_guides.py shogun-web-api:/app/tools/
    docker exec shogun-web-api python tools/enrich_poi_guides.py
"""
import json, os, sys, time
import httpx
import psycopg2

DATABASE_URL = os.environ["DATABASE_URL"]
TAVILY_URL   = "http://192.168.71.220:8084/v1/search"
PLACES_URL   = "http://192.168.71.220:8081/v1/places/search_text"
LLM_URL      = "http://192.168.71.220:8080/v1/chat"

INTER_CALL_DELAY = 1.5  # Seconds between API calls

# ... type classification, prompt templates ...

def get_all_pois(conn) -> list[dict]:
    """Fetch all trip_pois not yet enriched."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT p.id, p.city, p.name_en, p.name_ja, p.category,
                   p.lat, p.lng, p.tags, p.crowd_notes, p.best_time_notes
            FROM trip_pois p
            LEFT JOIN poi_guides g ON g.trip_poi_id = p.id
            WHERE g.id IS NULL
            ORDER BY p.city, p.name_en
        """)
        columns = [d[0] for d in cur.description]
        return [dict(zip(columns, row)) for row in cur.fetchall()]

def classify_poi_type(name: str, category: str) -> str:
    """Determine POI type from name and category."""
    combined = f"{name} {category}".lower()
    for poi_type, keywords in TYPE_KEYWORDS.items():
        if any(kw in combined for kw in keywords):
            return poi_type
    return "landmark"  # default

def search_places(name: str, city: str, lat=None, lng=None) -> dict:
    """Search Google Places for canonical info."""
    payload = {
        "text_query": f"{name} {city} Japan",
        "max_results": 1,
        "language_code": "en",
        "region_code": "JP",
    }
    if lat and lng:
        payload["lat"] = float(lat)
        payload["lng"] = float(lng)
        payload["radius_m"] = 500
    try:
        resp = httpx.post(PLACES_URL, json=payload, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        places = (data.get("data") or {}).get("places") or []
        return places[0] if places else {}
    except Exception as exc:
        print(f"  [WARN] Places search failed: {exc}", file=sys.stderr)
        return {}

def search_tavily(name: str, city: str) -> tuple[list[dict], list[str]]:
    """Search Tavily for web context + images."""
    try:
        resp = httpx.post(TAVILY_URL, json={
            "query": f"{name} {city} Japan visitor guide hours tips 2026",
            "max_results": 5,
            "search_depth": "basic",
            "include_images": True,
        }, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        return data.get("results", []), data.get("images", [])
    except Exception as exc:
        print(f"  [WARN] Tavily search failed: {exc}", file=sys.stderr)
        return [], []

def generate_guide(poi_type, name, city, category, places_data, tavily_results, visit_date) -> dict:
    """Call Gemini to synthesize guide content."""
    # Build context from Places
    places_snippet = ""
    if places_data:
        places_snippet = json.dumps({
            "name": (places_data.get("displayName") or {}).get("text"),
            "address": places_data.get("formattedAddress"),
            "rating": places_data.get("rating"),
            "hours": places_data.get("regularOpeningHours"),
            "website": places_data.get("websiteUri"),
        }, indent=2)

    # Build context from Tavily
    tavily_snippet = "\n".join([
        f"- {r.get('title', '')}: {r.get('content', '')[:300]}"
        for r in tavily_results[:5]
    ])

    system_prompt = _get_system_prompt(poi_type)  # Type-specific prompt
    user_prompt = f"""Generate a visitor guide for: {name}
City: {city}
Category: {category}

Google Places data:
{places_snippet or 'No Places data available.'}

Web search results:
{tavily_snippet or 'No web results available.'}

Date context: The family visits around {visit_date} (late March / early April 2026).
Write the guide as the JSON structure specified in your instructions."""

    try:
        resp = httpx.post(LLM_URL, json={
            "provider": "google",
            "model": "gemini-2.0-flash",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "max_output_tokens": 1200,
        }, timeout=25)
        resp.raise_for_status()
        output = resp.json().get("output_text", "").strip()
        # Parse JSON from LLM output (strip markdown fences if present)
        if output.startswith("```"):
            output = output.split("\n", 1)[1].rsplit("```", 1)[0]
        return json.loads(output)
    except json.JSONDecodeError as exc:
        print(f"  [WARN] LLM JSON parse failed: {exc}", file=sys.stderr)
        return {"overview": output[:500] if output else "Guide generation failed."}
    except Exception as exc:
        print(f"  [WARN] LLM call failed: {exc}", file=sys.stderr)
        return {}

def main():
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = False

    pois = get_all_pois(conn)
    print(f"Found {len(pois)} POIs to enrich")

    # Map city+date for trip_context
    CITY_DATES = {
        "osaka": "March 24-28, 2026",
        "nara": "March 25, 2026",
        "kanazawa": "March 30-31, 2026",
        "kyoto": "March 29, 2026",
        "tokyo": "April 1-8, 2026",
        "sakai": "March 28, 2026",
    }

    enriched = 0
    errors = 0

    for idx, poi in enumerate(pois, start=1):
        name = poi["name_en"]
        city = poi["city"]
        category = poi["category"]
        print(f"\n[{idx}/{len(pois)}] {name} ({city}/{category})")

        poi_type = classify_poi_type(name, category)
        visit_date = CITY_DATES.get(city, "March-April 2026")

        # 1. Google Places
        places_data = search_places(name, city, poi.get("lat"), poi.get("lng"))
        time.sleep(INTER_CALL_DELAY)

        # 2. Tavily
        tavily_results, tavily_images = search_tavily(name, city)
        time.sleep(INTER_CALL_DELAY)

        # 3. LLM synthesis
        guide = generate_guide(poi_type, name, city, category, places_data, tavily_results, visit_date)
        time.sleep(INTER_CALL_DELAY)

        if not guide:
            errors += 1
            continue

        # Build photos array
        photos = []
        # From Places
        for photo in (places_data.get("photos") or [])[:3]:
            photos.append({"name": photo.get("name"), "source": "google_places"})
        # From Tavily images
        for img_url in tavily_images[:3]:
            photos.append({"url": img_url, "source": "tavily"})

        # Build sources array
        sources = [{"url": r.get("url"), "title": r.get("title")} for r in tavily_results if r.get("url")]

        # Official URL
        official_url = places_data.get("websiteUri") or None

        # Hours verified?
        hours_verified = bool(places_data.get("regularOpeningHours"))

        # Completeness
        has_overview = bool(guide.get("overview"))
        has_hours = bool(guide.get("hours_info") and guide["hours_info"] != "Unknown")
        completeness = "full" if (has_overview and has_hours and photos) else "partial" if has_overview else "minimal"

        # 4. Insert
        try:
            with conn.cursor() as cur:
                cur.execute(INSERT_SQL, (
                    poi["id"], poi_type,
                    guide.get("overview"), guide.get("why_go"), guide.get("whats_there"),
                    guide.get("hours_info"), guide.get("admission_info"), guide.get("time_estimate"),
                    guide.get("transit_info"), guide.get("tips"), guide.get("trip_context"),
                    json.dumps(photos), official_url, json.dumps(sources),
                    hours_verified, completeness,
                ))
            conn.commit()
            enriched += 1
            print(f"  ✓ {completeness} | {len(photos)} photos | {len(sources)} sources")
        except Exception as exc:
            conn.rollback()
            print(f"  [ERROR] DB insert: {exc}", file=sys.stderr)
            errors += 1

    conn.close()

    print(f"\n{'='*60}")
    print(f"ENRICHMENT COMPLETE")
    print(f"  enriched: {enriched}")
    print(f"  errors:   {errors}")
    print(f"  total:    {len(pois)}")
    print(f"{'='*60}")

    # Verification
    verify = psycopg2.connect(DATABASE_URL)
    with verify.cursor() as cur:
        cur.execute("SELECT completeness, count(*) FROM poi_guides GROUP BY completeness")
        rows = cur.fetchall()
    print("\npoi_guides by completeness:")
    for r in rows:
        print(f"  {r[0]}: {r[1]}")
    verify.close()


if __name__ == "__main__":
    main()
```

### Execution on brainnode-01

```bash
# SSH to brainnode-01 as devops-agent
ssh -i ~/.ssh/devops-agent_ed25519_clean devops-agent@192.168.71.222

# Ensure the script is in the repo on brainnode-01
cd /home/devops-agent/git-work/shogun
git pull

# Copy script into the container and run
docker cp tools/enrich_poi_guides.py shogun-web-api:/app/tools/
docker exec shogun-web-api python tools/enrich_poi_guides.py
```

**Note:** The shogun-web-api container has `psycopg2`, `httpx`, and `DATABASE_URL` available. The script uses direct IPs for gateway access (not container names) because brainnode-01 containers are on a different Docker network than svcnode-01 containers.

---

## Part B: Web API Endpoint

### File to modify: `C:\git\work\shogun\app-services\shogun-web\shogun-web-api\routers\pois.py`

Add a new endpoint after the existing `get_poi_knowledge`:

```python
@router.get("/{poi_id}/guide")
def get_poi_guide(
    poi_id: int,
    request: Request,
    user: User = Depends(get_current_user),
):
    with get_conn() as conn:
        with conn.cursor() as cur:
            # Get POI
            cur.execute(
                """SELECT id, city, name_en, name_ja, category, lat, lng,
                          tags, crowd_notes, best_time_notes, source
                   FROM trip_pois WHERE id=%s""",
                (poi_id,),
            )
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="POI not found")
            poi = _row_to_poi(row)

            # Get guide
            cur.execute(
                """SELECT poi_type, overview, why_go, whats_there,
                          hours_info, admission_info, time_estimate,
                          transit_info, tips, trip_context,
                          photos, official_url, sources,
                          hours_verified, completeness, generated_utc
                   FROM poi_guides WHERE trip_poi_id=%s""",
                (poi_id,),
            )
            guide_row = cur.fetchone()

    if not guide_row:
        # No guide yet — fall back to basic knowledge view
        return {
            "poi": poi,
            "guide": None,
            "has_guide": False,
        }

    return {
        "poi": poi,
        "has_guide": True,
        "guide": {
            "poi_type": guide_row[0],
            "overview": guide_row[1],
            "why_go": guide_row[2],
            "whats_there": guide_row[3],
            "hours_info": guide_row[4],
            "admission_info": guide_row[5],
            "time_estimate": guide_row[6],
            "transit_info": guide_row[7],
            "tips": guide_row[8],
            "trip_context": guide_row[9],
            "photos": guide_row[10],       # JSONB → already parsed
            "official_url": guide_row[11],
            "sources": guide_row[12],      # JSONB → already parsed
            "hours_verified": guide_row[13],
            "completeness": guide_row[14],
            "generated_utc": str(guide_row[15]) if guide_row[15] else None,
        },
    }
```

### File to modify: `C:\git\work\shogun\app-services\shogun-web\shogun-web-ui\src\lib\api.ts`

Add to the `pois` section:

```typescript
guide: (id: number) => apiFetch(`/pois/${id}/guide`),
```

---

## Part C: Web UI Guide Component

### File to modify: `C:\git\work\shogun\app-services\shogun-web\shogun-web-ui\src\lib\types.ts`

Add new interface:

```typescript
export interface PoiGuide {
  poi_type: string;
  overview: string | null;
  why_go: string | null;
  whats_there: string | null;
  hours_info: string | null;
  admission_info: string | null;
  time_estimate: string | null;
  transit_info: string | null;
  tips: string | null;
  trip_context: string | null;
  photos: Array<{ url?: string; name?: string; attribution?: string; source: string }>;
  official_url: string | null;
  sources: Array<{ url: string; title: string }>;
  hours_verified: boolean;
  completeness: string;
  generated_utc: string | null;
}

export interface PoiGuideResponse {
  poi: Poi;
  has_guide: boolean;
  guide: PoiGuide | null;
}
```

### File to modify: `C:\git\work\shogun\app-services\shogun-web\shogun-web-ui\src\app\(app)\pois\[id]\page.tsx`

Replace the existing page to use the guide endpoint:

```typescript
import { api } from "@/lib/api";
import PoiGuideView from "@/components/pois/PoiGuideView";
import KnowledgeDeepDive from "@/components/knowledge/KnowledgeDeepDive";
import { notFound } from "next/navigation";

async function getGuide(id: string) {
  try {
    return await api.pois.guide(parseInt(id, 10));
  } catch {
    return null;
  }
}

export default async function PoiDetailPage({ params }: { params: { id: string } }) {
  const data = await getGuide(params.id);
  if (!data) notFound();

  return (
    <div style={{ minHeight: "100%", background: "var(--city-surface, #f9fafb)" }}>
      <div style={{ padding: "1rem", borderBottom: "1px solid #e5e7eb", background: "white" }}>
        <a href="/pois" style={{ color: "var(--city-accent)", fontSize: "0.875rem", fontWeight: 600, textDecoration: "none" }}>
          ← Back to Places
        </a>
      </div>
      {data.has_guide && data.guide ? (
        <PoiGuideView poi={data.poi} guide={data.guide} />
      ) : (
        <KnowledgeDeepDive data={data as any} />
      )}
    </div>
  );
}
```

### File to create: `C:\git\work\shogun\app-services\shogun-web\shogun-web-ui\src\components\pois\PoiGuideView.tsx`

Build a rich guide component. Follow these patterns from the existing codebase:
- Inline styles (project standard — no Tailwind classes)
- White cards with `borderRadius: "10px"`, `boxShadow: "0 1px 3px rgba(0,0,0,0.06)"`
- Section headers with `fontWeight: 700`
- Body text `color: "#374151"`, `lineHeight: 1.6`
- Tag badges: `background: "#eff6ff"`, `color: "#1d4ed8"`, `fontSize: "0.75rem"`
- Max width: `maxWidth: "720px"`, `margin: "0 auto"`, `padding: "1.5rem"`

Sections to render:
1. **Header**: name_en, name_ja, poi_type badge, category tags
2. **Photo gallery**: Horizontal scroll of photos (if available)
3. **Overview card**: overview text
4. **Why Go card**: why_go text with interest tags
5. **What's There card**: whats_there text
6. **Practical Info card**: hours_info, admission_info, time_estimate (with icons)
7. **Getting There card**: transit_info
8. **Tips card**: tips text
9. **Your Trip card**: trip_context text (with amber/highlight background)
10. **Sources accordion**: collapsible list of source URLs
11. **Ask Shogun**: reuse the ChatPanel integration from KnowledgeDeepDive

Use `"use client"` directive and `useState` for expandable sections.

---

## Done Criteria

- [ ] `tools/enrich_poi_guides.py` created and runs successfully
- [ ] All ~111 trip_pois have entries in poi_guides
- [ ] Verification query shows completeness breakdown
- [ ] `GET /pois/{id}/guide` endpoint returns enriched data
- [ ] `api.pois.guide(id)` method added to frontend API
- [ ] `PoiGuideView` component renders all guide sections
- [ ] POI detail page shows rich guide when available, falls back to old view when not
- [ ] Types added to types.ts
- [ ] Code committed to develop branch
