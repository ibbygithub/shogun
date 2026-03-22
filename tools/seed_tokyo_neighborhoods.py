"""
seed_tokyo_neighborhoods.py — Supplement Tokyo knowledge for itinerary neighborhoods.

The original seed_tokyo_knowledge.py covered only sugamo, ueno, and ghibli anchors
plus a handful of general interest topics. This script adds coverage for the remaining
8-day Tokyo itinerary areas: Shinjuku, Shibuya, Harajuku/Omotesando, Asakusa,
Akihabara, Ikebukuro/Sunshine City, Kichijoji, and Ginza.

Usage (on brainnode-01):
    docker exec shogun-web-api python tools/seed_tokyo_neighborhoods.py
"""
import os
import sys
import time
import httpx
import psycopg2

DATABASE_URL = os.environ["DATABASE_URL"]
TAVILY_URL   = os.environ.get("TAVILY_GATEWAY_URL", "http://platform-tavily:8084") + "/v1/search"

INTER_CALL_DELAY = 1.5

# (anchor, city, category, query)
# anchor=None for interest-based; named anchor for location-biased
TOPICS = [

    # ── Asakusa ──────────────────────────────────────────────────────────────
    (None, "tokyo", "temple",       "Senso-ji Asakusa visit guide best time crowds Nakamise 2026"),
    (None, "tokyo", "market",       "Nakamise shopping street Asakusa what to buy souvenirs snacks"),
    (None, "tokyo", "sakura",       "Sumida Park sakura 2026 cherry blossom bloom hanami Asakusa"),
    (None, "tokyo", "restaurant",   "best restaurants near Asakusa Nakamise traditional Tokyo dinner"),
    (None, "tokyo", "neighborhood", "Asakusa area guide rickshaw craft shops traditional Tokyo"),

    # ── Shinjuku ──────────────────────────────────────────────────────────────
    (None, "tokyo", "neighborhood", "Omoide Yokocho Memory Lane Shinjuku yakitori bars guide"),
    (None, "tokyo", "park",         "Shinjuku Gyoen National Garden sakura 2026 tips admission"),
    (None, "tokyo", "sightseeing",  "Tokyo Metropolitan Government Building free observatory night views"),
    (None, "tokyo", "sightseeing",  "Kabukicho Shinjuku nightlife guide Godzilla head Robot Restaurant area"),
    (None, "tokyo", "shrine",       "Hanazono Shrine Shinjuku flea market antiques guide"),
    (None, "tokyo", "shopping",     "Shinjuku shopping guide Takashimaya Times Square department store"),

    # ── Shibuya ───────────────────────────────────────────────────────────────
    (None, "tokyo", "sightseeing",  "Shibuya Crossing best time scramble viewing tips 2026"),
    (None, "tokyo", "shopping",     "Shibuya 109 fashion guide what to buy trends 2026"),
    (None, "tokyo", "shopping",     "Parco Shibuya floor guide Nintendo Tokyo Pokemon character shops"),
    (None, "tokyo", "shopping",     "Mega Don Quijote Shibuya best buys hours what to purchase"),
    (None, "tokyo", "shopping",     "Loft Shibuya stationery gifts design what to buy Japan 2026"),

    # ── Harajuku / Omotesando ─────────────────────────────────────────────────
    (None, "tokyo", "neighborhood", "Takeshita Street Harajuku guide crepes kawaii fashion morning tip"),
    (None, "tokyo", "neighborhood", "Cat Street Harajuku Ura-Harajuku indie boutiques cafes walkthrough"),
    (None, "tokyo", "neighborhood", "Omotesando shopping architecture guide luxury brands Tokyo"),
    (None, "tokyo", "shrine",       "Meiji Jingu Shrine visit guide forest walk Harajuku"),
    (None, "tokyo", "park",         "Yoyogi Park hanami picnic sakura 2026 Harajuku guide"),
    (None, "tokyo", "shopping",     "Kiddyland Omotesando character goods toys floors guide"),
    (None, "tokyo", "skincare",     "@Cosme Tokyo Harajuku beauty store guide best buys skincare"),

    # ── Akihabara ─────────────────────────────────────────────────────────────
    (None, "tokyo", "shopping",     "Akihabara Radio Kaikan guide floors what to buy figures models"),
    (None, "tokyo", "shopping",     "Akihabara anime manga electronics guide Chuo Dori 2026"),
    (None, "tokyo", "shopping",     "Akihabara retro games gashapons best shops Otome Road Tokyo"),

    # ── Ikebukuro / Sunshine City ─────────────────────────────────────────────
    (None, "tokyo", "shopping",     "Sunshine City Ikebukuro Pokemon Center Mega Tokyo Chiikawa guide"),
    (None, "tokyo", "shopping",     "Ikebukuro shopping guide Animate Otome Road character merchandise"),
    (None, "tokyo", "restaurant",   "best restaurants near Ikebukuro ramen gyoza Japanese food 2026"),

    # ── Kichijoji ─────────────────────────────────────────────────────────────
    (None, "tokyo", "shopping",     "Kichijoji shopping guide boutiques vintage cafes local scene"),
    (None, "tokyo", "restaurant",   "best cafes and food Kichijoji Harmonica Yokocho Shirohige cream puff"),
    (None, "tokyo", "park",         "Inokashira Park Kichijoji guide sakura swan boats Ghibli Museum walk"),

    # ── Ginza ─────────────────────────────────────────────────────────────────
    (None, "tokyo", "shopping",     "Uniqlo Ginza flagship store guide UTme floors what to buy 2026"),
    (None, "tokyo", "shopping",     "Ginza shopping guide highlights Itoya Mitsukoshi flagship stores"),

    # ── Transit / Practical ───────────────────────────────────────────────────
    (None, "tokyo", "transit",      "getting from Sugamo to Shibuya Harajuku Shinjuku best train route Tokyo"),
    (None, "tokyo", "transit",      "IC card Suica Pasmo Tokyo train tips tourist 2026"),
    (None, "tokyo", "pharmacy",     "pharmacy drugstore Tokyo Matsumoto Kiyoshi Welcia skincare must buy"),
    (None, "tokyo", "practical",    "Tokyo convenience store FamilyMart Lawson 7-Eleven what to buy tips"),

    # ── Experiences ───────────────────────────────────────────────────────────
    (None, "tokyo", "restaurant",   "Samurai ninja themed restaurants Tokyo dinner show experience"),
    (None, "tokyo", "sakura",       "best sakura spots Tokyo 2026 late March April bloom forecast"),
    (None, "tokyo", "street_food",  "Tokyo character themed food Chiikawa bakery Totoro cream puff"),
]


