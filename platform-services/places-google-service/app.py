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

# ----------------------------
# Config
# ----------------------------

def _env(name: str, default: Optional[str] = None) -> str:
    v = os.getenv(name, default)
    if v is None:
        raise RuntimeError(f"Missing required env var: {name}")
    return v

PORT = int(os.getenv("PORT", "8081"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

GOOGLE_KEY = os.getenv("GOOGLE_PLACES_API_KEY", "")
GOOGLE_BASE = os.getenv("GOOGLE_PLACES_BASE_URL", "https://places.googleapis.com/v1")

NEARBY_FIELDMASK = os.getenv("GOOGLE_NEARBY_FIELDMASK", "places.id,places.displayName,places.location")
TEXT_FIELDMASK = os.getenv("GOOGLE_TEXTSEARCH_FIELDMASK", "places.id,places.displayName,places.location")
DETAILS_FIELDMASK = os.getenv("GOOGLE_DETAILS_FIELDMASK", "id,displayName,formattedAddress,location")

DEFAULT_LANG = os.getenv("DEFAULT_LANGUAGE_CODE", "en")
DEFAULT_REGION = os.getenv("DEFAULT_REGION_CODE", "JP")

PGHOST = _env("PGHOST", "dbnode-01")
PGPORT = int(os.getenv("PGPORT", "5432"))
PGDATABASE = _env("PGDATABASE", "shogun_v1")
PGUSER = _env("PGUSER", "places_app")
PGPASSWORD = _env("PGPASSWORD", "")

DEFAULT_DETAILS_TOP_N = int(os.getenv("DEFAULT_DETAILS_TOP_N", "75"))
DEFAULT_RADIUS_M = int(os.getenv("DEFAULT_RADIUS_M", "2000"))
DEFAULT_MAX_RESULTS = int(os.getenv("DEFAULT_MAX_RESULTS", "50"))

CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "86400"))

SEEDS_FILE = os.getenv("SEEDS_FILE", "./seeds/neighborhoods.example.json")

# ----------------------------
# Simple cache
# ----------------------------

@dataclass
class CacheEntry:
    expires_at: float
    value: Any

_cache: Dict[str, CacheEntry] = {}

def cache_get(key: str) -> Optional[Any]:
    e = _cache.get(key)
    if not e:
        return None
    if time.time() > e.expires_at:
        _cache.pop(key, None)
        return None
    return e.value

def cache_set(key: str, value: Any, ttl: int = CACHE_TTL_SECONDS) -> None:
    _cache[key] = CacheEntry(expires_at=time.time() + ttl, value=value)

# ----------------------------
# DB helpers
# ----------------------------

def db_conn():
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

def db_health() -> bool:
    try:
        with db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1;")
                _ = cur.fetchone()
        return True
    except Exception:
        return False

# ----------------------------
# Google Places API (New)
# ----------------------------

def _headers(fieldmask: str) -> Dict[str, str]:
    if not GOOGLE_KEY:
        raise RuntimeError("GOOGLE_PLACES_API_KEY is not set")
    # Note: No spaces allowed in fieldmask per docs
    return {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": GOOGLE_KEY,
        "X-Goog-FieldMask": fieldmask,
    }

def google_nearby_search(
    lat: float,
    lng: float,
    radius_m: int,
    included_types: List[str],
    max_results: int,
    language_code: str,
    region_code: str,
) -> Dict[str, Any]:
    url = f"{GOOGLE_BASE}/places:searchNearby"
    body = {
        "includedTypes": included_types,
        "maxResultCount": max_results,
        "languageCode": language_code,
        "regionCode": region_code,
        "locationRestriction": {
            "circle": {
                "center": {"latitude": lat, "longitude": lng},
                "radius": float(radius_m),
            }
        },
    }
    cache_key = f"nearby:{lat}:{lng}:{radius_m}:{','.join(included_types)}:{max_results}:{language_code}:{region_code}:{NEARBY_FIELDMASK}"
    cached = cache_get(cache_key)
    if cached is not None:
        return cached
    resp = requests.post(url, headers=_headers(NEARBY_FIELDMASK), json=body, timeout=20)
    resp.raise_for_status()
    data = resp.json()
    cache_set(cache_key, data)
    return data

