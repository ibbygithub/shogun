#!/usr/bin/env python3
"""
Knowledge pipeline bulk ingestion — Tavily-sourced knowledge_items.

Runs inside the shogun-web-api container (has DATABASE_URL + TAVILY_GATEWAY_URL).

Usage (from brainnode-01 after docker cp):
    docker exec shogun-web-api python3 /tmp/ingest_knowledge_pipeline.py osaka
    docker exec shogun-web-api python3 /tmp/ingest_knowledge_pipeline.py kanazawa
    docker exec shogun-web-api python3 /tmp/ingest_knowledge_pipeline.py kyoto
    docker exec shogun-web-api python3 /tmp/ingest_knowledge_pipeline.py nara

Each entry in QUERY_MATRIX:
    (city, anchor_or_None, category, district_hint, query, include_domains)

Topic stored as: "{tavily_result_title} [{district_hint}]"
Content stored as: tavily snippet (≤400 chars)
"""

import sys
import os
import time
import httpx
import psycopg2

TAVILY_GW  = os.getenv("TAVILY_GATEWAY_URL", "http://192.168.71.220:8084")
DB_URL     = os.environ["DATABASE_URL"]

# ---------------------------------------------------------------------------
# Query matrix — (city, anchor, category, district_hint, query, domains)
# city: lowercase. anchor: None for Tier-2 destination zones.
# ---------------------------------------------------------------------------

