import json
from fastapi import APIRouter, Request, Depends, Query, HTTPException
import httpx
from auth import get_current_user, User
from db import get_conn
from models import Poi

router = APIRouter(prefix="/pois", tags=["pois"])


def _row_to_poi(row) -> Poi:
    tags = row[4]
    if isinstance(tags, str):
        try:
            tags = json.loads(tags)
        except Exception:
            tags = [t.strip() for t in tags.split(",") if t.strip()]
    return Poi(
        id=row[0],
        city=row[1],
        name_en=row[2],
        name_ja=row[3],
        category=None,
        tags=tags,
        description=row[5],
        crowd_notes=row[6],
        best_time=row[7],
        map_url=row[8],
        source=row[9],
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
                    SELECT id, city, name_en, name_ja, tags, description,
                           crowd_notes, best_time, map_url, source
                    FROM trip_pois WHERE city=%s ORDER BY name_en
                    """,
                    (city,),
                )
            else:
                cur.execute(
                    """
                    SELECT id, city, name_en, name_ja, tags, description,
                           crowd_notes, best_time, map_url, source
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
                SELECT id, city, name_en, name_ja, tags, description,
                       crowd_notes, best_time, map_url, source
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
        "summary": poi.description,
        "youtube_query": youtube_query,
        "suggested_searches": suggested_searches,
        "booking_url": poi.map_url,
    }