def google_text_search(
    text_query: str,
    lat: Optional[float],
    lng: Optional[float],
    radius_m: Optional[int],
    max_results: int,
    language_code: str,
    region_code: str,
) -> Dict[str, Any]:
    url = f"{GOOGLE_BASE}/places:searchText"
    body: Dict[str, Any] = {
        "textQuery": text_query,
        "maxResultCount": max_results,
        "languageCode": language_code,
        "regionCode": region_code,
    }
    if lat is not None and lng is not None and radius_m is not None:
        body["locationBias"] = {
            "circle": {
                "center": {"latitude": lat, "longitude": lng},
                "radius": float(radius_m),
            }
        }

    cache_key = f"text:{text_query}:{lat}:{lng}:{radius_m}:{max_results}:{language_code}:{region_code}:{TEXT_FIELDMASK}"
    cached = cache_get(cache_key)
    if cached is not None:
        return cached
    resp = requests.post(url, headers=_headers(TEXT_FIELDMASK), json=body, timeout=20)
    resp.raise_for_status()
    data = resp.json()
    cache_set(cache_key, data)
    return data

def google_place_details(place_id: str, fieldmask: str) -> Dict[str, Any]:
    url = f"{GOOGLE_BASE}/places/{place_id}"
    cache_key = f"details:{place_id}:{fieldmask}"
    cached = cache_get(cache_key)
    if cached is not None:
        return cached
    resp = requests.get(url, headers=_headers(fieldmask), timeout=20)
    resp.raise_for_status()
    data = resp.json()
    cache_set(cache_key, data)
    return data

# ----------------------------
# Normalization + ranking
# ----------------------------

def _get_display_name(place: Dict[str, Any]) -> Optional[str]:
    dn = place.get("displayName")
    if isinstance(dn, dict):
        return dn.get("text")
    if isinstance(dn, str):
        return dn
    return None

def _get_location(place: Dict[str, Any]) -> Tuple[Optional[float], Optional[float]]:
    loc = place.get("location") or {}
    return loc.get("latitude"), loc.get("longitude")