QUERY_MATRIX = {

    # ═══════════════════════════════════════════════════════════════════════
    # OSAKA
    # ═══════════════════════════════════════════════════════════════════════
    "osaka": [

        # ── Zone 1: Accommodation (anchor: osaka-airbnb, Nakazakicho / Umeda) ──
        ("osaka", "osaka-airbnb", "dining",   "Nakazakicho Osaka",
         "best ramen standing bar Nakazakicho Osaka noodles",
         ["tabelog.com"]),
        ("osaka", "osaka-airbnb", "dining",   "Tenjinbashisuji Osaka",
         "izakaya Tenjinbashisuji local dinner Osaka cheap",
         ["tabelog.com"]),
        ("osaka", "osaka-airbnb", "dining",   "Umeda Osaka",
         "best ramen Umeda Osaka tonkotsu tsukemen local favourite",
         ["tabelog.com"]),
        ("osaka", "osaka-airbnb", "coffee_cafe", "Nakazakicho Osaka",
         "independent coffee shop Nakazakicho Osaka specialty third wave",
         []),
        ("osaka", "osaka-airbnb", "craft_beer", "Umeda Osaka",
         "craft beer bar Umeda Osaka local tap brewery",
         []),
        ("osaka", "osaka-airbnb", "shopping", "Nakazakicho Osaka",
         "vintage clothing thrift shop Nakazakicho Osaka second-hand",
         []),
        ("osaka", "osaka-airbnb", "ceramics", "Umeda Osaka",
         "Japanese pottery ceramics shop Osaka Umeda buy",
         []),
        ("osaka", "osaka-airbnb", "jewelry_artisan", "Kita Ward Osaka",
         "handmade jewelry artisan shop market Osaka Kita Ward",
         []),
        ("osaka", "osaka-airbnb", "convenience_store", "Nakazakicho Osaka",
         "convenience store FamilyMart Lawson Nakazakicho Osaka what to buy",
         []),
        ("osaka", "osaka-airbnb", "dining", "Umeda Osaka",
         "food hall depachika Umeda Osaka basement restaurants",
         []),

        # ── Zone 2: Dotonbori / Namba / Shinsaibashi (3/27) ──
        ("osaka", None, "dining",   "Dotonbori Osaka",
         "street food Dotonbori Osaka must eat 2025",
         []),
        ("osaka", None, "dining",   "Dotonbori Osaka",
         "takoyaki best stall Dotonbori Osaka authentic",
         []),
        ("osaka", None, "dining",   "Namba Osaka",
         "ramen restaurant Namba Osaka local favourite hidden",
         ["tabelog.com"]),
        ("osaka", None, "dining",   "Dotonbori Osaka",
         "conveyor sushi kaiten Namba Dotonbori Osaka",
         []),
        ("osaka", None, "dining",   "Shinsaibashi Osaka",
         "food hall depachika Shinsaibashi Osaka basement",
         []),
        ("osaka", None, "coffee_cafe", "Namba Osaka",
         "specialty coffee cafe Namba Dotonbori Osaka independent",
         []),
        ("osaka", None, "shopping", "Shinsaibashi Osaka",
         "Shinsaibashi shopping street what to buy Osaka guide",
         []),
        ("osaka", None, "ceramics", "Shinsaibashi Osaka",
         "ceramics pottery Japanese souvenir shop Shinsaibashi Osaka",
         []),

        # ── Zone 3: Nipponbashi / Denden Town (3/28 tech + anime) ──
        ("osaka", None, "tech_electronics", "Nipponbashi Osaka",
         "ESP32 microcontroller electronics components shop Nipponbashi Osaka",
         []),
        ("osaka", None, "tech_electronics", "Nipponbashi Osaka",
         "robot kit hobby electronics Denden Town Osaka components store",
         []),
        ("osaka", None, "tech_electronics", "Nipponbashi Osaka",
         "Nipponbashi Denden Town electronics guide Osaka Akihabara",
         []),
        ("osaka", None, "anime_manga", "Nipponbashi Osaka",
         "anime figure shop best Nipponbashi Osaka 2025",
         []),
        ("osaka", None, "anime_manga", "Nipponbashi Osaka",
         "retro game shop vintage Nipponbashi Osaka Denden Town",
         []),
        ("osaka", None, "anime_manga", "Nipponbashi Osaka",
         "manga stickers plush figures Denden Town Osaka buy",
         []),
        ("osaka", None, "shopping", "Nipponbashi Osaka",
         "vintage antique shop Nipponbashi Osaka",
         []),
        ("osaka", None, "dining", "Nipponbashi Osaka",
         "ramen lunch Nipponbashi Osaka cheap eat near Denden Town",
         ["tabelog.com"]),

        # ── Zone 4: Shinsekai / Tsutenkaku (3/28) ──
        ("osaka", None, "dining", "Shinsekai Osaka",
         "kushikatsu Shinsekai Osaka best authentic rules no double dipping",
         []),
        ("osaka", None, "dining", "Shinsekai Osaka",
         "street food Shinsekai Osaka retro neighbourhood what to eat",
         []),
        ("osaka", None, "sightseeing", "Shinsekai Osaka",
         "Shinsekai Osaka atmosphere guide retro what to see Tsutenkaku",
         []),

        # ── Zone 5: Sakuranomiya / Osaka Castle (3/27 afternoon) ──
        ("osaka", None, "dining", "Osaka Castle area",
         "lunch restaurant near Osaka Castle park walk 2025",
         ["tabelog.com"]),
        ("osaka", None, "park", "Sakuranomiya Osaka",
         "Sakuranomiya park cherry blossom food stalls sakura late March",
         []),
        ("osaka", None, "sightseeing", "Osaka Castle",
         "Osaka Castle Nishinomaru Garden sakura tips what to know",
         []),

        # ── Zone 6: Interest threads (city-wide, anchor=None) ──
        ("osaka", None, "craft_beer", "Osaka",
         "best craft beer bars Osaka local brewery guide 2025",
         []),
        ("osaka", None, "shopping", "Osaka",
         "best vintage clothing thrift shop Osaka second-hand used",
         []),
        ("osaka", None, "sake_brewery", "Osaka",
         "sake tasting Osaka brewery visit experience",
         []),
        ("osaka", None, "dining", "Osaka",
         "authentic Japanese burger best Osaka 2025",
         []),
        ("osaka", None, "skincare", "Osaka",
         "Japanese skincare store Osaka best brands Cosme @cosme",
         []),
        ("osaka", None, "jewelry_artisan", "Osaka",
         "handmade jewelry artisan bazaar market Osaka craft",
         []),
        ("osaka", None, "dining", "Osaka",
         "standing ramen bar best Osaka experience 2025",
         []),
        ("osaka", None, "eyewear_prescription", "Osaka",
         "same day prescription glasses vision test Osaka optical shop",
         []),
    ],

    # ═══════════════════════════════════════════════════════════════════════
    # KANAZAWA — highlights only (30–40 items target)
    # ═══════════════════════════════════════════════════════════════════════
    "kanazawa": [

        # ── Zone 1: Higashi Chaya geisha district (priority) ──
        ("kanazawa", "kanazawa-hotel", "sightseeing", "Higashi Chaya Kanazawa",
         "Higashi Chaya geisha district Kanazawa guide what to do see",
         []),
        ("kanazawa", "kanazawa-hotel", "shopping_crafts", "Higashi Chaya Kanazawa",
         "gold leaf shop buy Higashi Chaya Kanazawa souvenir",
         []),
        ("kanazawa", "kanazawa-hotel", "sake_brewery", "Higashi Chaya Kanazawa",
         "sake tasting Kanazawa Higashi Chaya brewery local",
         []),
        ("kanazawa", "kanazawa-hotel", "coffee_cafe", "Higashi Chaya Kanazawa",
         "cafe tea house Higashi Chaya Kanazawa matcha",
         []),
        ("kanazawa", "kanazawa-hotel", "ceramics", "Kanazawa",
         "Kutani ware ceramics pottery shop Kanazawa buy authentic",
         []),
        ("kanazawa", "kanazawa-hotel", "dining", "Higashi Chaya Kanazawa",
         "lunch restaurant near Higashi Chaya Kanazawa local",
         ["tabelog.com"]),

        # ── Zone 2: Omicho Market ──
        ("kanazawa", "kanazawa-hotel", "market", "Omicho Market Kanazawa",
         "Omicho Market Kanazawa seafood what to eat guide morning",
         []),
        ("kanazawa", "kanazawa-hotel", "dining", "Omicho Market Kanazawa",
         "sushi breakfast Omicho Market Kanazawa fresh seafood",
         ["tabelog.com"]),
        ("kanazawa", None, "dining", "Kanazawa",
         "Kanazawa local food specialty dishes what to eat unique",
         []),

        # ── Zone 3: Kenroku-en / old town / crafts ──
        ("kanazawa", None, "sightseeing", "Kenroku-en Kanazawa",
         "Kenroku-en garden Kanazawa tips best time visit",
         []),
        ("kanazawa", None, "shopping_crafts", "Kanazawa old town",
         "lacquerware shop Kanazawa old town buy authentic",
         []),
        ("kanazawa", None, "shopping_crafts", "Kanazawa",
         "gold leaf workshop experience Kanazawa hands-on craft",
         []),
        ("kanazawa", None, "ceramics", "Kanazawa",
         "Kutani pottery workshop buy Kanazawa studio",
         []),
        ("kanazawa", None, "dining", "Kanazawa",
         "Kanazawa ramen 8th street style local guide best",
         ["tabelog.com"]),
        ("kanazawa", None, "craft_beer", "Kanazawa",
         "craft beer bar Kanazawa local tap",
         []),
        ("kanazawa", None, "coffee_cafe", "Kanazawa",
         "specialty third wave coffee Kanazawa cafe",
         []),
    ],

    # ═══════════════════════════════════════════════════════════════════════
    # KYOTO — day trip 3/29, Philosophers Path route
    # ═══════════════════════════════════════════════════════════════════════
    "kyoto": [

        # ── Zone 1: Ginkakuji / Philosophers Path start ──
        ("kyoto", None, "coffee_cafe", "Ginkakuji Kyoto",
         "coffee cafe near Ginkakuji Kyoto morning open early breakfast",
         []),
        ("kyoto", None, "sightseeing", "Ginkakuji Kyoto",
         "Ginkakuji Silver Pavilion Kyoto tips morning visit avoid crowds",
         []),
        ("kyoto", None, "temple", "Philosophers Path Kyoto",
         "Honen-in temple quiet Philosophers Path detour Kyoto hidden",
         []),

        # ── Zone 2: Nanzenji / Eikando ──
        ("kyoto", None, "dining", "Nanzenji Kyoto",
         "tofu kaiseki lunch restaurant Nanzenji Kyoto traditional",
         ["tabelog.com"]),
        ("kyoto", None, "dining", "Nanzenji Kyoto",
         "lunch cafe Nanzenji Eikando area Kyoto affordable local",
         ["tabelog.com"]),
        ("kyoto", None, "sightseeing", "Nanzenji Kyoto",
         "Nanzenji temple Meiji aqueduct Kyoto visit guide",
         []),

        # ── Zone 3: Gion / Maruyama / Yasaka ──
        ("kyoto", None, "dining", "Gion Kyoto",
         "lunch restaurant Gion Kyoto traditional hidden local",
         ["tabelog.com"]),
        ("kyoto", None, "dining", "Higashiyama Kyoto",
         "street food snacks Higashiyama Gion Kyoto walk",
         []),
        ("kyoto", None, "coffee_cafe", "Gion Kyoto",
         "third wave specialty coffee Gion Kyoto cafe",
         []),
        ("kyoto", None, "shopping", "Gion Kyoto",
         "antique shop vintage Gion Kyoto traditional",
         []),
        ("kyoto", None, "jewelry_artisan", "Gion Kyoto",
         "handmade artisan craft jewelry shop Gion Kyoto",
         []),

        # ── Zone 4: Higashiyama / Sannenzaka / Kiyomizudera ──
        ("kyoto", None, "ceramics", "Higashiyama Kyoto",
         "Kiyomizu-yaki pottery ceramics shop Sannenzaka Higashiyama Kyoto buy",
         []),
        ("kyoto", None, "dining", "Higashiyama Kyoto",
         "matcha sweets cafe Sannenzaka Ninenzaka Kyoto best",
         []),
        ("kyoto", None, "shopping", "Higashiyama Kyoto",
         "souvenir what to buy Higashiyama Ninenzaka Kyoto traditional",
         []),
        ("kyoto", None, "shopping_crafts", "Higashiyama Kyoto",
         "lacquerware textile craft shop Higashiyama Kyoto",
         []),
        ("kyoto", None, "sightseeing", "Kiyomizudera Kyoto",
         "Kiyomizudera wooden stage sunset Kyoto tips visit",
         []),
        ("kyoto", None, "dining", "Kyoto",
         "best noodle restaurant Kyoto udon soba local",
         ["tabelog.com"]),
    ],

    # ═══════════════════════════════════════════════════════════════════════
    # NARA — day trip 3/25
    # ═══════════════════════════════════════════════════════════════════════
    "nara": [

        # ── Zone 1: Nara Park / Todai-ji ──
        ("nara", "nara-park", "dining", "Nara Park area",
         "lunch restaurant near Nara Park Todai-ji after deer temples",
         ["tabelog.com"]),
        ("nara", "nara-park", "dining", "Nara",
         "Nara local food specialty what to eat unique dishes",
         []),
        ("nara", "nara-park", "sightseeing", "Nara Park",
         "Nara deer park tips etiquette shika senbei crackers guide",
         []),
        ("nara", "nara-park", "coffee_cafe", "Nara Park",
         "cafe coffee shop near Nara Park Todai-ji rest stop",
         []),
        ("nara", "nara-park", "dining", "Nara",
         "street food cheap eat near Nara station park",
         []),

        # ── Zone 2: Naramachi historic district (zero items currently) ──
        ("nara", None, "neighborhood", "Naramachi Nara",
         "Naramachi historic merchant district Nara guide what to see do",
         []),
        ("nara", None, "shopping", "Naramachi Nara",
         "craft artisan shop Naramachi Nara traditional buy",
         []),
        ("nara", None, "ceramics", "Naramachi Nara",
         "pottery craft ceramics shop Naramachi Nara",
         []),
        ("nara", None, "dining", "Naramachi Nara",
         "restaurant cafe Naramachi Nara hidden local lunch",
         ["tabelog.com"]),
        ("nara", None, "shopping", "Naramachi Nara",
         "antique vintage shop Naramachi Nara",
         []),

        # ── Zone 3: Higashimuki / Kintetsu station area ──
        ("nara", None, "shopping", "Higashimuki Nara",
         "Higashimuki shopping arcade Nara what to buy souvenir",
         []),
        ("nara", None, "dining", "Kintetsu Nara station",
         "ramen noodles restaurant near Kintetsu Nara station",
         ["tabelog.com"]),
        ("nara", None, "sake_brewery", "Nara",
         "sake Nara Harushika brewery tasting local",
         []),
    ],
}

