#!/usr/bin/env python3
"""
export_notebooklm.py — Export Shogun trip data to Markdown for Google NotebookLM.

Generates one .md file per trip city plus an overview.md.
Files are uploaded manually to NotebookLM as sources to create travel guides.

Usage:
    python tools/export_notebooklm.py [--output-dir outputs/notebooklm]

Output files:
    overview.md         — Traveler profiles + full trip timeline
    osaka.md            — Osaka itinerary + POIs + knowledge base
    kanazawa.md         — Kanazawa itinerary + POIs + knowledge base
    tokyo.md            — Tokyo itinerary + POIs + knowledge base
    nara.md             — Nara itinerary + POIs + knowledge base
"""

import argparse
import os
import sys
from collections import defaultdict
from datetime import date

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

# Load .env from app-services/shogun-core (or fall back to CWD)
_ENV_PATHS = [
    os.path.join(os.path.dirname(__file__), "..", "app-services", "shogun-core", ".env"),
    ".env",
]
for _p in _ENV_PATHS:
    if os.path.exists(_p):
        load_dotenv(_p)
        break

# ---------------------------------------------------------------------------
# DB connection
# ---------------------------------------------------------------------------

def _connect():
    host = os.environ.get("DB_HOST", "192.168.71.221")
    # platform-postgres is a Docker-internal name; resolve to bare metal IP for laptop use
    if host == "platform-postgres":
        host = "192.168.71.221"
    return psycopg2.connect(
        host=host,
        port=int(os.environ.get("DB_PORT", 5432)),
        dbname=os.environ.get("DB_NAME", "shogun_v1"),
        user=os.environ.get("DB_USER", "shogun_app"),
        password=os.environ.get("DB_PASSWORD", ""),
        cursor_factory=psycopg2.extras.RealDictCursor,
    )


# ---------------------------------------------------------------------------
# Query helpers
# ---------------------------------------------------------------------------

def _fetch(conn, sql, params=()):
    with conn.cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchall()


def load_users_and_prefs(conn):
    users = _fetch(conn, "SELECT id, display_name, full_name FROM users ORDER BY id")
    prefs = _fetch(
        conn,
        """
        SELECT u.display_name, up.category, up.preference_key,
               up.preference_value, up.notes
        FROM user_preferences up
        JOIN users u ON u.id = up.user_id
        ORDER BY u.display_name, up.category, up.preference_key
        """,
    )
    return users, prefs


def load_itinerary(conn):
    return _fetch(
        conn,
        """
        SELECT date_local, leg_sequence, leg_type, city, title,
               address_en, address_ja, start_time, end_time,
               confirmation_number, notes_en
        FROM trip_itinerary
        ORDER BY date_local, leg_sequence
        """,
    )


def load_pois(conn):
    return _fetch(
        conn,
        """
        SELECT city, name_en, name_ja, category, address_en,
               tags, crowd_notes, best_time_notes
        FROM trip_pois
        ORDER BY city, category, name_en
        """,
    )


def load_knowledge(conn):
    return _fetch(
        conn,
        """
        SELECT city, category, anchor, topic, content_summary, source_url
        FROM knowledge_items
        WHERE content_summary IS NOT NULL AND content_summary <> ''
        ORDER BY city, category, topic
        """,
    )


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def _fmt_date(d):
    if isinstance(d, date):
        return d.strftime("%A, %B %-d")  # e.g. "Monday, March 24"
    return str(d)


def _fmt_time(t):
    if t is None:
        return ""
    s = str(t)
    # HH:MM:SS → HH:MM
    return s[:5]


def _leg_emoji(leg_type):
    return {
        "flight": "✈️",
        "accommodation": "🏠",
        "activity": "📍",
        "transit": "🚇",
        "restaurant": "🍜",
        "shopping": "🛍️",
    }.get(leg_type, "•")


def _category_label(cat):
    return cat.replace("_", " ").title()


# ---------------------------------------------------------------------------
# Section builders
# ---------------------------------------------------------------------------

def build_traveler_section(users, prefs):
    lines = ["# Traveler Profiles\n"]

    # Group prefs by user
    by_user = defaultdict(lambda: defaultdict(list))
    for p in prefs:
        by_user[p["display_name"]][p["category"]].append(p)

    for u in users:
        name = u["display_name"]
        full = u["full_name"] or ""
        header = f"## {name}" + (f" ({full})" if full and full != name else "")
        lines.append(header)

        user_prefs = by_user.get(name, {})
        if not user_prefs:
            lines.append("_No preferences recorded._\n")
            continue

        for cat in ["dietary", "likes", "dislikes", "shopping", "entertainment"]:
            items = user_prefs.get(cat)
            if not items:
                continue
            lines.append(f"\n**{_category_label(cat)}:**")
            for p in items:
                val = p["preference_value"]
                note = f" — {p['notes']}" if p["notes"] else ""
                lines.append(f"- {p['preference_key']}: {val}{note}")

        lines.append("")

    return "\n".join(lines)