def rank_places(places: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    # Score = rating * log10(userRatingCount+1). Simple, effective.
    def score(p: Dict[str, Any]) -> float:
        r = p.get("rating") or 0.0
        c = p.get("userRatingCount") or 0
        return float(r) * math.log10(float(c) + 1.0)

    return sorted(places, key=score, reverse=True)

# ----------------------------
# DB upsert
# ----------------------------

UPSERT_SQL = """
INSERT INTO places.google_places (
  place_id, display_name, primary_type, types, formatted_address, lat, lng,
  google_maps_uri, website_uri, international_phone,
  rating, user_rating_count, price_level,
  open_now, opening_hours_json, payment_options_json,
  source_neighborhood_id, source_city, source_country,
  last_details_fetch_utc, last_nearby_fetch_utc,
  raw_details_json, raw_nearby_json,
  updated_utc
)
VALUES (
  %(place_id)s, %(display_name)s, %(primary_type)s, %(types)s, %(formatted_address)s, %(lat)s, %(lng)s,
  %(google_maps_uri)s, %(website_uri)s, %(international_phone)s,
  %(rating)s, %(user_rating_count)s, %(price_level)s,
  %(open_now)s, %(opening_hours_json)s, %(payment_options_json)s,
  %(source_neighborhood_id)s, %(source_city)s, %(source_country)s,
  %(last_details_fetch_utc)s, %(last_nearby_fetch_utc)s,
  %(raw_details_json)s, %(raw_nearby_json)s,
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
  last_details_fetch_utc = COALESCE(EXCLUDED.last_details_fetch_utc, places.google_places.last_details_fetch_utc),
  last_nearby_fetch_utc = COALESCE(EXCLUDED.last_nearby_fetch_utc, places.google_places.last_nearby_fetch_utc),
  raw_details_json = COALESCE(EXCLUDED.raw_details_json, places.google_places.raw_details_json),
  raw_nearby_json = COALESCE(EXCLUDED.raw_nearby_json, places.google_places.raw_nearby_json),
  updated_utc = NOW();
"""

SNAPSHOT_SQL = """
INSERT INTO places.google_place_snapshots (place_id, snapshot_type, neighborhood_id, raw_json)
VALUES (%s, %s, %s, %s::jsonb);
"""

def upsert_place(
    details: Dict[str, Any],
    raw_nearby_or_text: Optional[Dict[str, Any]],
    neighborhood_id: Optional[str],
    city: Optional[str],
    country: str = "JP",
    from_nearby: bool = True,
) -> None:
    place_id = details.get("id")
    if not place_id:
        return

    display_name = _get_display_name(details)
    primary_type = details.get("primaryType")
    types = details.get("types") or None
    formatted_address = details.get("formattedAddress")
    lat, lng = _get_location(details)

    google_maps_uri = details.get("googleMapsUri")
    website_uri = details.get("websiteUri")
    international_phone = details.get("internationalPhoneNumber")

    rating = details.get("rating")
    user_rating_count = details.get("userRatingCount")
    price_level = details.get("priceLevel")

    regular_opening_hours = details.get("regularOpeningHours") or None
    payment_options = details.get("paymentOptions") or None

    open_now = None
    if isinstance(regular_opening_hours, dict):
        open_now = regular_opening_hours.get("openNow")

    row = {
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
        "opening_hours_json": json.dumps(regular_opening_hours) if regular_opening_hours is not None else None,
        "payment_options_json": json.dumps(payment_options) if payment_options is not None else None,
        "source_neighborhood_id": neighborhood_id,
        "source_city": city,
        "source_country": country,
        "last_details_fetch_utc": "NOW()",
        "last_nearby_fetch_utc": "NOW()" if from_nearby else None,
        "raw_details_json": json.dumps(details),
        "raw_nearby_json": json.dumps(raw_nearby_or_text) if raw_nearby_or_text is not None else None,
    }

    # psycopg2 doesn't accept NOW() as a value; we store timestamps via SQL NOW() on update_utc only.
    # Keep last_details_fetch_utc/last_nearby_fetch_utc as NOW() using SQL expression is trickier;
    # easiest: set them in a separate update after insert if needed. For MVP-2 we can omit precise stamps.
    row["last_details_fetch_utc"] = None
    row["last_nearby_fetch_utc"] = None

    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(UPSERT_SQL, row)
            cur.execute(SNAPSHOT_SQL, (place_id, "details", neighborhood_id, json.dumps(details)))
            if raw_nearby_or_text is not None:
                stype = "nearby" if from_nearby else "textsearch"
                cur.execute(SNAPSHOT_SQL, (place_id, stype, neighborhood_id, json.dumps(raw_nearby_or_text)))

# ----------------------------
# Seed ingestion
# ----------------------------

def resolve_address_to_latlng(address: str, language_code: str, region_code: str) -> Tuple[float, float]:
    # Use Text Search to resolve an address -> location.
    # Endpoint: POST https://places.googleapis.com/v1/places:searchText :contentReference[oaicite:4]{index=4}
    data = google_text_search(
        text_query=address,
        lat=None,
        lng=None,
        radius_m=None,
        max_results=5,
        language_code=language_code,
        region_code=region_code,
    )
    places = data.get("places") or []
    if not places:
        raise RuntimeError(f"No places returned when resolving address: {address}")
    lat, lng = _get_location(places[0])
    if lat is None or lng is None:
        raise RuntimeError(f"Resolved place had no location for address: {address}")
    return float(lat), float(lng)

def ingest_from_seed(seed: Dict[str, Any]) -> Dict[str, Any]:
    language_code = seed.get("languageCode") or DEFAULT_LANG
    region_code = seed.get("regionCode") or DEFAULT_REGION
    default_radius = int(seed.get("default_radius_m") or DEFAULT_RADIUS_M)
    default_top_n = int(seed.get("default_details_top_n") or DEFAULT_DETAILS_TOP_N)
    default_max_results = int(seed.get("default_max_results") or DEFAULT_MAX_RESULTS)

    stats = {"neighborhoods": 0, "categories": 0, "places_discovered": 0, "places_enriched": 0, "errors": 0}

    for city_obj in seed.get("cities", []):
        city = city_obj.get("city")
        country = city_obj.get("country", "JP")
        for nb in city_obj.get("neighborhoods", []):
            stats["neighborhoods"] += 1
            nb_id = nb.get("id")
            anchor = nb.get("anchor", {})
            address = anchor.get("address")
            if not address:
                stats["errors"] += 1
                continue

            radius_m = int(nb.get("radius_m") or default_radius)
            top_n = int(nb.get("details_top_n") or default_top_n)

            lat, lng = resolve_address_to_latlng(address, language_code, region_code)

            for cat in nb.get("categories", []):
                stats["categories"] += 1
                mode = (cat.get("mode") or "nearby").lower()
                max_results = int(cat.get("max_results") or default_max_results)

                discovered: List[Dict[str, Any]] = []

                try:
                    if mode == "nearby":
                        included_types = cat.get("included_types") or []
                        if not included_types:
                            # fallback: if none supplied, treat as textsearch using label
                            q = cat.get("text_query") or cat.get("label") or "places"
                            resp = google_text_search(q, lat, lng, radius_m, max_results, language_code, region_code)
                            discovered = resp.get("places") or []
                        else:
                            resp = google_nearby_search(lat, lng, radius_m, included_types, max_results, language_code, region_code)
                            discovered = resp.get("places") or []
                    else:
                        # textsearch
                        q = cat.get("text_query") or cat.get("label") or "places"
                        # bias search to neighborhood circle
                        resp = google_text_search(q, lat, lng, radius_m, max_results, language_code, region_code)
                        discovered = resp.get("places") or []
                except Exception:
                    stats["errors"] += 1
                    continue

                stats["places_discovered"] += len(discovered)

                ranked = rank_places(discovered)
                ranked = ranked[:top_n]

                for p in ranked:
                    pid = p.get("id")
                    if not pid:
                        continue
                    try:
                        details = google_place_details(pid, DETAILS_FIELDMASK)
                        upsert_place(
                            details=details,
                            raw_nearby_or_text={"place": p, "category": cat},
                            neighborhood_id=nb_id,
                            city=city,
                            country=country,
                            from_nearby=(mode == "nearby"),
                        )
                        stats["places_enriched"] += 1
                    except Exception:
                        stats["errors"] += 1
                        continue

    return stats

# ----------------------------
# Flask app
# ----------------------------

app = Flask(__name__)

@app.get("/health")
def health():
    ok_db = db_health()
    return jsonify(
        {
            "ok": True,
            "time": int(time.time()),
            "google_key_set": bool(GOOGLE_KEY),
            "db_ok": ok_db,
            "db": {"host": PGHOST, "port": PGPORT, "database": PGDATABASE, "user": PGUSER},
            "defaults": {
                "lang": DEFAULT_LANG,
                "region": DEFAULT_REGION,
                "nearby_fieldmask": NEARBY_FIELDMASK,
                "details_fieldmask": DETAILS_FIELDMASK,
            },
        }
    )

@app.get("/v1/details/<place_id>")
def details(place_id: str):
    fieldmask = request.args.get("fieldmask") or DETAILS_FIELDMASK
    try:
        data = google_place_details(place_id, fieldmask)
        return jsonify(data)
    except requests.HTTPError as e:
        return jsonify({"error": "google_http_error", "status": e.response.status_code, "body": e.response.text}), 502
    except Exception as e:
        return jsonify({"error": "internal_error", "message": str(e)}), 500

@app.get("/v1/nearby")
def nearby():
    # Minimal nearby wrapper.
    # Query params:
    # - lat, lng (required)
    # - radius_m (optional)
    # - included_types (comma list) OR text_query
    lat = float(request.args.get("lat", "nan"))
    lng = float(request.args.get("lng", "nan"))
    if math.isnan(lat) or math.isnan(lng):
        return jsonify({"error": "missing_lat_lng"}), 400

    radius_m = int(request.args.get("radius_m") or DEFAULT_RADIUS_M)
    max_results = int(request.args.get("max_results") or DEFAULT_MAX_RESULTS)
    language_code = request.args.get("language_code") or DEFAULT_LANG
    region_code = request.args.get("region_code") or DEFAULT_REGION

    text_query = request.args.get("text_query")
    included_types_str = request.args.get("included_types") or ""
    included_types = [t.strip() for t in included_types_str.split(",") if t.strip()]

    try:
        if text_query:
            data = google_text_search(text_query, lat, lng, radius_m, max_results, language_code, region_code)
        else:
            if not included_types:
                return jsonify({"error": "missing_included_types_or_text_query"}), 400
            data = google_nearby_search(lat, lng, radius_m, included_types, max_results, language_code, region_code)
        return jsonify(data)
    except requests.HTTPError as e:
        return jsonify({"error": "google_http_error", "status": e.response.status_code, "body": e.response.text}), 502
    except Exception as e:
        return jsonify({"error": "internal_error", "message": str(e)}), 500

@app.post("/v1/ingest/seeds")
def ingest_seeds():
    # Either provide JSON body, or use SEEDS_FILE on disk.
    try:
        if request.is_json:
            seed = request.get_json()
        else:
            seed = None

        if not seed:
            with open(SEEDS_FILE, "r", encoding="utf-8") as f:
                seed = json.load(f)

        stats = ingest_from_seed(seed)
        return jsonify({"ok": True, "stats": stats})
    except requests.HTTPError as e:
        return jsonify({"error": "google_http_error", "status": e.response.status_code, "body": e.response.text}), 502
    except Exception as e:
        return jsonify({"error": "internal_error", "message": str(e)}), 500

def main():
    # Use gunicorn for production-ish behavior.
    # If you prefer pure Flask dev server, change CMD in Dockerfile.
    from gunicorn.app.base import BaseApplication

    class StandaloneApplication(BaseApplication):
        def __init__(self, app, options=None):
            self.options = options or {}
            self.application = app
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
