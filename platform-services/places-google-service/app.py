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
# Places Google Service (Shogun)
#
# Fixes the "California results" bug by:
#   1) Resolving anchor address using Places Autocomplete (New) -> placeId
#   2) Fetching Place Details to get authoritative lat/lng + country
#   3) Enforcing minimum hygiene: discovered places must match seed country
#
# Runbook:
#   - This file: platform-services/places-google-service/app.py
#   - Seeds file path inside container: /app/seeds/neighborhoods.example.json
#   - SQL already deployed to dbnode-01 (schema places, tables google_places, google_place_snapshots)
# =============================================================================

# ----------------------------
# Config / Env
# ----------------------------

def _env(name: str, default: Optional[str] = None) -> str:
    v = os.getenv(name, default)
    if v is None:
        raise RuntimeError(f"Missing required env var: {name}")
    return v


PORT = int(os.getenv("PORT", "8081"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

GOOGLE_KEY = os.getenv("GOOGLE_PLACES_API_KEY", "").strip()
GOOGLE_BASE = os.getenv("GOOGLE_PLACES_BASE_URL", "https://places.googleapis.com/v1").strip()

# DB
PGHOST = os.getenv("PGHOST", "dbnode-01").strip()
PGPORT = int(os.getenv("PGPORT", "5432"))
PGDATABASE = os.getenv("PGDATABASE", "shogun_v1").strip()
PGUSER = os.getenv("PGUSER", "places_app").strip()
PGPASSWORD = os.getenv("PGPASSWORD", "").strip()
PGSSLMODE = os.getenv("PGSSLMODE", "prefer").strip()

# Seeds
SEEDS_FILE = os.getenv("SEEDS_FILE", "/app/seeds/neighborhoods.example.json").strip()

# Defaults
DEFAULT_LANG = os.getenv("DEFAULT_LANG", "en").strip()
DEFAULT_REGION = os.getenv("DEFAULT_REGION", "JP").strip()
DEFAULT_RADIUS_M = int(os.getenv("DEFAULT_RADIUS_M", "2000"))
DEFAULT_MAX_RESULTS = int(os.getenv("DEFAULT_MAX_RESULTS", "50"))
DEFAULT_DETAILS_TOP_N = int(os.getenv("DEFAULT_DETAILS_TOP_N", "75"))

NEARBY_FIELDMASK = os.getenv(
    "NEARBY_FIELDMASK",
    "places.id,places.displayName,places.location,places.types,places.rating,places.userRatingCount,places.priceLevel,places.primaryType,places.googleMapsUri,places.formattedAddress",
).strip()

DETAILS_FIELDMASK = os.getenv(
    "DETAILS_FIELDMASK",
    "id,displayName,formattedAddress,location,googleMapsUri,websiteUri,internationalPhoneNumber,"
    "rating,userRatingCount,priceLevel,primaryType,types,regularOpeningHours,paymentOptions,"
    "addressComponents",
).strip()

# Anchor resolve: keep it tight & authoritative
ANCHOR_DETAILS_FIELDMASK = os.getenv(
    "ANCHOR_DETAILS_FIELDMASK",
    "id,formattedAddress,location,addressComponents",
).strip()


# ----------------------------
# Flask app
# ----------------------------

app = Flask(__name__)


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
        sslmode=PGSSLMODE,
        connect_timeout=5,
    )


def db_health() -> Tuple[bool, Optional[str]]:
    try:
        with db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("select 1;")
                cur.fetchone()
        return True, None
    except Exception as e:
        return False, str(e)


UPSERT_SQL = """
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
) VALUES (
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

SNAPSHOT_SQL = """
INSERT INTO places.google_place_snapshots (
  place_id,
  snapshot_type,
  snapshot_utc,
  neighborhood_id,
  raw_json
) VALUES (
  %s, %s, NOW(), %s, %s::jsonb
);
"""


def _extract_display_name(d: Dict[str, Any]) -> Optional[str]:
    dn = d.get("displayName")
    if isinstance(dn, dict):
        return dn.get("text")
    if isinstance(dn, str):
        return dn
    return None


def db_insert_snapshot(place_id: str, snapshot_type: str, neighborhood_id: str, raw_json: Dict[str, Any]) -> None:
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(SNAPSHOT_SQL, (place_id, snapshot_type, neighborhood_id, json.dumps(raw_json)))


def upsert_place(
    details: Dict[str, Any],
    raw_discovery: Dict[str, Any],
    neighborhood_id: str,
    city: str,
    country: str,
    discovery_type: str,
) -> None:
    place_id = details.get("id")
    if not place_id:
        raise RuntimeError("details missing id")

    loc = details.get("location") or {}
    lat = loc.get("latitude")
    lng = loc.get("longitude")

    opening = details.get("regularOpeningHours") or {}
    payment = details.get("paymentOptions") or {}

    open_now = None
    if isinstance(opening, dict):
        open_now = opening.get("openNow")

    row = {
        "place_id": place_id,
        "display_name": _extract_display_name(details),
        "primary_type": details.get("primaryType"),
        "types": details.get("types"),
        "formatted_address": details.get("formattedAddress"),
        "lat": lat,
        "lng": lng,
        "google_maps_uri": details.get("googleMapsUri"),
        "website_uri": details.get("websiteUri"),
        "international_phone": details.get("internationalPhoneNumber"),
        "rating": details.get("rating"),
        "user_rating_count": details.get("userRatingCount"),
        "price_level": details.get("priceLevel"),
        "open_now": open_now,
        "opening_hours_json": json.dumps(opening) if opening else None,
        "payment_options_json": json.dumps(payment) if payment else None,
        "source_neighborhood_id": neighborhood_id,
        "source_city": city,
        "source_country": country,
        "raw_details_json": json.dumps(details),
        "raw_nearby_json": json.dumps(raw_discovery),
    }

    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(UPSERT_SQL, row)

    # store snapshots
    db_insert_snapshot(place_id, "details", neighborhood_id, details)
    db_insert_snapshot(place_id, discovery_type, neighborhood_id, raw_discovery)


# ----------------------------
# Google Places API helpers
# ----------------------------

def _google_headers(fieldmask: str) -> Dict[str, str]:
    if not GOOGLE_KEY:
        raise RuntimeError("GOOGLE_PLACES_API_KEY is not set")
    return {
        "X-Goog-Api-Key": GOOGLE_KEY,
        "X-Goog-FieldMask": fieldmask,
        "Content-Type": "application/json",
    }


def google_place_details(place_id: str, fieldmask: str) -> Dict[str, Any]:
    url = f"{GOOGLE_BASE}/places/{place_id}"
    resp = requests.get(url, headers=_google_headers(fieldmask), timeout=20)
    resp.raise_for_status()
    return resp.json()


def google_autocomplete_place_id(
    input_text: str,
    language_code: str,
    region_code: str,
    included_region_codes: Optional[List[str]],
) -> Optional[str]:
    """
    Places Autocomplete (New) -> placeId.
    This is the correct way to resolve a physical address-like anchor.
    """
    url = f"{GOOGLE_BASE}/places:autocomplete"
    payload: Dict[str, Any] = {
        "input": input_text,
        "languageCode": language_code,
        "regionCode": region_code,
    }
    if included_region_codes:
        payload["includedRegionCodes"] = included_region_codes

    headers = {
        "X-Goog-Api-Key": GOOGLE_KEY,
        "X-Goog-FieldMask": "suggestions.placePrediction.placeId",
        "Content-Type": "application/json",
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=20)
    resp.raise_for_status()
    data = resp.json()

    suggestions = data.get("suggestions") or []
    for s in suggestions:
        pp = (s or {}).get("placePrediction") or {}
        pid = pp.get("placeId")
        if pid:
            return pid
    return None


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
    payload = {
        "includedTypes": included_types,
        "maxResultCount": max_results,
        "languageCode": language_code,
        "regionCode": region_code,
        # HARD geo restriction
        "locationRestriction": {
            "circle": {
                "center": {"latitude": lat, "longitude": lng},
                "radius": float(radius_m),
            }
        },
    }
    resp = requests.post(url, headers=_google_headers(NEARBY_FIELDMASK), json=payload, timeout=25)
    resp.raise_for_status()
    return resp.json()


def google_text_search(
    text_query: str,
    lat: float,
    lng: float,
    radius_m: int,
    max_results: int,
    language_code: str,
    region_code: str,
) -> Dict[str, Any]:
    url = f"{GOOGLE_BASE}/places:searchText"
    payload = {
        "textQuery": text_query,
        "maxResultCount": max_results,
        "languageCode": language_code,
        "regionCode": region_code,
        # soft bias (but bounded around anchor)
        "locationBias": {
            "circle": {
                "center": {"latitude": lat, "longitude": lng},
                "radius": float(radius_m),
            }
        },
    }
    resp = requests.post(url, headers=_google_headers(NEARBY_FIELDMASK), json=payload, timeout=25)
    resp.raise_for_status()
    return resp.json()


# ----------------------------
# Hygiene / validation helpers
# ----------------------------

def _extract_country_code_from_address_components(details: Dict[str, Any]) -> Optional[str]:
    comps = details.get("addressComponents") or []
    for c in comps:
        types = c.get("types") or []
        if "country" in types:
            short = c.get("shortText")
            if isinstance(short, str) and short.strip():
                return short.strip().upper()
    return None


def _country_match(details: Dict[str, Any], expected_country: str) -> bool:
    """
    Minimum hygiene rule you chose:
      - Country must match seed (e.g., JP).
    Prefer addressComponents country shortText; fallback to formattedAddress contains.
    """
    exp = (expected_country or "").strip().upper()
    if not exp:
        return True

    cc = _extract_country_code_from_address_components(details)
    if cc:
        return cc == exp

    fa = (details.get("formattedAddress") or "").upper()
    # not perfect, but acceptable as fallback
    if exp == "JP":
        return ("JAPAN" in fa) or ("JP" in fa)
    if exp == "US":
        return ("USA" in fa) or ("UNITED STATES" in fa)
    # generic fallback
    return exp in fa


def rank_places(places: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    def score(p: Dict[str, Any]) -> float:
        r = float(p.get("rating") or 0.0)
        c = float(p.get("userRatingCount") or 0.0)
        return r * math.log(1.0 + c)
    return sorted(places, key=score, reverse=True)


# ----------------------------
# Seed ingestion
# ----------------------------

def load_seeds_file(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def resolve_anchor(
    address: str,
    city: Optional[str],
    country: Optional[str],
    language_code: str,
    region_code: str,
) -> Tuple[float, float, str, str]:
    """
    Returns (lat, lng, resolved_place_id, resolved_country_code)
    """
    q = address.strip()
    # helpful, not required
    if city and city.lower() not in q.lower():
        q = f"{q}, {city}"
    if country and country.lower() not in q.lower():
        q = f"{q}, {country}"

    effective_region = (region_code or "").strip() or (country or "").strip() or DEFAULT_REGION
    restrict_regions = [country.strip().upper()] if country else None

    place_id = google_autocomplete_place_id(
        input_text=q,
        language_code=language_code,
        region_code=effective_region,
        included_region_codes=restrict_regions,
    )
    if not place_id:
        raise RuntimeError(
            f"Anchor autocomplete failed (q={q!r}, regionCode={effective_region}, includedRegionCodes={restrict_regions})"
        )

    details = google_place_details(place_id, ANCHOR_DETAILS_FIELDMASK)
    loc = details.get("location") or {}
    lat = loc.get("latitude")
    lng = loc.get("longitude")
    if lat is None or lng is None:
        raise RuntimeError(f"Anchor details missing location for place_id={place_id}")

    resolved_cc = _extract_country_code_from_address_components(details) or ""
    if country and resolved_cc and resolved_cc.upper() != country.upper():
        raise RuntimeError(
            f"Anchor country mismatch: expected={country}, got={resolved_cc}, place_id={place_id}, formattedAddress={details.get('formattedAddress')}"
        )

    return float(lat), float(lng), place_id, (resolved_cc or (country or "")).upper()


def ingest_seed_payload(seed: Dict[str, Any]) -> Dict[str, Any]:
    language_code = seed.get("languageCode") or DEFAULT_LANG
    region_code = seed.get("regionCode") or DEFAULT_REGION
    default_radius = int(seed.get("default_radius_m") or DEFAULT_RADIUS_M)
    default_top_n = int(seed.get("default_details_top_n") or DEFAULT_DETAILS_TOP_N)
    default_max_results = int(seed.get("default_max_results") or DEFAULT_MAX_RESULTS)

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

    for city_obj in seed.get("cities", []):
        city = city_obj.get("city") or ""
        country = (city_obj.get("country") or DEFAULT_REGION).upper()

        for nb in city_obj.get("neighborhoods", []):
            stats["neighborhoods"] += 1
            nb_id = nb.get("id") or ""
            anchor = nb.get("anchor", {}) or {}
            address = anchor.get("address")

            if not nb_id or not address:
                stats["errors"] += 1
                continue

            radius_m = int(nb.get("radius_m") or default_radius)
            top_n = int(nb.get("details_top_n") or default_top_n)

            try:
                lat, lng, anchor_pid, anchor_cc = resolve_anchor(
                    address=address,
                    city=city,
                    country=country,
                    language_code=language_code,
                    region_code=region_code,
                )
                stats["anchor_resolved"] += 1

                # Snapshot the anchor as a special "anchor" snapshot for audit/debug
                db_insert_snapshot(anchor_pid, "anchor", nb_id, {
                    "anchor_address": address,
                    "resolved_place_id": anchor_pid,
                    "resolved_country": anchor_cc,
                    "lat": lat,
                    "lng": lng,
                    "city": city,
                    "country": country,
                    "languageCode": language_code,
                    "regionCode": region_code,
                })
            except Exception:
                stats["anchor_failures"] += 1
                stats["errors"] += 1
                continue

            for cat in nb.get("categories", []):
                stats["categories"] += 1

                mode = (cat.get("mode") or "nearby").lower()
                max_results = int(cat.get("max_results") or default_max_results)
                discovered: List[Dict[str, Any]] = []

                try:
                    if mode == "nearby":
                        included_types = cat.get("included_types") or []
                        if included_types:
                            resp = google_nearby_search(lat, lng, radius_m, included_types, max_results, language_code, country)
                            discovered = resp.get("places") or []
                            discovery_type = "nearby"
                        else:
                            q = cat.get("text_query") or cat.get("label") or "places"
                            resp = google_text_search(q, lat, lng, radius_m, max_results, language_code, country)
                            discovered = resp.get("places") or []
                            discovery_type = "textsearch"
                    else:
                        q = cat.get("text_query") or cat.get("label") or "places"
                        resp = google_text_search(q, lat, lng, radius_m, max_results, language_code, country)
                        discovered = resp.get("places") or []
                        discovery_type = "textsearch"
                except Exception:
                    stats["errors"] += 1
                    continue

                stats["places_discovered"] += len(discovered)

                ranked = rank_places(discovered)[:top_n]

                for p in ranked:
                    pid = p.get("id")
                    if not pid:
                        continue

                    try:
                        details = google_place_details(pid, DETAILS_FIELDMASK)

                        # Minimum hygiene rule: country match
                        if not _country_match(details, country):
                            stats["filtered_country_mismatch"] += 1
                            continue

                        raw_discovery = {"place": p, "category": cat, "anchor": {"lat": lat, "lng": lng, "place_id": anchor_pid}}
                        upsert_place(
                            details=details,
                            raw_discovery=raw_discovery,
                            neighborhood_id=nb_id,
                            city=city,
                            country=country,
                            discovery_type=discovery_type,
                        )
                        stats["places_enriched"] += 1
                    except Exception:
                        stats["errors"] += 1
                        continue

    return stats


# ----------------------------
# Routes
# ----------------------------

@app.get("/health")
def health():
    ok_db, db_err = db_health()
    return jsonify(
        {
            "ok": True,
            "time": int(time.time()),
            "google_key_set": bool(GOOGLE_KEY),
            "db_ok": ok_db,
            "db_error": db_err,
            "db": {"host": PGHOST, "port": PGPORT, "database": PGDATABASE, "user": PGUSER},
            "defaults": {
                "details_fieldmask": DETAILS_FIELDMASK,
                "nearby_fieldmask": NEARBY_FIELDMASK,
                "lang": DEFAULT_LANG,
                "region": DEFAULT_REGION,
            },
        }
    )


@app.get("/v1/debug/db")
def debug_db():
    ok_db, db_err = db_health()
    if not ok_db:
        return jsonify({"ok": False, "db_error": db_err}), 500
    with db_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("select now() as now_utc;")
            now_utc = cur.fetchone()["now_utc"]
            cur.execute("select count(*) as google_places_count from places.google_places;")
            c1 = cur.fetchone()["google_places_count"]
            cur.execute("select count(*) as snapshots_count from places.google_place_snapshots;")
            c2 = cur.fetchone()["snapshots_count"]
    return jsonify({"ok": True, "now_utc": str(now_utc), "counts": {"google_places": c1, "snapshots": c2}})


@app.get("/v1/debug/anchor")
def debug_anchor():
    """
    Prove anchor resolution is correct BEFORE ingesting.
    Example:
      /v1/debug/anchor?address=Room%20202%2C%20Zeus%20Tenjinbashi%20Queen...&city=Osaka&country=JP
    """
    address = request.args.get("address", "").strip()
    city = request.args.get("city", "").strip() or None
    country = request.args.get("country", "").strip().upper() or None
    language_code = request.args.get("lang", DEFAULT_LANG).strip()
    region_code = request.args.get("region", DEFAULT_REGION).strip()

    if not address:
        return jsonify({"ok": False, "error": "missing_address"}), 400

    try:
        lat, lng, pid, cc = resolve_anchor(address, city, country, language_code, region_code)
        details = google_place_details(pid, ANCHOR_DETAILS_FIELDMASK)
        return jsonify(
            {
                "ok": True,
                "input": {"address": address, "city": city, "country": country},
                "resolved": {
                    "place_id": pid,
                    "country": cc,
                    "lat": lat,
                    "lng": lng,
                    "formattedAddress": details.get("formattedAddress"),
                },
            }
        )
    except requests.HTTPError as e:
        return jsonify({"ok": False, "error": "google_http_error", "status": e.response.status_code, "body": e.response.text}), 502
    except Exception as e:
        return jsonify({"ok": False, "error": "anchor_resolution_failed", "message": str(e)}), 500


@app.post("/v1/ingest/seeds")
def ingest_seeds():
    """
    Loads seed JSON from SEEDS_FILE inside the container (default /app/seeds/neighborhoods.example.json)
    and performs discovery+enrichment into Postgres.
    """
    try:
        seed = load_seeds_file(SEEDS_FILE)
    except FileNotFoundError:
        return jsonify({"ok": False, "error": "seeds_file_not_found", "path": SEEDS_FILE}), 500
    except json.JSONDecodeError as e:
        return jsonify({"ok": False, "error": "seeds_file_invalid_json", "path": SEEDS_FILE, "message": str(e)}), 500

    try:
        stats = ingest_seed_payload(seed)
        return jsonify({"ok": True, "stats": stats})
    except requests.HTTPError as e:
        return jsonify({"ok": False, "error": "google_http_error", "status": e.response.status_code, "body": e.response.text}), 502
    except Exception as e:
        return jsonify({"ok": False, "error": "ingest_failed", "message": str(e)}), 500


@app.post("/v1/ingest/file")
def ingest_file():
    """
    Optional: ingest seeds from an uploaded JSON file.
    Use multipart/form-data with file field name: seed_file
    """
    if "seed_file" not in request.files:
        return jsonify({"ok": False, "error": "missing_seed_file"}), 400

    f = request.files["seed_file"]
    try:
        seed = json.loads(f.read().decode("utf-8"))
    except Exception as e:
        return jsonify({"ok": False, "error": "invalid_json", "message": str(e)}), 400

    try:
        stats = ingest_seed_payload(seed)
        return jsonify({"ok": True, "stats": stats})
    except requests.HTTPError as e:
        return jsonify({"ok": False, "error": "google_http_error", "status": e.response.status_code, "body": e.response.text}), 502
    except Exception as e:
        return jsonify({"ok": False, "error": "ingest_failed", "message": str(e)}), 500


# ----------------------------
# Main (Gunicorn-friendly)
# ----------------------------

def main():
    # When running in container, prefer gunicorn (like your current setup).
    try:
        import gunicorn.app.base  # type: ignore
    except Exception:
        # fallback: flask dev server (not recommended for prod)
        app.run(host="0.0.0.0", port=PORT)
        return

    class StandaloneApplication(gunicorn.app.base.BaseApplication):  # type: ignore
        def __init__(self, application, options=None):
            self.options = options or {}
            self.application = application
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