def build_itinerary_section(rows, city=None):
    """
    Build an itinerary section, optionally filtered to a city.
    If city is None, includes all rows (for overview).
    """
    if city:
        # Include rows where city matches (case-insensitive) OR date overlaps
        # For simplicity: include all rows for this city
        rows = [r for r in rows if r["city"].lower() == city.lower()]
        title = f"# {city.title()} Itinerary\n"
    else:
        title = "# Full Trip Itinerary\n"

    if not rows:
        return f"{title}_No itinerary data for {city}._\n"

    lines = [title]

    # Group by date
    by_date = defaultdict(list)
    for r in rows:
        by_date[r["date_local"]].append(r)

    for d in sorted(by_date.keys()):
        lines.append(f"## {_fmt_date(d)}")
        for r in by_date[d]:
            emoji = _leg_emoji(r["leg_type"])
            time_str = _fmt_time(r["start_time"])
            time_prefix = f"{time_str} " if time_str else ""
            lines.append(f"\n### {emoji} {time_prefix}{r['title']}")
            if r["address_en"]:
                lines.append(f"📍 {r['address_en']}")
            if r["confirmation_number"]:
                lines.append(f"🔑 Confirmation: {r['confirmation_number']}")
            if r["notes_en"]:
                lines.append(f"📝 {r['notes_en']}")
        lines.append("")

    return "\n".join(lines)


def build_pois_section(rows, city):
    rows = [r for r in rows if r["city"].lower() == city.lower()]
    lines = [f"# {city.title()} — Points of Interest\n"]

    if not rows:
        lines.append("_No POIs recorded._\n")
        return "\n".join(lines)

    by_cat = defaultdict(list)
    for r in rows:
        by_cat[r["category"]].append(r)

    for cat in sorted(by_cat.keys()):
        lines.append(f"## {_category_label(cat)}")
        for p in by_cat[cat]:
            name = p["name_en"]
            ja = f" / {p['name_ja']}" if p["name_ja"] else ""
            lines.append(f"\n### {name}{ja}")
            if p["address_en"]:
                lines.append(f"📍 {p['address_en']}")
            tags = p["tags"]
            if tags:
                lines.append(f"🏷️ {', '.join(tags)}")
            if p["crowd_notes"]:
                lines.append(f"👥 Crowd: {p['crowd_notes']}")
            if p["best_time_notes"]:
                lines.append(f"⏰ Best time: {p['best_time_notes']}")
        lines.append("")

    return "\n".join(lines)


# Category grouping for NotebookLM readability
_CATEGORY_GROUPS = {
    "Dining & Food": [
        "dining", "restaurant", "street_food", "coffee_cafe",
        "convenience_store", "local_market", "market",
    ],
    "Craft Beer & Sake": [
        "craft_beer", "sake_brewery",
    ],
    "Shopping": [
        "shopping", "shopping_crafts", "vintage", "ceramics",
        "anime_manga", "eyewear", "eyewear_prescription", "jewelry_artisan",
        "skincare", "tech_electronics",
    ],
    "Temples & Shrines": [
        "temple", "shrine",
    ],
    "Sights & Culture": [
        "sightseeing", "museum", "neighborhood", "park",
        "nara_daytrip", "usj",
    ],
    "Practical": [
        "practical", "pharmacy", "transit",
    ],
    "Events & Seasonal": [
        "events", "sakura",
    ],
    "General": [
        "general",
    ],
}

def _group_for_category(cat):
    for group, cats in _CATEGORY_GROUPS.items():
        if cat in cats:
            return group
    return "Other"


