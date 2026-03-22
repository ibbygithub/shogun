#!/usr/bin/env python3
"""
enrich_poi_guides.py — Generate rich guide content for all trip_pois.

Usage (on brainnode-01):
    docker cp tools/enrich_poi_guides.py shogun-web-api:/app/tools/
    docker exec shogun-web-api python tools/enrich_poi_guides.py
"""
import json
import os
import sys
import time

import httpx
import psycopg2

DATABASE_URL = os.environ["DATABASE_URL"]
TAVILY_URL = "http://192.168.71.220:8084/v1/search"
PLACES_URL = "http://192.168.71.220:8081/v1/places/search_text"
LLM_URL = "http://192.168.71.220:8080/v1/chat"

INTER_CALL_DELAY = 1.5  # seconds between API calls to avoid rate limits

# ---------------------------------------------------------------------------
# POI type classification
# ---------------------------------------------------------------------------

TYPE_KEYWORDS = {
    "museum": ["museum", "gallery", "art"],
    "shrine": ["shrine", "jinja"],
    "temple": ["temple", "ji", "dera", "kannon"],
    "shopping_district": [
        "shopping", "street", "market", "mall", "store", "shop",
        "dori", "yokocho",
    ],
    "park": ["park", "garden", "gyoen", "koen"],
    "landmark": [
        "tower", "building", "castle", "observatory", "crossing", "billboard",
    ],
    "neighborhood": ["district", "area", "neighborhood", "chaya", "town"],
    "restaurant": [
        "restaurant", "cafe", "bakery", "ramen", "food", "cream puff",
    ],
    "event": ["studios", "samurai", "chiikawa"],
}

# ---------------------------------------------------------------------------
# LLM system prompts per POI type
# ---------------------------------------------------------------------------

_BASE_JSON_SCHEMA = """\
Output EXACTLY this JSON structure (no markdown, no code fences):
{
  "overview": "2-3 sentences: what this place is and why it matters",
  "why_go": "Who should visit and what interests it serves",
  "whats_there": "Key highlights visitors should know about",
  "hours_info": "Operating hours, closed days. Say 'Unknown' if not available.",
  "admission_info": "Entry cost, ticket types, reservations. Say 'Unknown' if not available.",
  "time_estimate": "One of: quick_stop (under 30min), standard_visit (1-2hr), deep_visit (2-4hr)",
  "transit_info": "Nearest station(s), walk time, useful train lines",
  "tips": "2-3 practical tips: best time, crowd avoidance, cash/card, photo spots",
  "trip_context": "Why this fits a March-April 2026 Japan trip for a family of 3 (tech-lover dad, shopping/skincare mom, anime-fan teen)"
}"""

SYSTEM_PROMPTS = {
    "museum": f"""You are a Japan travel expert writing a concise visitor guide.
Write in a warm, practical tone. Be specific — include real details, not generic advice.
Focus on key exhibits, floors, areas, and highlights visitors should know about.
{_BASE_JSON_SCHEMA}""",

    "shrine": f"""You are a Japan travel expert writing a concise visitor guide for a Shinto shrine.
Write in a warm, practical tone. Include etiquette notes (bowing, washing hands at temizu),
seasonal events, prayer customs, and any festivals around late March / early April.
{_BASE_JSON_SCHEMA}""",

    "temple": f"""You are a Japan travel expert writing a concise visitor guide for a Buddhist temple.
Write in a warm, practical tone. Include etiquette notes, incense rituals,
seasonal events (sakura around late March!), and any special exhibitions.
{_BASE_JSON_SCHEMA}""",

    "shopping_district": f"""You are a Japan travel expert writing a concise visitor guide for a shopping area.
Write in a warm, practical tone. Emphasize store highlights, what to buy,
price ranges, opening times, and whether shops accept card or cash only.
{_BASE_JSON_SCHEMA}""",

    "park": f"""You are a Japan travel expert writing a concise visitor guide for a park or garden.
Write in a warm, practical tone. Highlight seasonal features (sakura in late March!),
walking routes, photo spots, and picnic rules.
{_BASE_JSON_SCHEMA}""",

    "landmark": f"""You are a Japan travel expert writing a concise visitor guide for a landmark.
Write in a warm, practical tone. Cover viewing times, free vs paid entry,
night vs day differences, and best photo angles.
{_BASE_JSON_SCHEMA}""",

    "neighborhood": f"""You are a Japan travel expert writing a concise visitor guide for a neighborhood or district.
Write in a warm, practical tone. Suggest a walking route, hidden gems,
atmosphere description, and pairing with nearby POIs.
{_BASE_JSON_SCHEMA}""",

    "restaurant": f"""You are a Japan travel expert writing a concise visitor guide for a restaurant or cafe.
Write in a warm, practical tone. Cover signature dishes, reservation needs,
wait times, menu language tips, and dietary accommodation.
{_BASE_JSON_SCHEMA}""",

    "event": f"""You are a Japan travel expert writing a concise visitor guide for an attraction or experience.
Write in a warm, practical tone. Cover what to expect, booking requirements,
time needed, and how to get the most out of the visit.
{_BASE_JSON_SCHEMA}""",
}

