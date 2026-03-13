#!/usr/bin/env python3
"""
seed_users.py — Seed the users and user_preferences tables for the Japan trip.

Run once before departure from brainnode-01:
  cd /opt/git/work/shogun/app-services/shogun-core
  source venv/bin/activate
  python tools/seed_users.py

Requires TELEGRAM_USER_ID_BRENDA and TELEGRAM_USER_ID_MADELINE set in .env
(Todd's ID is already known: 204595710).
"""
import os
import sys
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host":     os.environ["DB_HOST"],
    "port":     int(os.environ.get("DB_PORT", 5432)),
    "dbname":   os.environ["DB_NAME"],
    "user":     os.environ["DB_USER"],
    "password": os.environ["DB_PASSWORD"],
}

TODD_TG_ID    = int(os.environ.get("TELEGRAM_USER_ID_TODD",    "204595710"))
BRENDA_TG_ID  = int(os.environ.get("TELEGRAM_USER_ID_BRENDA",  "0"))
MADELINE_TG_ID = int(os.environ.get("TELEGRAM_USER_ID_MADELINE", "0"))

if BRENDA_TG_ID == 0 or MADELINE_TG_ID == 0:
    print("ERROR: Set TELEGRAM_USER_ID_BRENDA and TELEGRAM_USER_ID_MADELINE in .env")
    sys.exit(1)

USERS = [
    {"telegram_user_id": TODD_TG_ID,    "display_name": "Todd",    "full_name": "Todd Ibbotson",    "notification_active": True,  "language_preference": "en"},
    {"telegram_user_id": BRENDA_TG_ID,  "display_name": "Brenda",  "full_name": "Brenda Loo",       "notification_active": False, "language_preference": "en"},
    {"telegram_user_id": MADELINE_TG_ID,"display_name": "Madeline","full_name": "Madeline Ibbotson","notification_active": False, "language_preference": "en"},
]

# Preferences known at build time — extended after questionnaire returns
PREFERENCES = [
    # Todd — dietary
    (TODD_TG_ID, "dietary", "eats",   "beef",    None),
    (TODD_TG_ID, "dietary", "eats",   "chicken", None),
    (TODD_TG_ID, "dietary", "eats",   "fish",    "some fish"),
    # Todd — shopping
    (TODD_TG_ID, "shopping", "interest_type", "vintage_cameras",        "no DSLR, no large lens"),
    (TODD_TG_ID, "shopping", "interest_type", "electronics_components", "ESP32, maker components, Akihabara"),
    (TODD_TG_ID, "shopping", "interest_type", "ceramics",               "Kanazawa Kutani ware primary target"),
    (TODD_TG_ID, "shopping", "interest_type", "grooming_kit",           "local Japanese steel, Sakai"),
    (TODD_TG_ID, "shopping", "interest_type", "vintage_anime_figures",  None),

    # Brenda — dietary
    (BRENDA_TG_ID, "dietary", "eats",   "fish",          None),
    (BRENDA_TG_ID, "dietary", "eats",   "dashi",         "fish-based broths OK"),
    (BRENDA_TG_ID, "dietary", "eats",   "beef_broth",    "broth OK, meat not"),
    (BRENDA_TG_ID, "dietary", "eats",   "vegetarian",    None),
    (BRENDA_TG_ID, "dietary", "avoids", "red_meat",      "pork, lamb, beef steak as protein — broth is fine"),

    # Madeline — dietary
    (MADELINE_TG_ID, "dietary", "eats",   "chicken_katsu", "favourite"),
    (MADELINE_TG_ID, "dietary", "eats",   "beef",          None),
    (MADELINE_TG_ID, "dietary", "avoids", "fish",          None),
    # Madeline — shopping
    (MADELINE_TG_ID, "shopping", "interest_type", "vintage_cameras",       "no DSLR, no large lens"),
    (MADELINE_TG_ID, "shopping", "interest_type", "vintage_anime_figures", None),
    (MADELINE_TG_ID, "shopping", "interest_type", "used_clothing",         "Harajuku / Shimokitazawa style"),
    (MADELINE_TG_ID, "shopping", "interest_type", "retro_gaming",          "Gameboy-era handheld consoles"),
    # Madeline — entertainment
    (MADELINE_TG_ID, "entertainment", "interest_type", "anime",    "Ghibli confirmed, others TBD"),
    (MADELINE_TG_ID, "entertainment", "interest_type", "ghibli",   "Ghibli Museum Apr 3"),
]


def seed():
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        with conn.cursor() as cur:
            user_id_map = {}  # telegram_user_id → users.id

            for u in USERS:
                cur.execute("""
                    INSERT INTO users (telegram_user_id, display_name, full_name, notification_active, language_preference, created_utc)
                    VALUES (%(telegram_user_id)s, %(display_name)s, %(full_name)s, %(notification_active)s, %(language_preference)s, NOW())
                    ON CONFLICT (telegram_user_id) DO UPDATE
                      SET display_name = EXCLUDED.display_name,
                          full_name    = EXCLUDED.full_name
                    RETURNING id
                """, u)
                row = cur.fetchone()
                user_id_map[u["telegram_user_id"]] = row[0]
                print(f"  Upserted user: {u['display_name']} (id={row[0]})")

            for (tg_id, category, key, value, notes) in PREFERENCES:
                uid = user_id_map.get(tg_id)
                if not uid:
                    print(f"  SKIP pref: telegram_user_id={tg_id} not in users")
                    continue
                cur.execute("""
                    INSERT INTO user_preferences (user_id, category, preference_key, preference_value, notes, created_utc)
                    VALUES (%s, %s, %s, %s, %s, NOW())
                    ON CONFLICT DO NOTHING
                """, (uid, category, key, value, notes))

            conn.commit()
            print(f"\nSeeded {len(USERS)} users and {len(PREFERENCES)} preference rows.")
            print("Run again safely — uses ON CONFLICT DO NOTHING for preferences.")

    except Exception as exc:
        conn.rollback()
        print(f"ERROR: {exc}")
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    print("Seeding shogun_v1 users and preferences...")
    seed()
