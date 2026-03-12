"""
Shogun Places (Google) Microservice
==================================

Goal (MVP2):
- Take "seed neighborhoods" (hotel address + categories) and ingest places into Postgres.
- CRITICAL: All results must be anchored to the neighborhood's *physical location in Japan*,
  NOT influenced by where the service is running (e.g., your datacenter in California).

This service enforces the design decisions you confirmed:

1) Anchor resolution (address -> lat/lng):
   - Uses Google Geocoding API
   - Hard restrict: components=country:JP
   - Bias: region=JP

2) Hybrid hygiene:
   - If the seed neighborhood's country == "JP" => STRICT mode:
       * If we cannot resolve a JP anchor, ingestion fails for that neighborhood.
       * If results are not in JP, they are filtered out.
   - Otherwise => SOFT mode (future "California mode"):
       * We still ingest, but we keep the filtering rules looser.

3) DB is the source of truth for resolved anchors:
   - Once an anchor is resolved, it's stored in Postgres.
   - Next runs do NOT re-guess (unless forced).

Why your Rocklin bug happened previously:
- TextSearch without a location bias/restriction is effectively "ramen anywhere".
- Even if you provide a Japan-looking address, if you never resolved it into a specific
  JP lat/lng and never used locationBias/locationRestriction, Google can return "relevance"
  results near the requester/service context.
- Fix = Resolve address -> lat/lng (JP) + always use locationRestriction/bias around anchor.

Deployment model:
- You develop on Windows -> commit/push -> pull on svcnode-01 -> docker compose up --build.
"""

from __future__ import annotations

import json
import os
import time
import traceback
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import psycopg2
import psycopg2.extras
import requests
from flask import Flask, jsonify, request


# ---------------------------------------------------------------------
# Environment / Configuration
# ---------------------------------------------------------------------

def _env(name: str, default: Optional[str] = None) -> str:
    v = os.getenv(name)
    if v is None or str(v).strip() == "":
        if default is None:
            raise RuntimeError(f"Missing required env var: {name}")
        return default
    return str(v).strip()


def _env_int(name: str, default: int) -> int:
    v = os.getenv(name)
    if v is None or str(v).strip() == "":
        return default
    return int(v)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class AppConfig:
    # Database
    pg_host: str
    pg_port: int
    pg_database: str
    pg_user: str
    pg_password: str

    # Gateway
    gateway_url: str

    # Defaults for Places payload shaping
    default_lang: str = "en"
    default_region: str = "JP"

    # Field masks (cost control)
    # NOTE: Field masks are your primary lever to reduce cost.
    details_fieldmask: str = (
        "id,displayName,formattedAddress,location,googleMapsUri,websiteUri,"
        "internationalPhoneNumber,rating,userRatingCount,priceLevel,primaryType,types,"
        "regularOpeningHours,paymentOptions,addressComponents"
    )
    nearby_fieldmask: str = (
        "places.id,places.displayName,places.location,places.types,places.rating,"
        "places.userRatingCount,places.priceLevel,places.primaryType,places.googleMapsUri,"
        "places.formattedAddress"
    )

    # Seeds
    seeds_path_primary: str = "/app/seeds/neighborhoods.json"
    seeds_path_example: str = "/app/seeds/neighborhoods.example.json"


CONFIG = AppConfig(
    pg_host=_env("PGHOST"),
    pg_port=_env_int("PGPORT", 5432),
    pg_database=_env("PGDATABASE"),
    pg_user=_env("PGUSER"),
    pg_password=_env("PGPASSWORD"),
    gateway_url=_env("PLACES_GATEWAY_URL", "http://places.platform.ibbytech.com").rstrip("/"),
)


# ---------------------------------------------------------------------
# Flask App + Simple Error Capture
# ---------------------------------------------------------------------

app = Flask(__name__)

_LAST_ERROR: Optional[str] = None
_LAST_ERROR_AT_UTC: Optional[str] = None


