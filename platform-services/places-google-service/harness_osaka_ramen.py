import os
import sys
import requests

GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "").strip()
GATEWAY_BASE_URL = os.environ.get("PLACES_GATEWAY_URL", "http://localhost:5000").rstrip("/")

if not GOOGLE_API_KEY:
    print("ERROR: set GOOGLE_API_KEY env var")
    sys.exit(1)

ADDRESS = os.environ.get("OSAKA_ADDRESS", "").strip()
if not ADDRESS:
    print("ERROR: set OSAKA_ADDRESS env var (your hotel/address in Osaka)")
    sys.exit(1)

def geocode_address(address: str, country_code: str = "JP"):
    # Geocoding happens in the APP/HARNESS (not the gateway).
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        "address": address,
        "key": GOOGLE_API_KEY,
        "region": country_code,
        "components": f"country:{country_code}",
    }
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    data = r.json()
    if data.get("status") != "OK" or not data.get("results"):
        raise RuntimeError(f"Geocode failed: {data.get('status')} {data.get('error_message')}")
    best = data["results"][0]
    loc = best["geometry"]["location"]
    # confirm country
    cc = None
    for c in best.get("address_components", []):
        if "country" in c.get("types", []):
            cc = c.get("short_name")
            break
    return {
        "lat": loc["lat"],
        "lng": loc["lng"],
        "formatted_address": best.get("formatted_address"),
        "country": cc,
    }

def gateway_search_text(text_query: str, lat: float, lng: float, radius_m: int = 2500, region_code: str = "JP", language_code: str = "en"):
    url = f"{GATEWAY_BASE_URL}/v1/places/search_text"
    body = {
        "text_query": text_query,
        "lat": lat,
        "lng": lng,
        "radius_m": radius_m,
        "max_results": 15,
        "region_code": region_code,
        "language_code": language_code,
    }
    r = requests.post(url, json=body, timeout=30)
    r.raise_for_status()
    return r.json()

def main():
    print(f"Geocoding Osaka address (APP-side): {ADDRESS}")
    anchor = geocode_address(ADDRESS, country_code="JP")
    print("ANCHOR:")
    print(anchor)

    if (anchor.get("country") or "").upper() != "JP":
        raise RuntimeError(f"Anchor did not resolve to JP. Got {anchor.get('country')}")

    print("\nCalling gateway (pure Places proxy) for ramen near anchor...")
    resp = gateway_search_text(
        text_query="ramen restaurant",
        lat=anchor["lat"],
        lng=anchor["lng"],
        radius_m=2500,
        region_code="JP",
        language_code="en",
    )

    if not resp.get("ok"):
        raise RuntimeError(resp)

    places = (resp["data"].get("places") or [])
    print(f"\nRESULTS: {len(places)}")
    for i, p in enumerate(places[:10], 1):
        name = (p.get("displayName") or {}).get("text")
        addr = p.get("formattedAddress")
        rating = p.get("rating")
        cnt = p.get("userRatingCount")
        loc = p.get("location") or {}
        print(f"{i:02d}. {name} | {addr} | rating={rating} ({cnt}) | {loc.get('latitude')},{loc.get('longitude')}")

    print("\nIf these are in Osaka, you have proven:")
    print("- geocoding/anchoring is correct (APP-side)")
    print("- gateway is not drifting to California (because it only follows lat/lng)")
    print("- Places API wiring is working end-to-end")

if __name__ == "__main__":
    main()
