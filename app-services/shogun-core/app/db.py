"""
PostgreSQL connection pool for shogun_v1.
Uses psycopg2 with a simple connection-per-request pattern (single user MVP).
"""
import logging
import psycopg2
import psycopg2.extras
from app.config import settings

logger = logging.getLogger(__name__)


def get_connection():
    """Return a new psycopg2 connection. Caller is responsible for closing."""
    return psycopg2.connect(
        host=settings.db_host,
        port=settings.db_port,
        dbname=settings.db_name,
        user=settings.db_user,
        password=settings.db_password,
        cursor_factory=psycopg2.extras.RealDictCursor,
        connect_timeout=5,
    )


def get_user_by_telegram_id(telegram_user_id: int) -> dict | None:
    """Return the users row for a given Telegram user ID, or None."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM users WHERE telegram_user_id = %s",
                (telegram_user_id,),
            )
            return cur.fetchone()
    finally:
        conn.close()


def get_user_preferences(user_id: int) -> list[dict]:
    """Return all user_preferences rows for a given users.id."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT category, preference_key, preference_value, notes "
                "FROM user_preferences WHERE user_id = %s ORDER BY category, preference_key",
                (user_id,),
            )
            return cur.fetchall()
    finally:
        conn.close()


def get_todays_itinerary(date_local: str) -> list[dict]:
    """Return trip_itinerary rows for a given local date (YYYY-MM-DD)."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT leg_type, city, title, address_en, address_ja, "
                "start_time, end_time, notes_en "
                "FROM trip_itinerary WHERE date_local = %s ORDER BY leg_sequence",
                (date_local,),
            )
            return cur.fetchall()
    finally:
        conn.close()


def get_city_for_date(date_local: str) -> str | None:
    """
    Return the base city for a given date by finding the most recent
    accommodation leg on or before that date.
    Returns None if no accommodation is found (pre-trip or post-trip).
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT city FROM trip_itinerary "
                "WHERE leg_type = 'accommodation' AND date_local <= %s "
                "ORDER BY date_local DESC LIMIT 1",
                (date_local,),
            )
            row = cur.fetchone()
            return row["city"] if row else None
    finally:
        conn.close()


def get_pois_by_city(city: str, category: str | None = None) -> list[dict]:
    """Return trip_pois for a city, optionally filtered by category."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            if category:
                cur.execute(
                    "SELECT name_en, name_ja, category, address_en, lat, lng, "
                    "tags, crowd_notes, best_time_notes "
                    "FROM trip_pois WHERE city = %s AND category = %s",
                    (city, category),
                )
            else:
                cur.execute(
                    "SELECT name_en, name_ja, category, address_en, lat, lng, "
                    "tags, crowd_notes, best_time_notes "
                    "FROM trip_pois WHERE city = %s",
                    (city,),
                )
            return cur.fetchall()
    finally:
        conn.close()


def get_checklist() -> list[dict]:
    """Return all checklist_items ordered by category and item name."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, category, item_name, packed, notes "
                "FROM checklist_items ORDER BY category, item_name"
            )
            return cur.fetchall()
    finally:
        conn.close()


def get_unpacked_items() -> list[dict]:
    """Return checklist items that have not yet been packed."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT category, item_name, notes "
                "FROM checklist_items WHERE packed = FALSE "
                "ORDER BY category, item_name"
            )
            return cur.fetchall()
    finally:
        conn.close()


def get_knowledge_tip_for_city(city: str) -> list[dict]:
    """Return up to 2 random knowledge_items for a city, used in the morning brief."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT topic, content_summary, category "
                "FROM knowledge_items WHERE LOWER(city) = LOWER(%s) "
                "ORDER BY RANDOM() LIMIT 2",
                (city,)
            )
            return cur.fetchall()
    finally:
        conn.close()


# Common navigational/stopwords that don't appear in knowledge content.
# Shared between search_trip_knowledge and any future caller.
_KNOWLEDGE_STOPWORDS = {
    "near", "the", "and", "for", "are", "our", "what", "see", "find",
    "best", "good", "some", "any", "not", "can", "get", "how", "do",
    "to", "in", "at", "of", "a", "an", "is", "it", "be", "or", "we",
    "i", "me", "my", "us", "you", "he", "she", "they", "that", "this",
    "with", "from", "have", "will", "was", "has", "had", "but", "if",
    "looking", "want", "need", "going", "try",
}


def search_trip_knowledge(
    query: str,
    city: str | None = None,
    anchor: str | None = None,
    category: str | None = None,
) -> list[dict]:
    """Search knowledge_items using OR-match + count-based relevance ranking.

    Tokens shorter than 3 chars and common stopwords are filtered so words
    like "near", "the", "see" don't dilute matching. Remaining tokens use OR
    logic — a row matches if ANY meaningful token appears in topic or
    content_summary. Results are ordered: full phrase in topic first, then
    by token match count, then alphabetically.

    Returns list of RealDictRow with keys: city, category, topic, content_summary.
    Returns empty list when no matches are found.
    """
    raw_tokens = query.lower().split()
    tokens = [t for t in raw_tokens if len(t) >= 3 and t not in _KNOWLEDGE_STOPWORDS]
    # If all tokens were filtered (very short query), use the raw query as one token
    if not tokens:
        tokens = [query.lower()]

    # Structural filters: city (case-insensitive), anchor, category
    struct_clauses: list[str] = []
    struct_params: list = []
    if city:
        struct_clauses.append("(LOWER(city) = LOWER(%s) OR city IS NULL)")
        struct_params.append(city)
    if anchor:
        struct_clauses.append("anchor = %s")
        struct_params.append(anchor)
    if category:
        struct_clauses.append("LOWER(category) = LOWER(%s)")
        struct_params.append(category)

    # Text match: OR across all meaningful tokens
    token_match_parts = []
    token_params: list = []
    for token in tokens:
        like = f"%{token}%"
        token_match_parts.append("(topic ILIKE %s OR content_summary ILIKE %s)")
        token_params.extend([like, like])
    token_clause = "(" + " OR ".join(token_match_parts) + ")"

    all_clauses = struct_clauses + [token_clause]
    where_sql = "WHERE " + " AND ".join(all_clauses)
    all_params = struct_params + token_params

    # Relevance score: sum of per-token CASE expressions
    score_parts = []
    score_params: list = []
    for token in tokens:
        like = f"%{token}%"
        score_parts.append(
            "(CASE WHEN topic ILIKE %s OR content_summary ILIKE %s THEN 1 ELSE 0 END)"
        )
        score_params.extend([like, like])
    match_score = " + ".join(score_parts) if score_parts else "1"

    full_like = f"%{query}%"

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT city, category, topic, content_summary
                FROM knowledge_items
                {where_sql}
                ORDER BY
                    CASE WHEN topic ILIKE %s THEN 0 ELSE 1 END,
                    ({match_score}) DESC,
                    city NULLS LAST,
                    topic
                LIMIT 15
                """,
                all_params + score_params + [full_like],
            )
            return cur.fetchall()
    except Exception:
        logger.exception("search_trip_knowledge query failed")
        return []
    finally:
        conn.close()
