"""
Shogun — Places Google Service (MVP2)
====================================

What this microservice does
---------------------------
This service ingests a *seed file* of “neighborhood anchors” (usually your lodging address),
resolves each anchor to a latitude/longitude, then uses **Google Places API (New)** to:
  1) Discover nearby places (nearbySearch OR textSearch)
  2) Enrich those places with details (Get Place Details)
  3) Store results in Postgres (schema: `places`)

Why this exists as its own microservice
--------------------------------------
You explicitly wanted Places to be independent from the LLM gateway (and other services).
So this service owns:
  - Google Places requests + cost controls (field masks, max results, top-N details)
  - “Anchor resolution” and scoping rules
  - Places database schema and writes

IMPORTANT: Where code runs vs where files live
----------------------------------------------
- This Python code runs inside a Docker container on svcnode-01 (or dev machine via Docker).
- `/app/...` paths refer to paths *inside the container image*.
- Seeds and SQL are included in the image under:
    /app/seeds/...
    /app/sql/...

If you edit seeds or SQL, do it on Windows → git commit/push → pull on Linux.
Do NOT hot-edit on Linux unless it’s a tiny troubleshooting step, and even then,
you should port the change back to Windows and commit.

High-level flow (Seeds ingestion)
---------------------------------
POST /v1/ingest/seeds
  -> Load seeds JSON file (/app/seeds/neighborhoods.example.json unless overridden)
  -> For each neighborhood:
       -> Resolve anchor:
            - If seed has anchor.location.lat/lng: use those
            - Else if seed has anchor.address: geocode it (Google Geocoding API)
       -> For each category:
            -> Discover places
            -> Rank + pick Top N
            -> Fetch details for Top N
            -> Upsert into places.google_places
            -> Store raw snapshots into places.google_place_snapshots

Why your earlier results were from California
---------------------------------------------
If the service uses a *text search without a location restriction*, Google can return
results near the server’s region / inferred context, which can look “wrong”.
The correct pattern for “near hotel” queries is:
  - Resolve hotel address to lat/lng first
  - Use Places requests with a location restriction (circle around that lat/lng)
  - Optionally enforce hygiene rules (country == JP) to discard mismatches

This script implements exactly that “address -> lat/lng -> constrained search” plan.

Cost control strategy (MVP)
---------------------------
- Use minimal field masks for discovery (nearby/text search)
- Only call Details for Top N results (default 75, configurable)
- Cache details results in DB (avoid refetching too frequently)
- Keep categories limited during early testing

Security / Secrets
------------------
- DB password + API key come from environment variables.
- `.env` is ignored by git. Only `.env.example` is committed.
"""

import json
import math
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import psycopg2
import psycopg2.extras
import requests
from flask import Flask, jsonify, request

# =============================================================================
# 1) Configuration
# =============================================================================

def _env(name: str, default: Optional[str] = None) -> str:
    """
    Read an environment variable (required unless default provided).

    Why:
      - Ensures we fail fast on missing config instead of silently running broken.
    """
    v = os.getenv(name, default)
    if v is None:
        raise RuntimeError(f"Missing required env var: {name}")
    return v


# Service
PORT = int(_env("PORT", "8081"))
LOG_LEVEL = _env("LOG_LEVEL", "INFO").upper()

# Google API
GOOGLE_PLACES_API_KEY = _env("GOOGLE_PLACES_API_KEY", "")
GOOGLE_REGION = _env("GOOGLE_REGION", "JP")      # used as a bias / default region
GOOGLE_LANGUAGE = _env("GOOGLE_LANGUAGE", "en")  # MVP2 uses English; MVP3 can add Japanese
GOOGLE_HYGIENE_COUNTRY = _env("GOOGLE_HYGIENE_COUNTRY", "JP")  # hygiene filter, post-response

# Seed / Ingest defaults
SEEDS_PATH = _env("SEEDS_PATH", "/app/seeds/neighborhoods.example.json")

DEFAULT_RADIUS_M = int(_env("DEFAULT_RADIUS_M", "2000"))
DEFAULT_MAX_RESULTS = int(_env("DEFAULT_MAX_RESULTS", "50"))
DEFAULT_DETAILS_TOP_N = int(_env("DEFAULT_DETAILS_TOP_N", "75"))