# ---------------------------------------------------------------------------
# DB insert
# ---------------------------------------------------------------------------

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

# ---------------------------------------------------------------------------
# Data fetchers
# ---------------------------------------------------------------------------


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
    return "landmark"


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


def _get_system_prompt(poi_type: str) -> str:
    return SYSTEM_PROMPTS.get(poi_type, SYSTEM_PROMPTS["landmark"])


def generate_guide(
    poi_type: str,
    name: str,
    city: str,
    category: str,
    places_data: dict,
    tavily_results: list[dict],
    visit_date: str,
) -> dict:
    """Call Gemini to synthesize guide content."""
    places_snippet = ""
    if places_data:
        places_snippet = json.dumps({
            "name": (places_data.get("displayName") or {}).get("text"),
            "address": places_data.get("formattedAddress"),
            "rating": places_data.get("rating"),
            "hours": places_data.get("regularOpeningHours"),
            "website": places_data.get("websiteUri"),
        }, indent=2)

    tavily_snippet = "\n".join([
        f"- {r.get('title', '')}: {r.get('content', '')[:300]}"
        for r in tavily_results[:5]
    ])

    system_prompt = _get_system_prompt(poi_type)
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
        # Strip markdown fences if the LLM wrapped them
        if output.startswith("```"):
            output = output.split("\n", 1)[1].rsplit("```", 1)[0]
        return json.loads(output)
    except json.JSONDecodeError as exc:
        print(f"  [WARN] LLM JSON parse failed: {exc}", file=sys.stderr)
        return {"overview": output[:500] if output else "Guide generation failed."}
    except Exception as exc:
        print(f"  [WARN] LLM call failed: {exc}", file=sys.stderr)
        return {}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

CITY_DATES = {
    "osaka": "March 24-28, 2026",
    "nara": "March 25, 2026",
    "kanazawa": "March 30-31, 2026",
    "kyoto": "March 29, 2026",
    "tokyo": "April 1-8, 2026",
    "sakai": "March 28, 2026",
}


def main():
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = False

    pois = get_all_pois(conn)
    print(f"Found {len(pois)} POIs to enrich")

    if not pois:
        print("Nothing to do — all POIs already enriched.")
        conn.close()
        return

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

        # 2. Tavily web search
        tavily_results, tavily_images = search_tavily(name, city)
        time.sleep(INTER_CALL_DELAY)

        # 3. LLM synthesis
        guide = generate_guide(
            poi_type, name, city, category,
            places_data, tavily_results, visit_date,
        )
        time.sleep(INTER_CALL_DELAY)

        if not guide:
            errors += 1
            continue

        # Build photos array
        photos = []
        for photo in (places_data.get("photos") or [])[:3]:
            photos.append({"name": photo.get("name"), "source": "google_places"})
        for img_url in tavily_images[:3]:
            photos.append({"url": img_url, "source": "tavily"})

        # Build sources array
        sources = [
            {"url": r.get("url"), "title": r.get("title")}
            for r in tavily_results if r.get("url")
        ]

        official_url = places_data.get("websiteUri") or None
        hours_verified = bool(places_data.get("regularOpeningHours"))

        # Completeness assessment
        has_overview = bool(guide.get("overview"))
        has_hours = bool(
            guide.get("hours_info") and guide["hours_info"] != "Unknown"
        )
        if has_overview and has_hours and photos:
            completeness = "full"
        elif has_overview:
            completeness = "partial"
        else:
            completeness = "minimal"

        # 4. Insert into poi_guides
        try:
            with conn.cursor() as cur:
                cur.execute(INSERT_SQL, (
                    poi["id"], poi_type,
                    guide.get("overview"), guide.get("why_go"),
                    guide.get("whats_there"),
                    guide.get("hours_info"), guide.get("admission_info"),
                    guide.get("time_estimate"), guide.get("transit_info"),
                    guide.get("tips"), guide.get("trip_context"),
                    json.dumps(photos), official_url, json.dumps(sources),
                    hours_verified, completeness,
                ))
            conn.commit()
            enriched += 1
            print(
                f"  -> {completeness} | {len(photos)} photos | "
                f"{len(sources)} sources"
            )
        except Exception as exc:
            conn.rollback()
            print(f"  [ERROR] DB insert: {exc}", file=sys.stderr)
            errors += 1

    conn.close()

    print(f"\n{'=' * 60}")
    print("ENRICHMENT COMPLETE")
    print(f"  enriched: {enriched}")
    print(f"  errors:   {errors}")
    print(f"  total:    {len(pois)}")
    print(f"{'=' * 60}")

    # Verification query
    verify_conn = psycopg2.connect(DATABASE_URL)
    with verify_conn.cursor() as cur:
        cur.execute(
            "SELECT completeness, count(*) FROM poi_guides GROUP BY completeness"
        )
        rows = cur.fetchall()
    print("\npoi_guides by completeness:")
    for r in rows:
        print(f"  {r[0]}: {r[1]}")
    verify_conn.close()


if __name__ == "__main__":
    main()