def build_knowledge_section(rows, city):
    rows = [r for r in rows if r["city"] and r["city"].lower() == city.lower()]
    lines = [f"# {city.title()} — Local Knowledge Base\n"]

    if not rows:
        lines.append("_No knowledge items recorded._\n")
        return "\n".join(lines)

    by_group = defaultdict(list)
    for r in rows:
        group = _group_for_category(r["category"] or "general")
        by_group[group].append(r)

    group_order = list(_CATEGORY_GROUPS.keys()) + ["Other"]

    for group in group_order:
        items = by_group.get(group)
        if not items:
            continue
        lines.append(f"## {group}")

        # Sub-group by category within the group
        by_cat = defaultdict(list)
        for item in items:
            by_cat[item["category"] or "general"].append(item)

        for cat in sorted(by_cat.keys()):
            cat_items = by_cat[cat]
            if len(by_cat) > 1:
                lines.append(f"\n### {_category_label(cat)}")

            for ki in cat_items:
                anchor_str = f" [{ki['anchor']}]" if ki["anchor"] else ""
                lines.append(f"\n**{ki['topic']}{anchor_str}**")
                lines.append(ki["content_summary"])
                if ki["source_url"]:
                    lines.append(f"Source: {ki['source_url']}")

        lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Per-city document
# ---------------------------------------------------------------------------

_TRIP_CITIES = ["osaka", "kanazawa", "kyoto", "tokyo", "nara"]


def build_city_document(city, users, prefs, itinerary, pois, knowledge):
    parts = []

    # Header
    parts.append(f"# Shogun Travel Guide — {city.title()}\n")
    parts.append(
        "_This document was exported from the Shogun Japan trip database "
        "for use in Google NotebookLM. It contains trip itinerary, points of interest, "
        f"and curated local knowledge for {city.title()}._\n"
    )

    parts.append("---\n")
    parts.append(build_traveler_section(users, prefs))
    parts.append("---\n")
    parts.append(build_itinerary_section(itinerary, city=city))
    parts.append("---\n")
    parts.append(build_pois_section(pois, city))
    parts.append("---\n")
    parts.append(build_knowledge_section(knowledge, city))

    return "\n".join(parts)


def build_overview_document(users, prefs, itinerary):
    parts = []
    parts.append("# Shogun Japan Trip — Overview\n")
    parts.append(
        "_Master itinerary and traveler profiles. "
        "See individual city files for local knowledge and POIs._\n"
    )
    parts.append("---\n")
    parts.append(build_traveler_section(users, prefs))
    parts.append("---\n")
    parts.append(build_itinerary_section(itinerary, city=None))

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Export Shogun trip data to NotebookLM Markdown")
    parser.add_argument(
        "--output-dir",
        default=os.path.join(os.path.dirname(__file__), "..", "outputs", "notebooklm"),
        help="Directory to write .md files (default: outputs/notebooklm)",
    )
    args = parser.parse_args()

    out_dir = os.path.abspath(args.output_dir)
    os.makedirs(out_dir, exist_ok=True)

    print(f"Connecting to shogun_v1 ...")
    try:
        conn = _connect()
    except Exception as e:
        print(f"ERROR: Could not connect to database: {e}", file=sys.stderr)
        sys.exit(1)

    print("Loading data ...")
    users, prefs = load_users_and_prefs(conn)
    itinerary = load_itinerary(conn)
    pois = load_pois(conn)
    knowledge = load_knowledge(conn)
    conn.close()

    # Count summary
    ki_by_city = defaultdict(int)
    for k in knowledge:
        if k["city"]:
            ki_by_city[k["city"].lower()] += 1

    print(f"  Users:          {len(users)}")
    print(f"  Preferences:    {len(prefs)}")
    print(f"  Itinerary legs: {len(itinerary)}")
    print(f"  POIs:           {len(pois)}")
    print(f"  Knowledge items: {sum(ki_by_city.values())} "
          f"({', '.join(f'{c}:{n}' for c, n in sorted(ki_by_city.items()))})")

    # Overview
    path = os.path.join(out_dir, "overview.md")
    content = build_overview_document(users, prefs, itinerary)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  → {path}")

    # Per-city files
    for city in _TRIP_CITIES:
        path = os.path.join(out_dir, f"{city}.md")
        content = build_city_document(city, users, prefs, itinerary, pois, knowledge)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        ki_count = ki_by_city.get(city, 0)
        print(f"  → {path}  ({ki_count} knowledge items)")

    print(f"\nDone. {len(_TRIP_CITIES) + 1} files written to {out_dir}")
    print("\nNext steps:")
    print("  1. Open https://notebooklm.google.com")
    print("  2. Create a new notebook (e.g. 'Japan Trip 2026')")
    print("  3. Add sources → Upload files → select all .md files from outputs/notebooklm/")
    print("  4. Ask NotebookLM to create a travel guide for each city")


if __name__ == "__main__":
    main()