# Google Places "New API" endpoints
PLACES_NEARBY_URL = "https://places.googleapis.com/v1/places:searchNearby"
PLACES_TEXT_URL = "https://places.googleapis.com/v1/places:searchText"
PLACES_DETAILS_URL = "https://places.googleapis.com/v1/places/"

# Google Geocoding endpoint (used to resolve hotel address -> lat/lng)
GEOCODE_URL = "https://maps.googleapis.com/maps/api/geocode/json"

# Field masks (cost control!)
# Nearby/Text discovery masks should be minimal.
DEFAULT_NEARBY_FIELDMASK = _env(
    "GOOGLE_NEARBY_FIELDMASK",
    "places.id,places.displayName,places.location,places.types,places.rating,"
    "places.userRatingCount,places.priceLevel,places.primaryType,places.googleMapsUri,"
    "places.formattedAddress",
)

# Details mask pulls what we actually want to store for “enriched place”
DEFAULT_DETAILS_FIELDMASK = _env(
    "GOOGLE_DETAILS_FIELDMASK",
    "id,displayName,formattedAddress,location,googleMapsUri,websiteUri,internationalPhoneNumber,"
    "rating,userRatingCount,priceLevel,primaryType,types,regularOpeningHours,paymentOptions,"
    "addressComponents",
)


# Database
PGHOST = _env("PGHOST", "dbnode-01")
PGPORT = int(_env("PGPORT", "5432"))
PGDATABASE = _env("PGDATABASE", "shogun_v1")
PGUSER = _env("PGUSER", "places_app")
PGPASSWORD = _env("PGPASSWORD", "")


# =============================================================================
# 2) Lightweight in-process cache (for short-lived repeat calls)
# =============================================================================
# NOTE: This is not meant to replace DB caching. DB is the real cache across restarts.
# This is just to reduce duplicate HTTP calls during a single ingestion run.

@dataclass
class CacheEntry:
    value: Any
    expires_at: float


_CACHE: Dict[str, CacheEntry] = {}


def cache_get(key: str) -> Optional[Any]:
    entry = _CACHE.get(key)
    if not entry:
        return None
    if time.time() >= entry.expires_at:
        _CACHE.pop(key, None)
        return None
    return entry.value


def cache_set(key: str, value: Any, ttl_s: int = 60) -> None:
    _CACHE[key] = CacheEntry(value=value, expires_at=time.time() + ttl_s)


# =============================================================================
# 3) Database helpers
# =============================================================================

def db_conn():
    """
    Open a new Postgres connection.

    Note:
      - We intentionally create connections “as needed” for simplicity in MVP.
      - If load grows, replace with a connection pool.
    """
    return psycopg2.connect(
        host=PGHOST,
        port=PGPORT,
        dbname=PGDATABASE,
        user=PGUSER,
        password=PGPASSWORD,
        connect_timeout=5,
    )


def db_exec(sql: str, params: Optional[Tuple[Any, ...]] = None) -> None:
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)


def db_health() -> Tuple[bool, Optional[str]]:
    """
    Return (db_ok, db_error_str)
    """
    try:
        with db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1;")
                _ = cur.fetchone()
        return True, None
    except Exception as e:
        return False, str(e)


# =============================================================================
# 4) Google HTTP helpers
# =============================================================================

def _headers(fieldmask: str) -> Dict[str, str]:
    """
    Google Places (New) requires:
      - X-Goog-Api-Key
      - X-Goog-FieldMask
    """
    return {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": GOOGLE_PLACES_API_KEY,
        "X-Goog-FieldMask": fieldmask,
    }


def google_nearby_search(
    lat: float,
    lng: float,
    radius_m: int,
    included_types: Optional[List[str]],
    max_results: int,
    language_code: str,
    region_code: str,
    fieldmask: str = DEFAULT_NEARBY_FIELDMASK,
) -> Dict[str, Any]:
    """
    Places Nearby Search (New API)

    This is the “correct” query style for “near my hotel” use-cases.
    It uses a strict locationRestriction around the anchor lat/lng.

    Docs hint: Nearby search requires a locationRestriction shape and returns nearby places.
    """
    payload: Dict[str, Any] = {
        "languageCode": language_code,
        "regionCode": region_code,
        "maxResultCount": max_results,
        "locationRestriction": {
            "circle": {
                "center": {"latitude": lat, "longitude": lng},
                "radius": float(radius_m),
            }
        },
    }
    if included_types:
        payload["includedTypes"] = included_types

    resp = requests.post(PLACES_NEARBY_URL, headers=_headers(fieldmask), json=payload, timeout=20)
    return {"status_code": resp.status_code, "json": resp.json() if resp.content else {}}