def _set_last_error(msg: str) -> None:
    global _LAST_ERROR, _LAST_ERROR_AT_UTC
    _LAST_ERROR = msg
    _LAST_ERROR_AT_UTC = _utc_now().isoformat()


@app.errorhandler(Exception)
def _handle_exception(e: Exception):
    """
    Hard rule: never silently swallow errors.
    When you get a 500, you should see a usable stack trace in Docker logs,
    and you should also see a summarized error in /health.
    """
    tb = traceback.format_exc()
    _set_last_error(f"{type(e).__name__}: {e}")
    # Print for Docker logs
    print("=== UNHANDLED EXCEPTION ===")
    print(tb)
    return jsonify({
        "ok": False,
        "error": f"{type(e).__name__}: {str(e)}",
        "time": int(time.time()),
    }), 500


# ---------------------------------------------------------------------
# DB Helpers
# ---------------------------------------------------------------------

def db_connect():
    """
    Creates a new DB connection. We keep it simple for MVP2.
    If you later want pooling, we'd add it (psycopg_pool or pgbouncer).
    """
    return psycopg2.connect(
        host=CONFIG.pg_host,
        port=CONFIG.pg_port,
        dbname=CONFIG.pg_database,
        user=CONFIG.pg_user,
        password=CONFIG.pg_password,
        connect_timeout=5,
        sslmode="prefer",  # keeps it compatible with your pg_hba rules
    )


def db_ping() -> Tuple[bool, Optional[str]]:
    try:
        conn = db_connect()
        cur = conn.cursor()
        cur.execute("select 1;")
        cur.fetchone()
        conn.close()
        return True, None
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"


def db_bootstrap_schema() -> None:
    """
    Ensures anchor storage exists. Your project already created:
      - places.google_places
      - places.google_place_snapshots
    But MVP2 also needs a table to store resolved neighborhood anchors.
    """
    sql = """
    CREATE SCHEMA IF NOT EXISTS places;

    CREATE TABLE IF NOT EXISTS places.neighborhood_anchors (
      provider                text not null,
      neighborhood_id         text not null,
      city                    text,
      country                 text,
      input_address           text,
      resolved_place_id       text,
      resolved_formatted_addr text,
      resolved_country        text,
      lat                     double precision,
      lng                     double precision,
      resolution_method       text,
      raw_geocode_json        jsonb,
      created_utc             timestamptz not null default now(),
      updated_utc             timestamptz not null default now(),
      PRIMARY KEY (provider, neighborhood_id)
    );

    CREATE INDEX IF NOT EXISTS idx_neighborhood_anchors_country
      ON places.neighborhood_anchors (country);
    """
    conn = db_connect()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(sql)
    finally:
        conn.close()


def db_upsert_anchor(
    neighborhood_id: str,
    city: str,
    country: str,
    input_address: str,
    resolved_place_id: Optional[str],
    resolved_formatted_addr: Optional[str],
    resolved_country: Optional[str],
    lat: float,
    lng: float,
    resolution_method: str,
    raw_geocode_json: Dict[str, Any],
) -> None:
    sql = """
    INSERT INTO places.neighborhood_anchors (
      provider, neighborhood_id, city, country, input_address,
      resolved_place_id, resolved_formatted_addr, resolved_country,
      lat, lng, resolution_method, raw_geocode_json, created_utc, updated_utc
    )
    VALUES (
      'google', %(neighborhood_id)s, %(city)s, %(country)s, %(input_address)s,
      %(resolved_place_id)s, %(resolved_formatted_addr)s, %(resolved_country)s,
      %(lat)s, %(lng)s, %(resolution_method)s, %(raw_geocode_json)s::jsonb,
      now(), now()
    )
    ON CONFLICT (provider, neighborhood_id)
    DO UPDATE SET
      city = EXCLUDED.city,
      country = EXCLUDED.country,
      input_address = EXCLUDED.input_address,
      resolved_place_id = EXCLUDED.resolved_place_id,
      resolved_formatted_addr = EXCLUDED.resolved_formatted_addr,
      resolved_country = EXCLUDED.resolved_country,
      lat = EXCLUDED.lat,
      lng = EXCLUDED.lng,
      resolution_method = EXCLUDED.resolution_method,
      raw_geocode_json = EXCLUDED.raw_geocode_json,
      updated_utc = now();
    """
    conn = db_connect()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(sql, {
                    "neighborhood_id": neighborhood_id,
                    "city": city,
                    "country": country,
                    "input_address": input_address,
                    "resolved_place_id": resolved_place_id,
                    "resolved_formatted_addr": resolved_formatted_addr,
                    "resolved_country": resolved_country,
                    "lat": lat,
                    "lng": lng,
                    "resolution_method": resolution_method,
                    "raw_geocode_json": json.dumps(raw_geocode_json),
                })
    finally:
        conn.close()


