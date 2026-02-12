from flask import request, jsonify

@app.post("/v1/places/search_text")
def v1_places_search_text():
    """
    Enterprise gateway endpoint.
    Caller MUST provide an anchor (lat/lng). No address geocoding here.
    """
    body = request.get_json(force=True, silent=False) or {}

    text_query = (body.get("text_query") or "").strip()
    lat = body.get("lat")
    lng = body.get("lng")
    radius_m = int(body.get("radius_m") or 2500)
    max_results = int(body.get("max_results") or 15)
    region_code = (body.get("region_code") or "JP").strip().upper()
    language_code = (body.get("language_code") or "en").strip()

    if not text_query:
        return jsonify({"ok": False, "error": "Missing: text_query"}), 400
    if lat is None or lng is None:
        return jsonify({"ok": False, "error": "Missing: lat/lng (anchor required)"}), 400

    try:
        data = google_places_text_search(
            text_query=text_query,
            lat=float(lat),
            lng=float(lng),
            radius_m=radius_m,
            max_results=max_results,
            region_code=region_code,
            language_code=language_code,
        )
        return jsonify({"ok": True, "data": data})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.post("/v1/places/nearby")
def v1_places_nearby():
    """
    Enterprise gateway endpoint.
    Nearby search requires anchor + included_types.
    """
    body = request.get_json(force=True, silent=False) or {}

    included_types = body.get("included_types") or []
    lat = body.get("lat")
    lng = body.get("lng")
    radius_m = int(body.get("radius_m") or 2500)
    max_results = int(body.get("max_results") or 15)
    region_code = (body.get("region_code") or "JP").strip().upper()
    language_code = (body.get("language_code") or "en").strip()

    if not isinstance(included_types, list) or not included_types:
        return jsonify({"ok": False, "error": "Missing: included_types (list)"}), 400
    if lat is None or lng is None:
        return jsonify({"ok": False, "error": "Missing: lat/lng (anchor required)"}), 400

    try:
        data = google_places_nearby_search(
            included_types=included_types,
            lat=float(lat),
            lng=float(lng),
            radius_m=radius_m,
            max_results=max_results,
            region_code=region_code,
            language_code=language_code,
        )
        return jsonify({"ok": True, "data": data})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500
