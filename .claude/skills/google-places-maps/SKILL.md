---
name: google-places-maps
description: >
  Google Places API and Google Maps URL knowledge for Shogun. Use this skill when
  building or debugging the find_nearby_places tool, constructing Google Maps links,
  working with the places-google gateway, or reasoning about coordinates, distances,
  and direction link patterns. Also covers the anchor coordinate system, haversine
  distance, locationBias vs locationRestriction, and the two-link-per-place pattern.
user-invocable: true
---

# Google Places and Maps — Shogun Reference

## Overview

Shogun uses Google Places via an internal gateway (`platform-places-google`) running on svcnode-01. The gateway wraps the Google Places API `searchNearby` endpoint. Results feed the `find_nearby_places` tool in `chat.py`.

**Gateway endpoint:** `http://192.168.71.220:8081` (direct IP, not FQDN — internal access from brainnode-01)
**Gateway code:** `../ibbytech-foundation/services/places-google/app.py`

---

## Google Places API: `searchNearby` vs `searchText`

The gateway uses `searchNearby`, not `searchText`. This matters because they have different radius behaviors:

| API Method | Radius behavior | Use case |
|-----------|----------------|----------|
| `searchText` with `locationBias` | **Soft hint** — results can be outside the radius | General text search |
| `searchNearby` with `locationRestriction` | **Hard cutoff** — results always within radius | Proximity-critical search |

Shogun uses `searchNearby` for `find_nearby_places` because we want results near a specific anchor, not results that might be 5km away just because they match the text query well.

**Critical lesson:** Even with `locationRestriction`, the right answer is to return ALL results and let the user decide, not to apply an additional software filter. The Places API may return fewer results than expected in some areas (a 800m radius in Osaka may yield 3 SIM card shops, all of which are actually 1400-2200m away because the Places API itself is approximating). A hard software filter on top of this will silently discard all results and leave the AI with nothing.

**Correct approach:** Return all results, sort by haversine distance, label results that exceed the requested radius.

---

## Field Mask

The `searchNearby` call must include `places.location` in the field mask to get lat/lng coordinates back.

Current field mask in `platform-places-google/app.py`:
```
TEXT_SEARCH_FIELD_MASK = (
    "places.id,places.displayName,places.formattedAddress,"
    "places.location,places.googleMapsUri,places.rating,"
    "places.regularOpeningHours,places.primaryType,places.types"
)
```

`places.location` returns `{ "latitude": float, "longitude": float }`. These coordinates are used for:
1. Haversine distance calculation
2. Building direction links with exact destination coordinates

**Without `places.location` in the mask, direction links will be wrong.** Verify the gateway includes this field before debugging distance or link issues.

---

## Haversine Distance

Real-world distance between two lat/lng points. Used to sort results and show users actual walking distance estimates.

Implementation in `chat.py`:
```python
import math

def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6_371_000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))
```

Returns meters. For walking time estimates: 800m ≈ 10 min walk at average pace.

**Do not estimate distance from radius.** `radius_m / 80` (old approximation) was wrong. Always use haversine with the actual lat/lng from the API response.

---

## Trip Anchor Coordinates

Shogun has 6 pre-defined anchor coordinates matching the family's actual accommodation addresses:

```python
_ANCHOR_COORDS: dict[str, tuple[float, float]] = {
    "osaka-airbnb":   (34.6979, 135.5035),   # 大阪市北区浪花町10-12
    "nara-park":      (34.6851, 135.8050),   # Nara accommodation
    "usjapan":        (34.6654, 135.4323),   # Universal Studios Japan area
    "kanazawa-hotel": (36.5613, 136.6562),   # Hotel Sanraku, Kanazawa
    "tokyo-sugamo":   (35.7337, 139.7394),   # 東京都豊島区巣鴨4-37-6
    "ghibli-museum":  (35.6962, 139.5704),   # Ghibli Museum, Mitaka
}
```

These are used as the search origin and as the "Walk from [Anchor]" link origin.

The `find_nearby_places` tool accepts an `anchor` string parameter. It maps to one of these entries. "current accommodation" in the system prompt resolves to the city-appropriate anchor. If no anchor is specified, the tool defaults to the anchor matching the current city.

**Coordinate accuracy:** These are area coordinates, not building-exact. They are accurate enough for navigation (Google Maps will route to the exact building from these points) but not accurate enough to measure walking distance to 10m precision.

---

## Google Maps URL Patterns

### Direction Links (Walking)

Two patterns — use both per place result:

**1. Walk from fixed anchor (web UI, pre-planned route):**
```
https://www.google.com/maps/dir/?api=1
  &origin={anchor_lat},{anchor_lng}
  &destination={place_lat},{place_lng}
  &travelmode=walking
```
- Shows on a map where the user will walk from
- Renders as: `[Walk from Osaka Airbnb →]`
- Use the anchor's `_ANCHOR_COORDS` lat/lng as origin

**2. Navigate from current GPS (Telegram, on-the-ground):**
```
https://www.google.com/maps/dir/?api=1
  &destination={place_lat},{place_lng}
  &travelmode=walking
```
- No `origin=` parameter — Google Maps uses device GPS automatically
- Opens navigation from wherever the user is standing
- Renders as: `[Navigate from here →]`

**Never construct these URLs with place names instead of coordinates.** Name-based URLs are unreliable and ambiguous. Only coordinates produce reliable, direct navigation links.

### Place View (Not Directions)

```
https://www.google.com/maps/place/?q=place_id:{place_id}
```
- Opens the Google Maps place card for a specific location
- Use the `places.id` field from the Places API response
- Only use this if you want to show the place details, not navigate there

### Search Query (Fallback)

```
https://www.google.com/maps/search/?api=1&query={encoded_name}
```
- Last resort — ambiguous, may show wrong location
- Use coordinates-based links whenever possible

---

## Two-Link-Per-Place Pattern

Every place result from `find_nearby_places` should include both:

```
1. **Yamada Denki Namba** (家電量販店)
   📍 2.1 km from Osaka Airbnb • ⏱ ~26 min walk
   [Walk from Osaka Airbnb →](https://www.google.com/maps/dir/?api=1&origin=34.6979,135.5035&destination={lat},{lng}&travelmode=walking)
   [Navigate from here →](https://www.google.com/maps/dir/?api=1&destination={lat},{lng}&travelmode=walking)
```

**Rationale:**
- The web UI is used for planning — "Walk from Airbnb" shows the user exactly how far it is from base
- Telegram is used on-the-ground — "Navigate from here" routes from wherever they are standing
- Both are needed because the same content may be accessed from both interfaces

---

## `find_nearby_places` Tool — Implementation Reference

**Tool definition parameters:**
- `query`: What to search for (e.g., "SIM card shop", "pharmacy")
- `anchor`: One of the 6 anchor keys or "current accommodation"
- `radius_m`: Search radius in meters (default 800)

**Call chain:**
1. Resolve anchor → lat/lng from `_ANCHOR_COORDS`
2. POST to `http://192.168.71.220:8081/places/nearby` with `{lat, lng, radius_m, query}`
3. Response: `{"places": [{id, displayName, formattedAddress, location, googleMapsUri, ...}]}`
4. Extract `location.latitude` / `location.longitude` from each place
5. Calculate haversine distance from anchor to each place
6. Sort by distance
7. Build direction links using real coordinates
8. Auto-save to `knowledge_items` table (dedup on `googleMapsUri`)
9. Return: plain text summary (for Gemini) + formatted block (for user)

**PLACES_GATEWAY_URL env var:** Set in brainnode-01's `.env` as `http://192.168.71.220:8081`. Do not use the FQDN `places.platform.ibbytech.com` for direct brainnode-01 → svcnode-01 traffic — use the IP.

---

## When to Use `find_nearby_places` vs `web_search`

| Situation | Tool | Why |
|-----------|------|-----|
| User asks what's near the hotel/airbnb | `find_nearby_places` | Real location data, direction links |
| User asks for SIM cards, pharmacy, convenience store | `find_nearby_places` | Physical proximity matters |
| User asks for restaurant recommendations | `web_search` with `include_domains: ["tabelog.com"]` | Ratings/reviews matter more than raw proximity |
| User asks about a specific place (Kenroku-en) | `get_trip_pois` first, then `search_trip_knowledge` | Likely already in knowledge base |
| User asks about current events, sakura, hours | `web_search` | Real-time info needed |
| User asks "find X near Y neighborhood" | `find_nearby_places` | Proximity-based with known anchor |

---

## Knowledge Base Integration

`find_nearby_places` auto-saves results to the `knowledge_items` table with:
- Deduplication on `googleMapsUri`
- Category: `"place"` (or more specific if determinable)
- Source: `"google_places"`

Subsequent `search_trip_knowledge` queries can find these saved results, so repeated searches for similar things in the same area hit the local DB first. This is the self-improving knowledge base pattern.