def db_get_anchor(neighborhood_id: str) -> Optional[Dict[str, Any]]:
    sql = """
    SELECT provider, neighborhood_id, city, country,
           input_address, resolved_place_id, resolved_formatted_addr,
           resolved_country, lat, lng, resolution_method, raw_geocode_json,
           created_utc, updated_utc
    FROM places.neighborhood_anchors
    WHERE provider='google' AND neighborhood_id=%s;
    """
    conn = db_connect()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, (neighborhood_id,))
            row = cur.fetchone()
            return dict(row) if row else None
    finally:
        conn.close()


# ---------------------------------------------------------------------
# Seeds Loading
# ---------------------------------------------------------------------

def load_seeds_from_disk() -> Dict[str, Any]:
    """
    Loads seeds JSON from /app/seeds.
    You can later add a new endpoint to upload/replace seeds,
    but for MVP2 this is file-based and Git-controlled.
    """
    path = CONFIG.seeds_path_primary
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    # fallback to example
    path = CONFIG.seeds_path_example
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    raise RuntimeError(
        "No seeds file found. Expected one of:\n"
        f"- {CONFIG.seeds_path_primary}\n"
        f"- {CONFIG.seeds_path_example}\n"
        "Fix by ensuring seeds are included in the image and exist at /app/seeds."
    )


# ---------------------------------------------------------------------
# Google APIs - Anchor Geocoding
# ---------------------------------------------------------------------

def google_geocode_address_jp(address: str) -> Dict[str, Any]:
    url = f"{CONFIG.gateway_url}/v1/places/geocode"
    params = {
        "address": address,
        "components": "country:JP",
        "region": "JP",
    }
    r = requests.get(url, params=params, timeout=20)
    r.raise_for_status()
    resp = r.json()
    if not resp.get("ok"):
        raise RuntimeError(f"Gateway geocode failed: {resp.get('error')}")
    return resp.get("data", {})


def extract_geocode_best_result(geo_json: Dict[str, Any]) -> Tuple[float, float, str, Optional[str]]:
    """
    Returns:
      lat, lng, formatted_address, country_short (e.g. 'JP')
    """
    status = geo_json.get("status")
    if status != "OK":
        raise RuntimeError(f"Geocode failed: status={status}, error={geo_json.get('error_message')}")

    results = geo_json.get("results") or []
    if not results:
        raise RuntimeError("Geocode returned OK but results list is empty.")

    best = results[0]
    loc = best["geometry"]["location"]
    lat = float(loc["lat"])
    lng = float(loc["lng"])
    formatted = best.get("formatted_address", "")

    # Parse country component (short_name)
    country_short = None
    for c in best.get("address_components", []):
        types = c.get("types") or []
        if "country" in types:
            country_short = c.get("short_name")
            break

    return lat, lng, formatted, country_short


# ---------------------------------------------------------------------
# Google Places API (New) - Search helpers
# ---------------------------------------------------------------------

