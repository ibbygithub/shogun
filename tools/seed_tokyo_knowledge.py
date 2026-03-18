"""
seed_tokyo_knowledge.py — Seed the Tokyo knowledge base in shogun_v1.

Runs inside the shogun-web-api container (has DB + Tavily gateway access).
Usage: docker exec shogun-web-api python tools/seed_tokyo_knowledge.py

Steps:
  1. Creates knowledge_items table if it does not exist.
  2. For each topic, calls the Tavily gateway (POST /v1/search).
  3. Inserts results into knowledge_items, deduplicating on (anchor, category, source_url).

Connection: DATABASE_URL from environment (set by docker-compose via .env).
Tavily:     http://platform-tavily:8084/v1/search
"""

import os
import sys
import time
import httpx
import psycopg2

# ── Configuration ────────────────────────────────────────────────────────────

DATABASE_URL = os.environ["DATABASE_URL"]
TAVILY_URL   = os.environ.get("TAVILY_GATEWAY_URL", "http://platform-tavily:8084") + "/v1/search"

# Seconds to pause between Tavily calls — avoids hammering the upstream API.
INTER_CALL_DELAY = 1.5

# Topics to seed. Each entry: (anchor, city, category, query)
# anchor=None means interest-based (no location anchor).
TOPICS = [
    # ── Interest-based (anchor=None) ──────────────────────────────────────
    (None, "tokyo", "vintage",      "Shimokitazawa vintage clothing Tokyo best shops 2026"),
    (None, "tokyo", "vintage",      "Koenji vintage clothing shops Tokyo"),
    (None, "tokyo", "skincare",     "best skincare shops Tokyo Cosme Matsumoto Kiyoshi Loft Tokyu Hands must buy"),
    (None, "tokyo", "skincare",     "Japanese face cream serum best buys tourists Tokyo 2026"),
    (None, "tokyo", "street_food",  "best street food Tokyo Yanaka Ginza Ameyoko vendors what to eat"),
    (None, "tokyo", "shopping",     "Harajuku Omotesando shopping guide fashion youth culture"),
    (None, "tokyo", "shopping",     "Don Quijote Tokyo what to buy souvenirs"),
    (None, "tokyo", "temple",       "Senso-ji Asakusa tips avoid crowds best time visit"),
    (None, "tokyo", "temple",       "lesser known temples Tokyo hidden gems alternatives"),
    (None, "tokyo", "events",       "Tokyo events late March April 2026 hanami sakura festivals"),

    # ── anchor: tokyo-sugamo ──────────────────────────────────────────────
    ("tokyo-sugamo", "tokyo", "restaurant",   "best ramen restaurants near Sugamo Toshima Tokyo"),
    ("tokyo-sugamo", "tokyo", "temple",       "Koganji Temple Sugamo Togenuki Jizo shopping street guide"),
    ("tokyo-sugamo", "tokyo", "local_market", "Sugamo Jizo-dori shopping street what to buy"),
    ("tokyo-sugamo", "tokyo", "pharmacy",     "pharmacy near Sugamo station Tokyo"),

    # ── anchor: tokyo-ueno ───────────────────────────────────────────────
    ("tokyo-ueno", "tokyo", "museum",     "Tokyo National Museum highlights must see exhibits 2026"),
    ("tokyo-ueno", "tokyo", "market",     "Ameyoko market Ueno hours best things to buy street food"),
    ("tokyo-ueno", "tokyo", "restaurant", "best restaurants near Ueno Park Tokyo"),
    ("tokyo-ueno", "tokyo", "sakura",     "Ueno Park cherry blossom 2026 sakura forecast bloom"),

    # ── anchor: ghibli-museum ────────────────────────────────────────────
    ("ghibli-museum", "tokyo", "restaurant", "restaurants near Ghibli Museum Mitaka Tokyo"),
    ("ghibli-museum", "tokyo", "transit",    "how to get to Ghibli Museum from Sugamo Tokyo train"),
]

