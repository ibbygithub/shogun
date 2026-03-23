import json
from fastapi import APIRouter, Request, Depends, Query, HTTPException
from auth import get_current_user, User
from db import get_conn
from models import Poi

router = APIRouter(prefix="/pois", tags=["pois"])

# Actual DB columns: id, city, name_en, name_ja, category, lat, lng,
#   address_en, address_ja, tags, crowd_notes, best_time_notes, source, created_utc
# No description column — use None. map_url constructed from lat/lng.


def _row_to_poi(row) -> Poi:
    # row: id, city, name_en, name_ja, category, lat, lng, tags, crowd_notes, best_time_notes, source
    tags = row[7]
    if isinstance(tags, str):
        try:
            tags = json.loads(tags)
        except Exception:
            tags = [t.strip() for t in tags.split(",") if t.strip()]
    elif tags is None:
        tags = []

    lat, lng = row[5], row[6]
    map_url = f"https://maps.google.com/?q={lat},{lng}" if lat and lng else None

    return Poi(
        id=row[0],
        city=row[1],
        name_en=row[2],
        name_ja=row[3],
        category=row[4],
        tags=tags,
        description=None,           # not in schema
        crowd_notes=row[8],
        best_time=row[9],           # best_time_notes
        map_url=map_url,
        source=row[10],
        lat=lat,
        lng=lng,
    )


@router.get("", response_model=list[Poi])
def get_pois(
    request: Request,
    city: str | None = Query(None),
    tags: list[str] = Query(default=[]),
    user: User = Depends(get_current_user),
):
    with get_conn() as conn:
        with conn.cursor() as cur:
            if city:
                cur.execute(
                    """
                    SELECT id, city, name_en, name_ja, category, lat, lng,
                           tags, crowd_notes, best_time_notes, source
                    FROM trip_pois WHERE city=%s ORDER BY name_en
                    """,
                    (city,),
                )
            else:
                cur.execute(
                    """
                    SELECT id, city, name_en, name_ja, category, lat, lng,
                           tags, crowd_notes, best_time_notes, source
                    FROM trip_pois ORDER BY city, name_en
                    """
                )
            pois = [_row_to_poi(r) for r in cur.fetchall()]

    if tags:
        pois = [
            p for p in pois
            if p.tags and any(t in p.tags for t in tags)
        ]
    return pois


@router.get("/{poi_id}/knowledge")
def get_poi_knowledge(
    poi_id: int,
    request: Request,
    user: User = Depends(get_current_user),
):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, city, name_en, name_ja, category, lat, lng,
                       tags, crowd_notes, best_time_notes, source
                FROM trip_pois WHERE id=%s
                """,
                (poi_id,),
            )
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="POI not found")
            poi = _row_to_poi(row)

    youtube_query = f"{poi.name_en} Japan guide 2026"
    suggested_searches = [
        f"{poi.name_en} best time to visit",
        f"{poi.name_en} travel tips",
        f"{poi.name_ja} 観光" if poi.name_ja else f"{poi.name_en} 観光",
    ]

    return {
        "poi": poi,
        "summary": poi.crowd_notes,
        "youtube_query": youtube_query,
        "suggested_searches": suggested_searches,
        "booking_url": poi.map_url,
    }


@router.get("/{poi_id}/guide")
def get_poi_guide(
    poi_id: int,
    request: Request,
    user: User = Depends(get_current_user),
):
    with get_conn() as conn:
        with conn.cursor() as cur:
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
            "photos": guide_row[10],
            "official_url": guide_row[11],
            "sources": guide_row[12],
            "hours_verified": guide_row[13],
            "completeness": guide_row[14],
            "generated_utc": str(guide_row[15]) if guide_row[15] else None,
        },
    }