GOOGLE_PLACES_BASE = "https://places.googleapis.com/v1"

def google_places_text_search(
    text_query: str,
    lat: float,
    lng: float,
    radius_m: int,
    max_results: int,
    region_code: str,
    language_code: str,
) -> Dict[str, Any]:
    url = f"{CONFIG.gateway_url}/v1/places/search_text"
    body = {
        "text_query": text_query,
        "lat": lat,
        "lng": lng,
        "radius_m": radius_m,
        "max_results": max_results,
        "region_code": region_code,
        "language_code": language_code,
    }
    r = requests.post(url, json=body, timeout=30)
    r.raise_for_status()
    resp = r.json()
    if not resp.get("ok"):
        raise RuntimeError(f"Gateway error: {resp.get('error')}")
    return resp.get("data", {})


def google_places_nearby_search(
    included_types: List[str],
    lat: float,
    lng: float,
    radius_m: int,
    max_results: int,
    region_code: str,
    language_code: str,
) -> Dict[str, Any]:
    url = f"{CONFIG.gateway_url}/v1/places/nearby"
    body = {
        "included_types": included_types,
        "lat": lat,
        "lng": lng,
        "radius_m": radius_m,
        "max_results": max_results,
        "region_code": region_code,
        "language_code": language_code,
    }
    r = requests.post(url, json=body, timeout=30)
    r.raise_for_status()
    resp = r.json()
    if not resp.get("ok"):
        raise RuntimeError(f"Gateway error: {resp.get('error')}")
    return resp.get("data", {})


def google_places_details(place_id: str, language_code: str, region_code: str) -> Dict[str, Any]:
    url = f"{CONFIG.gateway_url}/v1/places/details/{place_id}"
    params = {
        "language_code": language_code,
        "region_code": region_code,
    }
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    resp = r.json()
    if not resp.get("ok"):
        raise RuntimeError(f"Gateway error: {resp.get('error')}")
    return resp.get("data", {})


def place_country_from_address_components(details_json: Dict[str, Any]) -> Optional[str]:
    """
    Extracts country shortName if present.
    With Places (New), addressComponents include 'shortText' sometimes.
    We store the whole json for forensics.
    """
    comps = details_json.get("addressComponents") or []
    for c in comps:
        types = c.get("types") or []
        if "country" in types:
            # Places uses 'shortText' / 'longText' often
            short = c.get("shortText") or c.get("shortName") or c.get("short_text")
            if isinstance(short, str) and short.strip():
                return short.strip()
    return None


# ---------------------------------------------------------------------
# DB Writes for Places + Snapshots
# ---------------------------------------------------------------------

def db_insert_snapshot(snapshot_type: str, category_obj: Dict[str, Any], raw_json: Dict[str, Any]) -> None:
    """
    Records raw API payloads for debugging and audit.
    """
    sql = """
    INSERT INTO places.google_place_snapshots (snapshot_type, snapshot_utc, raw_json)
    VALUES (%s, now(), %s::jsonb);
    """
    payload = dict(raw_json)
    payload["category"] = category_obj  # attach category metadata
    conn = db_connect()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(sql, (snapshot_type, json.dumps(payload)))
    finally:
        conn.close()