# ── DB helpers ───────────────────────────────────────────────────────────────

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS knowledge_items (
  id              SERIAL PRIMARY KEY,
  anchor          TEXT,
  city            TEXT,
  category        TEXT,
  topic           TEXT,
  source_url      TEXT,
  content_summary TEXT,
  raw_content     TEXT,
  tavily_score    FLOAT,
  ingested_utc    TIMESTAMPTZ DEFAULT now()
);
"""

INSERT_SQL = """
INSERT INTO knowledge_items (anchor, city, category, topic, source_url, content_summary, tavily_score)
VALUES (%s, %s, %s, %s, %s, %s, %s)
ON CONFLICT DO NOTHING;
"""

# Unique constraint for deduplication — created after table if absent.
UNIQUE_IDX_SQL = """
CREATE UNIQUE INDEX IF NOT EXISTS uidx_knowledge_anchor_cat_url
    ON knowledge_items (
        COALESCE(anchor, ''),
        COALESCE(category, ''),
        COALESCE(source_url, '')
    );
"""


def ensure_schema(cur):
    cur.execute(CREATE_TABLE_SQL)
    cur.execute(UNIQUE_IDX_SQL)


# ── Tavily helpers ────────────────────────────────────────────────────────────

def search_tavily(query: str, max_results: int = 5) -> list[dict]:
    """Call the Tavily gateway and return a list of result dicts."""
    payload = {
        "query":        query,
        "max_results":  max_results,
        "search_depth": "basic",
    }
    resp = httpx.post(TAVILY_URL, json=payload, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    return data.get("results", [])


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = False

    try:
        with conn.cursor() as cur:
            ensure_schema(cur)
        conn.commit()
        print("[schema] knowledge_items table and unique index ready.")
    except Exception as exc:
        conn.rollback()
        print(f"[ERROR] Schema setup failed: {exc}", file=sys.stderr)
        sys.exit(1)

    inserted_total = 0
    skipped_total  = 0
    error_total    = 0

    for idx, (anchor, city, category, query) in enumerate(TOPICS, start=1):
        anchor_label = anchor or "(interest-based)"
        print(f"\n[{idx}/{len(TOPICS)}] {anchor_label} / {category} — {query[:70]}")

        # Tavily call
        try:
            results = search_tavily(query, max_results=5)
            print(f"  Tavily returned {len(results)} result(s)")
        except Exception as exc:
            print(f"  [ERROR] Tavily call failed: {exc}", file=sys.stderr)
            error_total += 1
            time.sleep(INTER_CALL_DELAY)
            continue

        # Insert each result
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
                    cur.execute(
                        INSERT_SQL,
                        (anchor, city, category, query, url, summary, score),
                    )
                    if cur.rowcount > 0:
                        inserted_this += 1
                    else:
                        skipped_this += 1
                conn.commit()
            except Exception as exc:
                conn.rollback()
                print(f"  [ERROR] Insert failed for {url}: {exc}", file=sys.stderr)
                skipped_this += 1

        print(f"  inserted={inserted_this}  skipped/dup={skipped_this}")
        inserted_total += inserted_this
        skipped_total  += skipped_this

        time.sleep(INTER_CALL_DELAY)

    conn.close()

    # ── Verification ──────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("SEEDING COMPLETE")
    print(f"  Total inserted : {inserted_total}")
    print(f"  Total skipped  : {skipped_total}")
    print(f"  Total errors   : {error_total}")
    print("=" * 60)

    # Run counts by category for the final report
    verify_conn = psycopg2.connect(DATABASE_URL)
    try:
        with verify_conn.cursor() as cur:
            cur.execute(
                """
                SELECT city, category, count(*)
                FROM knowledge_items
                WHERE city = 'tokyo'
                GROUP BY city, category
                ORDER BY city, category;
                """
            )
            rows = cur.fetchall()

        print("\nVerification — knowledge_items WHERE city='tokyo':")
        total = 0
        for row in rows:
            print(f"  {row[0]} / {row[1]}: {row[2]}")
            total += row[2]
        print(f"  TOTAL: {total}")

        passing = total >= 20
        print(f"\nMinimum 20 records: {'PASS' if passing else 'FAIL'} ({total})")

        required_min3 = ["vintage", "skincare", "street_food", "temple", "museum"]
        cat_map = {r[1]: r[2] for r in rows}
        for cat in required_min3:
            cnt = cat_map.get(cat, 0)
            status = "PASS" if cnt >= 3 else "FAIL"
            print(f"  {cat} >= 3: {status} ({cnt})")

    finally:
        verify_conn.close()


if __name__ == "__main__":
    main()