# ---------------------------------------------------------------------------

def tavily_search(query: str, domains: list, max_results: int = 5) -> list:
    """Call Tavily gateway, return list of result dicts."""
    payload = {
        "query": query,
        "max_results": max_results,
        "search_depth": "basic",
    }
    if domains:
        payload["include_domains"] = domains
    try:
        resp = httpx.post(f"{TAVILY_GW}/v1/search", json=payload, timeout=20.0)
        resp.raise_for_status()
        return resp.json().get("results") or []
    except Exception as e:
        print(f"    ⚠  Tavily error: {e}")
        return []


def already_exists(cur, city: str, source_url: str, topic: str) -> bool:
    """Return True if we already have this result."""
    if source_url:
        cur.execute(
            "SELECT 1 FROM knowledge_items WHERE LOWER(city)=%s AND source_url=%s LIMIT 1",
            (city.lower(), source_url),
        )
    else:
        cur.execute(
            "SELECT 1 FROM knowledge_items WHERE LOWER(city)=%s AND topic=%s LIMIT 1",
            (city.lower(), topic),
        )
    return cur.fetchone() is not None


def run_city(city: str):
    entries = QUERY_MATRIX.get(city)
    if not entries:
        print(f"Unknown city: {city}")
        sys.exit(1)

    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()

    total_inserted = 0
    total_skipped  = 0
    total_queries  = len(entries)

    print(f"\n{'='*60}")
    print(f"  Knowledge pipeline — {city.upper()} — {total_queries} queries")
    print(f"{'='*60}\n")

    for idx, (db_city, anchor, category, district, query, domains) in enumerate(entries, 1):
        print(f"[{idx:02d}/{total_queries}] {category} | {district}")
        print(f"        Query: {query[:70]}")

        results = tavily_search(query, domains)

        if not results:
            print("        → 0 results\n")
            time.sleep(0.5)
            continue

        inserted = 0
        for r in results:
            title   = (r.get("title") or "").strip()
            content = (r.get("content") or "").strip()
            url     = r.get("url") or None
            score   = float(r.get("score") or 0)

            if not title or not content:
                continue

            # Score threshold — save everything if sparse (<3 results), else 0.4+
            if len(results) >= 3 and score < 0.4:
                continue

            # Topic: title + district context for searchability
            topic = f"{title[:80]} [{district}]"

            if already_exists(cur, db_city, url, topic):
                total_skipped += 1
                continue

            summary = content[:400]

            try:
                cur.execute(
                    """INSERT INTO knowledge_items
                       (city, anchor, category, topic, source_url, content_summary, tavily_score)
                       VALUES (%s,%s,%s,%s,%s,%s,%s)""",
                    (db_city, anchor, category, topic, url, summary, score),
                )
                conn.commit()
                inserted += 1
                total_inserted += 1
                print(f"        ✓ {title[:65]}")
            except psycopg2.errors.UniqueViolation:
                conn.rollback()
                total_skipped += 1

        print(f"        → {inserted} inserted\n")
        time.sleep(0.6)   # gentle rate limiting

    cur.close()
    conn.close()

    print(f"\n{'='*60}")
    print(f"  {city.upper()} COMPLETE")
    print(f"  Inserted: {total_inserted}  |  Skipped (dups): {total_skipped}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: ingest_knowledge_pipeline.py <city>")
        print("  Cities: osaka, kanazawa, kyoto, nara")
        sys.exit(1)

    city_arg = sys.argv[1].lower()
    run_city(city_arg)