INSERT_SQL = """
INSERT INTO knowledge_items (anchor, city, category, topic, source_url, content_summary, tavily_score)
VALUES (%s, %s, %s, %s, %s, %s, %s)
ON CONFLICT DO NOTHING;
"""


def search_tavily(query: str, max_results: int = 5) -> list[dict]:
    payload = {"query": query, "max_results": max_results, "search_depth": "basic"}
    resp = httpx.post(TAVILY_URL, json=payload, timeout=30)
    resp.raise_for_status()
    return resp.json().get("results", [])


def main():
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = False

    inserted_total = 0
    skipped_total  = 0
    error_total    = 0

    for idx, (anchor, city, category, query) in enumerate(TOPICS, start=1):
        anchor_label = anchor or "(general)"
        print(f"\n[{idx}/{len(TOPICS)}] {anchor_label} / {category}")
        print(f"  query: {query[:80]}")

        try:
            results = search_tavily(query, max_results=5)
            print(f"  Tavily: {len(results)} result(s)")
        except Exception as exc:
            print(f"  [ERROR] Tavily: {exc}", file=sys.stderr)
            error_total += 1
            time.sleep(INTER_CALL_DELAY)
            continue

        inserted_this = 0
        skipped_this  = 0
        for result in results:
            url     = result.get("url", "")
            summary = result.get("content", "")
            score   = result.get("score")
            if not url:
                skipped_this += 1
                continue
            try:
                with conn.cursor() as cur:
                    cur.execute(INSERT_SQL, (anchor, city, category, query, url, summary, score))
                    if cur.rowcount > 0:
                        inserted_this += 1
                    else:
                        skipped_this += 1
                conn.commit()
            except Exception as exc:
                conn.rollback()
                print(f"  [ERROR] insert {url}: {exc}", file=sys.stderr)
                skipped_this += 1

        print(f"  inserted={inserted_this}  skipped/dup={skipped_this}")
        inserted_total += inserted_this
        skipped_total  += skipped_this
        time.sleep(INTER_CALL_DELAY)

    conn.close()

    print("\n" + "=" * 60)
    print("SEEDING COMPLETE")
    print(f"  inserted : {inserted_total}")
    print(f"  skipped  : {skipped_total}")
    print(f"  errors   : {error_total}")
    print("=" * 60)

    # Final count by category
    verify = psycopg2.connect(DATABASE_URL)
    try:
        with verify.cursor() as cur:
            cur.execute(
                "SELECT category, count(*) FROM knowledge_items WHERE city='tokyo' "
                "GROUP BY category ORDER BY count(*) DESC"
            )
            rows = cur.fetchall()
        print("\nknowledge_items WHERE city='tokyo' by category:")
        total = 0
        for r in rows:
            print(f"  {r[0]:<25} {r[1]}")
            total += r[1]
        print(f"  TOTAL: {total}")
    finally:
        verify.close()


if __name__ == "__main__":
    main()
