#!/usr/bin/env python3
"""
Seed tool — trip_itinerary table.

Clears and reloads all rows. Idempotent — safe to re-run.

Run from brainnode-01:
    cd /opt/git/work/shogun/app-services/shogun-core
    source venv/bin/activate && python tools/seed_itinerary.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv()

import psycopg2

conn_params = dict(
    host=os.environ["DB_HOST"],
    port=int(os.environ.get("DB_PORT", 5432)),
    dbname=os.environ["DB_NAME"],
    user=os.environ["DB_USER"],
    password=os.environ["DB_PASSWORD"],
)

# ── Trip itinerary ──────────────────────────────────────────────────────────
# All confirmed legs. Dates are local Japan time (JST).
# TBD items (Kyoto, Sakai) omitted — they are in trip_pois instead.

ITINERARY = [
    # ── Outbound flights (Mar 23) ──
    {
        "leg_sequence": 1,
        "leg_type": "flight",
        "date_local": "2026-03-23",
        "city": "San Francisco",
        "title": "JL7555 SFO → LAX",
        "address_en": "San Francisco International Airport",
        "address_ja": "サンフランシスコ国際空港",
        "confirmation_number": "APGNWZ",
        "notes_en": "Japan Airlines codeshare SFO→LAX connector. Connects to JL69 at Tom Bradley International Terminal (LAX).",
        "start_time": None,
        "end_time": None,
    },
    {
        "leg_sequence": 2,
        "leg_type": "flight",
        "date_local": "2026-03-23",
        "city": "Los Angeles",
        "title": "JL69 LAX → KIX (Kansai International)",
        "address_en": "Los Angeles International Airport, Tom Bradley International Terminal",
        "address_ja": "ロサンゼルス国際空港",
        "confirmation_number": "APGNWZ",
        "notes_en": "Japan Airlines direct to Kansai International. PNR: APGNWZ. Arrives KIX next afternoon. From KIX to Osaka Namba by Haruka express or airport bus.",
        "start_time": None,
        "end_time": None,
    },

    # ── Osaka leg (Mar 24–30) ──
    {
        "leg_sequence": 3,
        "leg_type": "accommodation",
        "date_local": "2026-03-24",
        "city": "Osaka",
        "title": "Tenjinbashi Queen Airbnb — check in",
        "address_en": "10-12 Namihana-cho, Kita-ku, Osaka 530-0022",
        "address_ja": "大阪市北区浪花町10-12 530-0022",
        "notes_en": "Airbnb host: Mayu (contact via Airbnb app). Tenjinbashisuji-Rokuchome area. Nearest station: Tenjinbashisuji-Rokuchome on Osaka Metro Sakaisujisen/Tanimachi line. Supermarket and 7-Eleven within 2 min walk.",
        "start_time": None,
        "end_time": None,
    },
    {
        "leg_sequence": 4,
        "leg_type": "activity",
        "date_local": "2026-03-25",
        "city": "Nara",
        "title": "Nara day trip — deer park, Todai-ji, Kasugataisha, Naramachi",
        "address_en": "Nara Park, Nara City, Nara Prefecture",
        "address_ja": "奈良公園 奈良市",
        "notes_en": "DEPART EARLY — arrive Nara before 9am to beat tour buses. Cherry blossom peak (late March) makes this timing critical. Route: Tenjinbashisuji-Rokuchome → Osaka Metro to Namba → Kintetsu Nara Line direct (~40 min). Kasugataisha Shrine is 10 min walk from deer park and far less crowded than Todai-ji. Naramachi historic district best before 10am.",
        "start_time": None,
        "end_time": None,
    },
    {
        "leg_sequence": 5,
        "leg_type": "activity",
        "date_local": "2026-03-26",
        "city": "Osaka",
        "title": "Universal Studios Japan (USJ) — Nintendo World",
        "address_en": "2-1-33 Sakurajima, Konohana-ku, Osaka 554-0031",
        "address_ja": "大阪市此花区桜島2-1-33 554-0031",
        "notes_en": "DEPART AIRBNB 5:30AM to arrive gates ~6:30am. Route: Tenjinbashisuji-Rokuchome → Osaka Metro Sakaisujisen → Osaka Station → JR Osaka Loop Line → Nishikujo → JR Yumesaki Line → Universal City Station. Nintendo World (Todd + Madeline) is the primary target — express pass highly recommended.",
        "start_time": "05:30",
        "end_time": None,
    },

    # ── Osaka → Kanazawa transition (Mar 30) ──
    {
        "leg_sequence": 6,
        "leg_type": "transit",
        "date_local": "2026-03-30",
        "city": "Osaka",
        "title": "Check out Tenjinbashi Queen → depart for Kanazawa",
        "notes_en": "Check out Tenjinbashi Queen Airbnb. Travel to Kanazawa by Thunderbird limited express (Osaka Umeda → Kanazawa, ~2h30m). Depart from Osaka Umeda station.",
        "start_time": None,
        "end_time": None,
    },

    # ── Kanazawa leg (Mar 30–Apr 1) ──
    {
        "leg_sequence": 7,
        "leg_type": "accommodation",
        "date_local": "2026-03-30",
        "city": "Kanazawa",
        "title": "Hotel Sanraku Kanazawa — check in",
        "address_en": "1-1-1 Owaricho, Kanazawa, Ishikawa 920-0902",
        "address_ja": "石川県金沢市尾張町1-1-1 920-0902",
        "notes_en": "Hotel Sanraku. Central location — Omicho Market 5 min walk, Higashi Chaya 10 min walk, Kenroku-en 15 min walk.",
        "start_time": None,
        "end_time": None,
    },

    # ── Kanazawa → Tokyo transition (Apr 1) ──
    {
        "leg_sequence": 8,
        "leg_type": "transit",
        "date_local": "2026-04-01",
        "city": "Kanazawa",
        "title": "Check out Hotel Sanraku → depart for Tokyo",
        "notes_en": "Check out Hotel Sanraku. Travel to Tokyo — Kagayaki Shinkansen Kanazawa → Tokyo (~2.5 hours) or Thunderbird to Tsuruga + Shinkansen. Brenda has train booking details.",
        "start_time": None,
        "end_time": None,
    },

    # ── Tokyo leg (Apr 1–9) ──
    {
        "leg_sequence": 9,
        "leg_type": "accommodation",
        "date_local": "2026-04-01",
        "city": "Tokyo",
        "title": "Sugamo Airbnb (Toshima-ku) — check in",
        "address_en": "4-37-6 Sugamo, Toshima-ku, Tokyo 170-0002",
        "address_ja": "東京都豊島区巣鴨4-37-6 170-0002",
        "notes_en": "Tokyo base. Sugamo station on Yamanote Line and Mita Line. 1 stop to Ikebukuro. Jizo-dori traditional shopping street 1 min walk. Supermarket nearby.",
        "start_time": None,
        "end_time": None,
    },
    {
        "leg_sequence": 10,
        "leg_type": "activity",
        "date_local": "2026-04-03",
        "city": "Tokyo",
        "title": "Ghibli Museum — Mitaka (TIMED ENTRY NOON)",
        "address_en": "1-1-83 Shimorenjaku, Mitaka, Tokyo 181-0013",
        "address_ja": "東京都三鷹市下連雀1-1-83 181-0013",
        "confirmation_number": "7961560155",
        "notes_en": "TIMED ENTRY: 12:00 NOON. Booking: 7961560155. DO NOT BE LATE — no late entry. Route from Sugamo: Yamanote to Shinjuku → JR Chuo Line rapid to Mitaka → 10 min walk or shuttle bus (200 yen). Allow 40 min travel. DEPART SUGAMO BY 10:45AM.",
        "start_time": "12:00",
        "end_time": None,
    },

    # ── Return flight (Apr 9) ──
    {
        "leg_sequence": 11,
        "leg_type": "flight",
        "date_local": "2026-04-09",
        "city": "Tokyo",
        "title": "JL2 HND → SFO — departure 4:25pm",
        "address_en": "Tokyo Haneda Airport, International Terminal 3",
        "address_ja": "東京国際空港（羽田空港）国際線ターミナル",
        "confirmation_number": "APGNWZ",
        "notes_en": "Departure 4:25pm. DEPART SUGAMO BY 1:30PM. Route: Sugamo → Yamanote to Hamamatsucho → Tokyo Monorail to HND (20 min); OR Sugamo → Mita Line to Mita → Keikyu Line to HND. Allow 2.5 hours for international check-in and security.",
        "start_time": "16:25",
        "end_time": None,
    },
]


def main():
    conn = psycopg2.connect(**conn_params)
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM trip_itinerary")
            print(f"Cleared trip_itinerary.")

            for row in ITINERARY:
                cur.execute(
                    """
                    INSERT INTO trip_itinerary
                        (leg_sequence, leg_type, date_local, city, title,
                         address_en, address_ja, contact_phone, confirmation_number,
                         notes_en, start_time, end_time)
                    VALUES
                        (%(leg_sequence)s, %(leg_type)s, %(date_local)s, %(city)s, %(title)s,
                         %(address_en)s, %(address_ja)s, %(contact_phone)s, %(confirmation_number)s,
                         %(notes_en)s, %(start_time)s, %(end_time)s)
                    """,
                    {
                        "address_en": None, "address_ja": None,
                        "contact_phone": None, "confirmation_number": None,
                        "notes_en": None, "start_time": None, "end_time": None,
                        **row,
                    },
                )
                seq = row["leg_sequence"]
                print(f"  [{seq:02d}] {row['date_local']} {row['city']:12s} — {row['title']}")

        conn.commit()
        print(f"\n✅ Inserted {len(ITINERARY)} itinerary rows.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