def db_upsert_place(
    neighborhood_id: str,
    city: str,
    country: str,
    nearby_place: Dict[str, Any],
    details_json: Optional[Dict[str, Any]],
    raw_nearby_json: Dict[str, Any],
) -> None:
    """
    Upserts a place into places.google_places.
    Primary key is place_id.
    """
    place_id = nearby_place.get("id") or nearby_place.get("placeId")
    if not place_id:
        return

    # Pull fields from details if present; fall back to nearby where possible
    def _safe_text(x: Any) -> Optional[str]:
        if isinstance(x, str) and x.strip():
            return x.strip()
        return None

    display_name = None
    dn = (details_json or {}).get("displayName") or nearby_place.get("displayName")
    if isinstance(dn, dict):
        display_name = _safe_text(dn.get("text"))
    elif isinstance(dn, str):
        display_name = _safe_text(dn)

    formatted_address = _safe_text((details_json or {}).get("formattedAddress") or nearby_place.get("formattedAddress"))

    location = (details_json or {}).get("location") or nearby_place.get("location") or {}
    lat = location.get("latitude")
    lng = location.get("longitude")

    google_maps_uri = _safe_text((details_json or {}).get("googleMapsUri") or nearby_place.get("googleMapsUri"))
    website_uri = _safe_text((details_json or {}).get("websiteUri"))
    international_phone = _safe_text((details_json or {}).get("internationalPhoneNumber"))
    primary_type = _safe_text((details_json or {}).get("primaryType") or nearby_place.get("primaryType"))
    types = (details_json or {}).get("types") or nearby_place.get("types")
    rating = (details_json or {}).get("rating") or nearby_place.get("rating")
    user_rating_count = (details_json or {}).get("userRatingCount") or nearby_place.get("userRatingCount")
    price_level = _safe_text((details_json or {}).get("priceLevel") or nearby_place.get("priceLevel"))

    # Opening hours & openNow (if present)
    opening_hours_json = (details_json or {}).get("regularOpeningHours")
    open_now = None
    if isinstance(opening_hours_json, dict):
        open_now = opening_hours_json.get("openNow")

    payment_options_json = (details_json or {}).get("paymentOptions")

    # Track fetch times
    details_fetch = _utc_now() if details_json else None
    nearby_fetch = _utc_now()

    sql = """
    INSERT INTO places.google_places (
      place_id, display_name, primary_type, types, formatted_address,
      lat, lng, google_maps_uri, website_uri, international_phone,
      rating, user_rating_count, price_level, open_now,
      opening_hours_json, payment_options_json,
      source_neighborhood_id, source_city, source_country,
      last_details_fetch_utc, last_nearby_fetch_utc,
      raw_details_json, raw_nearby_json,
      created_utc, updated_utc
    )
    VALUES (
      %(place_id)s, %(display_name)s, %(primary_type)s, %(types)s, %(formatted_address)s,
      %(lat)s, %(lng)s, %(google_maps_uri)s, %(website_uri)s, %(international_phone)s,
      %(rating)s, %(user_rating_count)s, %(price_level)s, %(open_now)s,
      %(opening_hours_json)s::jsonb, %(payment_options_json)s::jsonb,
      %(source_neighborhood_id)s, %(source_city)s, %(source_country)s,
      %(last_details_fetch_utc)s, %(last_nearby_fetch_utc)s,
      %(raw_details_json)s::jsonb, %(raw_nearby_json)s::jsonb,
      now(), now()
    )
    ON CONFLICT (place_id)
    DO UPDATE SET
      display_name = EXCLUDED.display_name,
      primary_type = EXCLUDED.primary_type,
      types = EXCLUDED.types,
      formatted_address = EXCLUDED.formatted_address,
      lat = EXCLUDED.lat,
      lng = EXCLUDED.lng,
      google_maps_uri = EXCLUDED.google_maps_uri,
      website_uri = COALESCE(EXCLUDED.website_uri, places.google_places.website_uri),
      international_phone = COALESCE(EXCLUDED.international_phone, places.google_places.international_phone),
      rating = EXCLUDED.rating,
      user_rating_count = EXCLUDED.user_rating_count,
      price_level = EXCLUDED.price_level,
      open_now = EXCLUDED.open_now,
      opening_hours_json = COALESCE(EXCLUDED.opening_hours_json, places.google_places.opening_hours_json),
      payment_options_json = COALESCE(EXCLUDED.payment_options_json, places.google_places.payment_options_json),
      source_neighborhood_id = EXCLUDED.source_neighborhood_id,
      source_city = EXCLUDED.source_city,
      source_country = EXCLUDED.source_country,
      last_details_fetch_utc = COALESCE(EXCLUDED.last_details_fetch_utc, places.google_places.last_details_fetch_utc),
      last_nearby_fetch_utc = EXCLUDED.last_nearby_fetch_utc,
      raw_details_json = COALESCE(EXCLUDED.raw_details_json, places.google_places.raw_details_json),
      raw_nearby_json = EXCLUDED.raw_nearby_json,
      updated_utc = now();
    """
    conn = db_connect()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(sql, {
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
                    "opening_hours_json": json.dumps(opening_hours_json) if opening_hours_json is not None else None,
                    "payment_options_json": json.dumps(payment_options_json) if payment_options_json is not None else None,
                    "source_neighborhood_id": neighborhood_id,
                    "source_city": city,
                    "source_country": country,
                    "last_details_fetch_utc": details_fetch,
                    "last_nearby_fetch_utc": nearby_fetch,
                    "raw_details_json": json.dumps(details_json) if details_json is not None else None,
                    "raw_nearby_json": json.dumps(raw_nearby_json),
                })
    finally:
        conn.close()