def google_text_search(
    query: str,
    lat: float,
    lng: float,
    radius_m: int,
    max_results: int,
    language_code: str,
    region_code: str,
    fieldmask: str = DEFAULT_NEARBY_FIELDMASK,
) -> Dict[str, Any]:
    """
    Places Text Search (New API)

    We still apply a strict locationRestriction circle so it behaves like:
      “text query near this hotel”.

    This is essential. Without locationRestriction, results can “drift” and look wrong.

    Why not just add 'Osaka' to the query?
      - You said you do NOT want hard-coded “Osaka” logic that prevents future non-Japan use.
      - Constraining by lat/lng is the correct general solution.
    """
    payload: Dict[str, Any] = {
        "textQuery": query,
        "languageCode": language_code,
        "regionCode": region_code,
        "maxResultCount": max_results,
        "locationRestriction": {
            "circle": {
                "center": {"latitude": lat, "longitude": lng},
                "radius": float(radius_m),
            }
        },
    }

    resp = requests.post(PLACES_TEXT_URL, headers=_headers(fieldmask), json=payload, timeout=20)
    return {"status_code": resp.status_code, "json": resp.json() if resp.content else {}}


def google_place_details(
    place_id: str,
    language_code: str,
    region_code: str,
    fieldmask: str = DEFAULT_DETAILS_FIELDMASK,
) -> Dict[str, Any]:
    """
    Places Details (New API): GET /v1/places/{placeId}

    This is where costs can grow, so:
      - Only call details for Top N
      - Store results in DB to avoid refetching
    """
    url = f"{PLACES_DETAILS_URL}{place_id}"
    params = {"languageCode": language_code, "regionCode": region_code}
    resp = requests.get(url, headers=_headers(fieldmask), params=params, timeout=20)
    return {"status_code": resp.status_code, "json": resp.json() if resp.content else {}}


# =============================================================================
# 5) Parsing helpers
# =============================================================================

def _get_display_name(place_obj: Dict[str, Any]) -> str:
    """
    Google returns displayName as object: {"text": "...", "languageCode": "..."}
    """
    dn = place_obj.get("displayName")
    if isinstance(dn, dict):
        return dn.get("text") or ""
    if isinstance(dn, str):
        return dn
    return ""


def _get_location(place_obj: Dict[str, Any]) -> Tuple[Optional[float], Optional[float]]:
    loc = place_obj.get("location") or {}
    lat = loc.get("latitude")
    lng = loc.get("longitude")
    return lat, lng