# ---------------------------------------------------------------------
# Ingest Orchestration
# ---------------------------------------------------------------------

def resolve_or_get_anchor(
    neighborhood_id: str,
    city: str,
    country: str,
    address: str,
    strict_if_country_is_jp: bool = True,
    force: bool = False,
) -> Tuple[bool, Optional[float], Optional[float], Optional[str]]:
    """
    Returns:
      ok, lat, lng, reason

    - If anchor exists in DB and force=False -> return it.
    - Otherwise geocode address (JP) and store result.
    - STRICT logic (Japan seeds):
        If country == "JP" and resolved_country != "JP" -> fail.
    """
    existing = None if force else db_get_anchor(neighborhood_id)
    if existing and existing.get("lat") is not None and existing.get("lng") is not None:
        return True, float(existing["lat"]), float(existing["lng"]), "anchor_from_db"

    geo = google_geocode_address_jp(address)
    lat, lng, formatted, resolved_country = extract_geocode_best_result(geo)

    # STRICT if JP seed
    strict_mode = strict_if_country_is_jp and (country.upper() == "JP")
    if strict_mode and (resolved_country is None or resolved_country.upper() != "JP"):
        # Store for forensics, but return failure
        db_upsert_anchor(
            neighborhood_id=neighborhood_id,
            city=city,
            country=country,
            input_address=address,
            resolved_place_id=None,
            resolved_formatted_addr=formatted,
            resolved_country=resolved_country,
            lat=lat,
            lng=lng,
            resolution_method="geocoding_api_components_country_jp",
            raw_geocode_json=geo,
        )
        return False, None, None, f"STRICT_JP: geocode resolved_country={resolved_country} not JP"

    db_upsert_anchor(
        neighborhood_id=neighborhood_id,
        city=city,
        country=country,
        input_address=address,
        resolved_place_id=None,
        resolved_formatted_addr=formatted,
        resolved_country=resolved_country,
        lat=lat,
        lng=lng,
        resolution_method="geocoding_api_components_country_jp",
        raw_geocode_json=geo,
    )
    return True, lat, lng, "anchor_geocoded_and_stored"