def rank_places(places: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Rank places “best first” using a simple heuristic.

    MVP heuristic:
      - rating desc
      - userRatingCount desc
    """
    def _score(p: Dict[str, Any]) -> Tuple[float, int]:
        rating = float(p.get("rating") or 0.0)
        urc = int(p.get("userRatingCount") or 0)
        return rating, urc

    return sorted(places, key=_score, reverse=True)


# =============================================================================
# 6) Persistence helpers (Postgres)
# =============================================================================

def upsert_place(
    place_id: str,
    details_json: Dict[str, Any],
    nearby_json: Optional[Dict[str, Any]],
    source_neighborhood_id: str,
    source_city: str,
    source_country: str,
) -> None:
    """
    Upsert a place into places.google_places.

    This table is the “canonical” view of a place.
    Raw snapshots go into places.google_place_snapshots.
    """
    display_name = _get_display_name(details_json)
    formatted_address = details_json.get("formattedAddress")
    primary_type = details_json.get("primaryType")
    types = details_json.get("types") or []
    lat, lng = _get_location(details_json)

    google_maps_uri = details_json.get("googleMapsUri")
    website_uri = details_json.get("websiteUri")
    international_phone = details_json.get("internationalPhoneNumber")

    rating = details_json.get("rating")
    user_rating_count = details_json.get("userRatingCount")
    price_level = details_json.get("priceLevel")

    opening_hours_json = details_json.get("regularOpeningHours")
    payment_options_json = details_json.get("paymentOptions")

    open_now = None
    if isinstance(opening_hours_json, dict):
        open_now = opening_hours_json.get("openNow")

    sql = """
    INSERT INTO places.google_places (
        place_id,
        display_name,
        primary_type,
        types,
        formatted_address,
        lat,
        lng,
        google_maps_uri,
        website_uri,
        international_phone,
        rating,
        user_rating_count,
        price_level,
        open_now,
        opening_hours_json,
        payment_options_json,
        source_neighborhood_id,
        source_city,
        source_country,
        last_details_fetch_utc,
        last_nearby_fetch_utc,
        raw_details_json,
        raw_nearby_json,
        created_utc,
        updated_utc
    )
    VALUES (
        %(place_id)s,
        %(display_name)s,
        %(primary_type)s,
        %(types)s,
        %(formatted_address)s,
        %(lat)s,
        %(lng)s,
        %(google_maps_uri)s,
        %(website_uri)s,
        %(international_phone)s,
        %(rating)s,
        %(user_rating_count)s,
        %(price_level)s,
        %(open_now)s,
        %(opening_hours_json)s,
        %(payment_options_json)s,
        %(source_neighborhood_id)s,
        %(source_city)s,
        %(source_country)s,
        NOW(),
        NOW(),
        %(raw_details_json)s,
        %(raw_nearby_json)s,
        NOW(),
        NOW()
    )
    ON CONFLICT (place_id) DO UPDATE SET
        display_name = EXCLUDED.display_name,
        primary_type = EXCLUDED.primary_type,
        types = EXCLUDED.types,
        formatted_address = EXCLUDED.formatted_address,
        lat = EXCLUDED.lat,
        lng = EXCLUDED.lng,
        google_maps_uri = EXCLUDED.google_maps_uri,
        website_uri = EXCLUDED.website_uri,
        international_phone = EXCLUDED.international_phone,
        rating = EXCLUDED.rating,
        user_rating_count = EXCLUDED.user_rating_count,
        price_level = EXCLUDED.price_level,
        open_now = EXCLUDED.open_now,
        opening_hours_json = EXCLUDED.opening_hours_json,
        payment_options_json = EXCLUDED.payment_options_json,
        source_neighborhood_id = EXCLUDED.source_neighborhood_id,
        source_city = EXCLUDED.source_city,
        source_country = EXCLUDED.source_country,
        last_details_fetch_utc = NOW(),
        last_nearby_fetch_utc = NOW(),
        raw_details_json = EXCLUDED.raw_details_json,
        raw_nearby_json = EXCLUDED.raw_nearby_json,
        updated_utc = NOW();
    """

    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                sql,
                {
                    "place_id": place_id,
                    "display_name": display_name,
                    "primary_type": primary_type,
                    "types": types,
                    "formatted_address": formatted_address,
                    "lat": lat,
                    "lng": lng,
                    "google_maps_uri": google_maps_uri,
                    "website_uri": website_uri,
                    "international_phone": international_phone,
                    "rating": rating,
                    "user_rating_count": user_rating_count,
                    "price_level": price_level,
                    "open_now": open_now,
                    "opening_hours_json": psycopg2.extras.Json(opening_hours_json) if opening_hours_json else None,
                    "payment_options_json": psycopg2.extras.Json(payment_options_json) if payment_options_json else None,
                    "source_neighborhood_id": source_neighborhood_id,
                    "source_city": source_city,
                    "source_country": source_country,
                    "raw_details_json": psycopg2.extras.Json(details_json),
                    "raw_nearby_json": psycopg2.extras.Json(nearby_json) if nearby_json else None,
                },
            )


def snapshot_raw(snapshot_type: str, raw_json: Dict[str, Any]) -> None:
    """
    Store raw API responses in places.google_place_snapshots for debugging/audit.
    """
    sql = """
    INSERT INTO places.google_place_snapshots (snapshot_type, snapshot_utc, raw_json)
    VALUES (%s, NOW(), %s::jsonb);
    """
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (snapshot_type, json.dumps(raw_json)))


# =============================================================================
# 7) Anchor resolution (Hotel address -> lat/lng)
# =============================================================================

def resolve_address_to_latlng(
    address: str,
    country_code: str,
    region_code: str,
    language_code: str,
) -> Tuple[bool, Optional[Tuple[float, float]], Optional[str], Optional[str]]:
    """
    Resolve a human-readable address to (lat, lng) using Google Geocoding API.

    Returns:
      (ok, (lat,lng) or None, formatted_address or None, error_str or None)

    Why this is required:
      - Places "nearby" queries must use lat/lng
      - This avoids “server location drift”
      - This avoids hard-coding “Osaka” or other city text hacks

    We strongly restrict to the intended country using:
      components=country:JP   (hard restriction)
    And provide a region bias:
      region=JP
    """
    cache_key = f"geocode:{country_code}:{region_code}:{language_code}:{address}"
    cached = cache_get(cache_key)
    if cached:
        return True, cached["latlng"], cached.get("formatted_address"), None

    params = {
        "address": address,
        "key": GOOGLE_PLACES_API_KEY,
        "language": language_code,
        "region": region_code.lower(),
        "components": f"country:{country_code}",
    }

    try:
        resp = requests.get(GEOCODE_URL, params=params, timeout=20)
        data = resp.json() if resp.content else {}
    except Exception as e:
        return False, None, None, f"geocode_http_error:{type(e).__name__}:{e}"

    if data.get("status") != "OK":
        return False, None, None, f"geocode_status:{data.get('status')}:{data.get('error_message')}"

    results = data.get("results") or []
    if not results:
        return False, None, None, "geocode_no_results"

    top = results[0]
    loc = (top.get("geometry") or {}).get("location") or {}
    lat = loc.get("lat")
    lng = loc.get("lng")
    if lat is None or lng is None:
        return False, None, None, "geocode_missing_latlng"

    formatted = top.get("formatted_address")

    out = {"latlng": (float(lat), float(lng)), "formatted_address": formatted}
    cache_set(cache_key, out, ttl_s=3600)
    return True, out["latlng"], formatted, None


# =============================================================================
# 8) Core ingest logic
# =============================================================================

def ingest_from_seed(seed: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ingest one neighborhood seed definition.

    Seed includes:
      - neighborhood id
      - city/country
      - anchor: { address: "..."} OR { location: {lat,lng} }
      - categories: list of category search definitions

    Returns stats dict for observability.
    """
    stats = {
        "neighborhoods": 0,
        "categories": 0,
        "places_discovered": 0,
        "places_enriched": 0,
        "errors": 0,
        "anchor_resolved": 0,
        "anchor_failures": 0,
        "filtered_country_mismatch": 0,
    }

    neighborhood_id = seed.get("id") or "unknown_neighborhood"
    city = seed.get("city") or "unknown_city"
    country = seed.get("country") or GOOGLE_REGION

    # --- Resolve anchor lat/lng ---
    anchor = seed.get("anchor") or {}
    anchor_loc = anchor.get("location") or {}
    lat = anchor_loc.get("lat")
    lng = anchor_loc.get("lng")

    if lat is None or lng is None:
        address = anchor.get("address")
        if not address:
            stats["errors"] += 1
            stats["anchor_failures"] += 1
            snapshot_raw("anchor_error", {
                "error": "seed_missing_anchor_location_and_address",
                "neighborhood_id": neighborhood_id,
                "seed": seed,
            })
            return stats

        ok, latlng, formatted, err = resolve_address_to_latlng(
            address=address,
            country_code=country,
            region_code=GOOGLE_REGION,
            language_code=GOOGLE_LANGUAGE,
        )
        if not ok or not latlng:
            stats["errors"] += 1
            stats["anchor_failures"] += 1
            snapshot_raw("anchor_error", {
                "error": err or "anchor_geocode_failed",
                "neighborhood_id": neighborhood_id,
                "address": address,
                "country": country,
                "region": GOOGLE_REGION,
                "language": GOOGLE_LANGUAGE,
            })
            return stats

        lat, lng = latlng
        stats["anchor_resolved"] += 1
        snapshot_raw("anchor_resolved", {
            "neighborhood_id": neighborhood_id,
            "address": address,
            "formatted_address": formatted,
            "country": country,
            "lat": lat,
            "lng": lng,
        })

    # Ingest each category
    radius_m = int(seed.get("radius_m") or DEFAULT_RADIUS_M)
    details_top_n = int(seed.get("details_top_n") or DEFAULT_DETAILS_TOP_N)

    categories = seed.get("categories") or []
    stats["neighborhoods"] += 1

    for cat in categories:
        stats["categories"] += 1
        mode = cat.get("mode")
        label = cat.get("label", "unknown")
        max_results = int(cat.get("max_results") or DEFAULT_MAX_RESULTS)

        discovered: List[Dict[str, Any]] = []

        try:
            if mode == "nearby":
                included_types = cat.get("included_types") or []
                resp = google_nearby_search(
                    lat=lat,
                    lng=lng,
                    radius_m=radius_m,
                    included_types=included_types,
                    max_results=max_results,
                    language_code=GOOGLE_LANGUAGE,
                    region_code=GOOGLE_REGION,
                )
                snapshot_raw("nearby", {
                    "neighborhood_id": neighborhood_id,
                    "city": city,
                    "country": country,
                    "category": cat,
                    "response": resp,
                })
                places = (resp.get("json") or {}).get("places") or []
                discovered = places

            elif mode == "textsearch":
                text_query = cat.get("text_query") or ""
                if not text_query:
                    raise ValueError("textsearch requires text_query")

                resp = google_text_search(
                    query=text_query,
                    lat=lat,
                    lng=lng,
                    radius_m=radius_m,
                    max_results=max_results,
                    language_code=GOOGLE_LANGUAGE,
                    region_code=GOOGLE_REGION,
                )
                # Store raw snapshot for debugging, including category
                snapshot_raw("textsearch", {
                    "neighborhood_id": neighborhood_id,
                    "city": city,
                    "country": country,
                    "category": cat,
                    "response": resp,
                })
                places = (resp.get("json") or {}).get("places") or []
                discovered = places
            else:
                raise ValueError(f"unknown category mode: {mode}")

        except Exception as e:
            stats["errors"] += 1
            snapshot_raw("category_error", {
                "neighborhood_id": neighborhood_id,
                "city": city,
                "country": country,
                "category": cat,
                "error": f"{type(e).__name__}:{e}",
            })
            continue

        stats["places_discovered"] += len(discovered)

        # Rank and take top N for details
        ranked = rank_places(discovered)
        top_for_details = ranked[:max(0, details_top_n)]

        for p in top_for_details:
            place_id = p.get("id")
            if not place_id:
                continue

            # Details caching key
            cache_key = f"details:{place_id}:{GOOGLE_LANGUAGE}:{GOOGLE_REGION}"
            cached_details = cache_get(cache_key)

            if cached_details:
                details = cached_details
                status_code = 200
            else:
                details_resp = google_place_details(
                    place_id=place_id,
                    language_code=GOOGLE_LANGUAGE,
                    region_code=GOOGLE_REGION,
                )
                status_code = details_resp.get("status_code")
                details = details_resp.get("json") or {}
                snapshot_raw("details", details)
                if status_code == 200 and details:
                    cache_set(cache_key, details, ttl_s=3600)

            if status_code != 200 or not details:
                stats["errors"] += 1
                continue

            # --- Hygiene filter: enforce country match (minimum) ---
            # We do NOT hard-code "must include Osaka".
            # We only enforce "must be Japan" (JP) by checking addressComponents.
            if GOOGLE_HYGIENE_COUNTRY:
                comps = details.get("addressComponents") or []
                found_country = None
                for c in comps:
                    t = c.get("types") or []
                    if "country" in t:
                        found_country = (c.get("shortText") or c.get("short_name") or "").strip()
                        break

                if found_country and found_country.upper() != GOOGLE_HYGIENE_COUNTRY.upper():
                    stats["filtered_country_mismatch"] += 1
                    snapshot_raw("filtered_country_mismatch", {
                        "place_id": place_id,
                        "expected_country": GOOGLE_HYGIENE_COUNTRY,
                        "found_country": found_country,
                        "details": details,
                    })
                    continue

            # Persist the enriched place
            try:
                upsert_place(
                    place_id=place_id,
                    details_json=details,
                    nearby_json=p,
                    source_neighborhood_id=neighborhood_id,
                    source_city=city,
                    source_country=country,
                )
                stats["places_enriched"] += 1
            except Exception as e:
                stats["errors"] += 1
                snapshot_raw("db_upsert_error", {
                    "place_id": place_id,
                    "neighborhood_id": neighborhood_id,
                    "error": f"{type(e).__name__}:{e}",
                })

    return stats


# =============================================================================
# 9) Flask app + routes
# =============================================================================

app = Flask(__name__)


@app.get("/health")
def health():
    """
    Health endpoint for Traefik / monitoring.

    Returns:
      - ok: service is up
      - google_key_set: whether API key exists
      - db_ok: ability to run SELECT 1
      - defaults: shows current masks/region/lang for fast debugging
    """
    ok_db, db_err = db_health()
    return jsonify(
        {
            "ok": True,
            "time": int(time.time()),
            "google_key_set": bool(GOOGLE_PLACES_API_KEY),
            "db": {
                "host": PGHOST,
                "port": PGPORT,
                "database": PGDATABASE,
                "user": PGUSER,
            },
            "db_ok": ok_db,
            "db_error": db_err,
            "defaults": {
                "region": GOOGLE_REGION,
                "lang": GOOGLE_LANGUAGE,
                "nearby_fieldmask": DEFAULT_NEARBY_FIELDMASK,
                "details_fieldmask": DEFAULT_DETAILS_FIELDMASK,
            },
        }
    )


@app.get("/v1/details/<place_id>")
def details(place_id: str):
    """
    Convenience endpoint: fetch details for a place_id and return JSON.
    Useful for quick validation during development.
    """
    r = google_place_details(place_id, GOOGLE_LANGUAGE, GOOGLE_REGION)
    return jsonify(r), (200 if r.get("status_code") == 200 else 400)


@app.get("/v1/nearby")
def nearby():
    """
    Convenience endpoint: run a nearby query with querystring params:
      lat, lng, radius_m, included_types (comma)
    """
    lat = float(request.args.get("lat", "0"))
    lng = float(request.args.get("lng", "0"))
    radius_m = int(request.args.get("radius_m", str(DEFAULT_RADIUS_M)))
    included_types_raw = request.args.get("included_types", "")
    included_types = [x.strip() for x in included_types_raw.split(",") if x.strip()] if included_types_raw else []

    r = google_nearby_search(
        lat=lat,
        lng=lng,
        radius_m=radius_m,
        included_types=included_types,
        max_results=DEFAULT_MAX_RESULTS,
        language_code=GOOGLE_LANGUAGE,
        region_code=GOOGLE_REGION,
    )
    return jsonify(r), (200 if r.get("status_code") in (200, 400) else 500)


@app.post("/v1/ingest/seeds")
def ingest_seeds():
    """
    Primary MVP endpoint.

    Loads the seed JSON file and ingests it into Postgres.
    """
    try:
        with open(SEEDS_PATH, "r", encoding="utf-8") as f:
            seeds_obj = json.load(f)
    except Exception as e:
        return jsonify({"ok": False, "error": f"failed_to_load_seeds:{type(e).__name__}:{e}", "seeds_path": SEEDS_PATH}), 500

    # Expected schema:
    # {
    #   "version": 1,
    #   "provider": "google",
    #   "cities": [
    #      { "city":"Osaka", "country":"JP", "neighborhoods":[ ... ] }
    #   ]
    # }
    cities = seeds_obj.get("cities") or []
    total_stats = {
        "ok": True,
        "stats": {
            "neighborhoods": 0,
            "categories": 0,
            "places_discovered": 0,
            "places_enriched": 0,
            "errors": 0,
            "anchor_resolved": 0,
            "anchor_failures": 0,
            "filtered_country_mismatch": 0,
        },
    }

    for city_obj in cities:
        city_name = city_obj.get("city") or "unknown_city"
        country = city_obj.get("country") or GOOGLE_REGION
        neighborhoods = city_obj.get("neighborhoods") or []

        for n in neighborhoods:
            # Normalize seed to what ingest_from_seed expects
            seed = dict(n)
            seed["city"] = city_name
            seed["country"] = country

            s = ingest_from_seed(seed)
            for k, v in s.items():
                total_stats["stats"][k] = total_stats["stats"].get(k, 0) + int(v)

    return jsonify(total_stats), 200


# =============================================================================
# 10) Entrypoint (Gunicorn)
# =============================================================================

def main():
    """
    Run with Gunicorn for a “production-ish” behavior in Docker.
    """
    from gunicorn.app.base import BaseApplication

    class StandaloneApplication(BaseApplication):
        def __init__(self, flask_app, options=None):
            self.options = options or {}
            self.application = flask_app
            super().__init__()

        def load_config(self):
            for k, v in self.options.items():
                self.cfg.set(k, v)

        def load(self):
            return self.application

    options = {
        "bind": f"0.0.0.0:{PORT}",
        "workers": 2,
        "timeout": 60,
        "loglevel": LOG_LEVEL.lower(),
    }
    StandaloneApplication(app, options).run()


if __name__ == "__main__":
    main()