def ingest_one_neighborhood(
    city: str,
    country: str,
    neighborhood: Dict[str, Any],
    defaults: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Ingests one neighborhood:
    1) Resolve anchor
    2) For each category: discover places (textsearch or nearby)
    3) For each place: fetch details
    4) Write snapshots + upsert place rows
    """
    stats = {
        "neighborhood_id": neighborhood.get("id"),
        "anchor_resolved": 0,
        "anchor_failures": 0,
        "categories": 0,
        "places_discovered": 0,
        "places_enriched": 0,
        "filtered_country_mismatch": 0,
        "errors": 0,
        "error_messages": [],
    }

    nid = neighborhood.get("id")
    if not nid:
        stats["errors"] += 1
        stats["error_messages"].append("Neighborhood missing id")
        return stats

    anchor = neighborhood.get("anchor") or {}
    address = (anchor.get("address") or "").strip()
    if not address:
        stats["errors"] += 1
        stats["error_messages"].append(f"Neighborhood {nid} missing anchor.address")
        return stats

    strict_mode = (country.upper() == "JP")

    ok, lat, lng, reason = resolve_or_get_anchor(
        neighborhood_id=nid,
        city=city,
        country=country,
        address=address,
        strict_if_country_is_jp=True,
        force=False,
    )
    if not ok:
        stats["anchor_failures"] += 1
        stats["errors"] += 1
        stats["error_messages"].append(f"Anchor resolution failed: {reason}")
        return stats

    stats["anchor_resolved"] += 1

    radius_m = int(neighborhood.get("radius_m") or defaults.get("default_radius_m") or 2000)
    details_top_n = int(neighborhood.get("details_top_n") or defaults.get("default_details_top_n") or 50)
    max_results_default = int(defaults.get("default_max_results") or 50)

    language_code = defaults.get("lang") or CONFIG.default_lang
    region_code = defaults.get("region") or CONFIG.default_region

    categories = neighborhood.get("categories") or []
    for cat in categories:
        try:
            stats["categories"] += 1
            mode = (cat.get("mode") or "").strip().lower()
            label = (cat.get("label") or "unknown").strip()
            max_results = int(cat.get("max_results") or max_results_default)

            # Discover places
            if mode == "textsearch":
                text_query = (cat.get("text_query") or "").strip()
                if not text_query:
                    stats["errors"] += 1
                    stats["error_messages"].append(f"Category {label}: textsearch missing text_query")
                    continue
                nearby_raw = google_places_text_search(
                    text_query=text_query,
                    lat=lat,
                    lng=lng,
                    radius_m=radius_m,
                    max_results=max_results,
                    region_code=region_code,
                    language_code=language_code,
                )
                places_list = nearby_raw.get("places") or []

            elif mode == "nearby":
                included_types = cat.get("included_types") or []
                if not included_types:
                    stats["errors"] += 1
                    stats["error_messages"].append(f"Category {label}: nearby missing included_types")
                    continue
                nearby_raw = google_places_nearby_search(
                    included_types=included_types,
                    lat=lat,
                    lng=lng,
                    radius_m=radius_m,
                    max_results=max_results,
                    region_code=region_code,
                    language_code=language_code,
                )
                places_list = nearby_raw.get("places") or []

            else:
                stats["errors"] += 1
                stats["error_messages"].append(f"Category {label}: unknown mode={mode}")
                continue

            stats["places_discovered"] += len(places_list)

            # Snapshot the discovery payload
            db_insert_snapshot(
                snapshot_type="discover",
                category_obj={"city": city, "country": country, "neighborhood_id": nid, **cat},
                raw_json={"places": places_list, "raw": nearby_raw},
            )

            # Enrich places with details (top N)
            # NOTE: For MVP2, we enrich up to details_top_n. Later we can add caching/refresh logic.
            to_enrich = places_list[:details_top_n]
            for p in to_enrich:
                place_id = p.get("id")
                if not place_id:
                    continue

                details = google_places_details(
                    place_id=place_id,
                    language_code=language_code,
                    region_code=region_code,
                )

                # Country hygiene
                resolved_place_country = place_country_from_address_components(details)
                if strict_mode and resolved_place_country and resolved_place_country.upper() != "JP":
                    stats["filtered_country_mismatch"] += 1
                    continue

                # Snapshot details payload
                db_insert_snapshot(
                    snapshot_type="details",
                    category_obj={"city": city, "country": country, "neighborhood_id": nid, **cat},
                    raw_json=details,
                )

                db_upsert_place(
                    neighborhood_id=nid,
                    city=city,
                    country=country,
                    nearby_place=p,
                    details_json=details,
                    raw_nearby_json={"places": places_list, "raw": nearby_raw},
                )
                stats["places_enriched"] += 1

        except Exception as e:
            stats["errors"] += 1
            stats["error_messages"].append(f"Category error ({cat.get('label')}): {type(e).__name__}: {e}")

    return stats


def ingest_seeds() -> Dict[str, Any]:
    """
    Main ingestion entry:
    - loads seeds file
    - bootstraps DB anchor table
    - ingests each neighborhood
    """
    db_bootstrap_schema()

    seeds = load_seeds_from_disk()
    defaults = {
        "default_radius_m": seeds.get("default_radius_m", 2000),
        "default_details_top_n": seeds.get("default_details_top_n", 50),
        "default_max_results": seeds.get("default_max_results", 50),
        "lang": seeds.get("lang", CONFIG.default_lang),
        "region": seeds.get("region", CONFIG.default_region),
    }

    overall = {
        "ok": True,
        "stats": {
            "neighborhoods": 0,
            "anchor_resolved": 0,
            "anchor_failures": 0,
            "categories": 0,
            "places_discovered": 0,
            "places_enriched": 0,
            "filtered_country_mismatch": 0,
            "errors": 0,
        },
        "neighborhood_results": [],
    }

    cities = seeds.get("cities") or []
    for c in cities:
        city = (c.get("city") or "").strip()
        country = (c.get("country") or "").strip().upper()
        if not city or not country:
            overall["stats"]["errors"] += 1
            continue

        neighborhoods = c.get("neighborhoods") or []
        for n in neighborhoods:
            overall["stats"]["neighborhoods"] += 1
            res = ingest_one_neighborhood(city=city, country=country, neighborhood=n, defaults=defaults)
            overall["neighborhood_results"].append(res)

            # aggregate
            overall["stats"]["anchor_resolved"] += res.get("anchor_resolved", 0)
            overall["stats"]["anchor_failures"] += res.get("anchor_failures", 0)
            overall["stats"]["categories"] += res.get("categories", 0)
            overall["stats"]["places_discovered"] += res.get("places_discovered", 0)
            overall["stats"]["places_enriched"] += res.get("places_enriched", 0)
            overall["stats"]["filtered_country_mismatch"] += res.get("filtered_country_mismatch", 0)
            overall["stats"]["errors"] += res.get("errors", 0)

    if overall["stats"]["errors"] > 0:
        overall["ok"] = False
    return overall


# ---------------------------------------------------------------------
# HTTP Endpoints
# ---------------------------------------------------------------------

@app.get("/health")
def health():
    db_ok, db_err = db_ping()
    payload = {
        "ok": True,
        "time": int(time.time()),
        "google_key_set": bool(CONFIG.google_api_key),
        "db": {
            "host": CONFIG.pg_host,
            "port": CONFIG.pg_port,
            "database": CONFIG.pg_database,
            "user": CONFIG.pg_user,
        },
        "db_ok": db_ok,
        "db_error": db_err,
        "defaults": {
            "lang": CONFIG.default_lang,
            "region": CONFIG.default_region,
            "nearby_fieldmask": CONFIG.nearby_fieldmask,
            "details_fieldmask": CONFIG.details_fieldmask,
        },
        "last_error": _LAST_ERROR,
        "last_error_at_utc": _LAST_ERROR_AT_UTC,
    }
    return jsonify(payload)


@app.post("/v1/ingest/seeds")
def ingest_seeds_endpoint():
    """
    Runs ingestion using the on-disk seeds.
    Returns stats + per-neighborhood breakdown.
    """
    result = ingest_seeds()
    return jsonify(result)


# ---------------------------------------------------------------------
# Local dev entrypoint (optional)
# ---------------------------------------------------------------------
if __name__ == "__main__":
    # For local debugging only. In docker we run gunicorn.
    app.run(host="0.0.0.0", port=8081, debug=True)
