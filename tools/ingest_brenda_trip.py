"""
Brenda trip plan ingestion — 2026-03-20
Inserts trip_itinerary legs, trip_pois, and knowledge_items from brenda-trip-plan.md
Run inside shogun-web-api container: python3 /app/tools/ingest_brenda_trip.py
"""
import psycopg2, os

conn = psycopg2.connect(os.environ['DATABASE_URL'])
conn.autocommit = False
cur = conn.cursor()

try:
    # ── BATCH 1: DELETES ─────────────────────────────────────────────
    cur.execute("DELETE FROM trip_itinerary WHERE id IN (21, 4, 5)")
    print(f"BATCH 1 — DELETES: {cur.rowcount} rows removed (IDs 21=Orange Burger, 4=Nara combined, 5=USJ combined)")

    # ── BATCH 2: 3/24 Osaka arrival ──────────────────────────────────
    legs_0324 = [
        (20, "transit",    "2026-03-24", "Osaka", "Airport Limo to Umeda to Tenjinbashisuji 6-chome",
         None, None,
         "Airport Limo Bus to Umeda Station, walk to Higashi Umeda, Tanimachi Line 4 stops to Tenjinbashisuji-Rokuchome, exit gate 13 toward Tenjinbashisuji shopping street",
         None),
        (21, "restaurant", "2026-03-24", "Osaka", "Hitotsuzuki - okonomiyaki (dinner option)",
         "1 Chome-6-4 Ukida, Kita Ward, Osaka 530-0021", None,
         "Near Airbnb. Brenda pick. Flexible - any evening during Osaka stay.",
         None),
        (22, "restaurant", "2026-03-24", "Osaka", "Umeda Okonomiyaki Izakaya Fuwatoro (dinner option)",
         "Kita Ward, Osaka", None,
         "Near Airbnb. Brenda pick. Flexible - any evening during Osaka stay.",
         None),
        (23, "restaurant", "2026-03-24", "Osaka", "GODROCK BURGER (casual option)",
         "530-0015 Osaka, Kita Ward, Nakazakinishi, 1 Chome-8-101", None,
         "Near Airbnb. Casual dining option.",
         None),
    ]
    for seq, lt, dt, city, title, addr, addr_ja, notes, st in legs_0324:
        cur.execute(
            "INSERT INTO trip_itinerary (leg_sequence,leg_type,date_local,city,title,address_en,address_ja,notes_en,start_time) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (seq, lt, dt, city, title, addr, addr_ja, notes, st))
    print(f"BATCH 2 — 3/24 Osaka arrival: {len(legs_0324)} rows")

    # ── BATCH 3: 3/25 Nara ───────────────────────────────────────────
    legs_0325 = [
        (30, "transit",  "2026-03-25", "Nara",  "Osaka to Nara via Kintetsu Nara Line",
         None, None,
         "Tenjinbashisuji-Rokuchome to Osaka Metro to Namba to Kintetsu Nara Line (~40 min). Take city loop bus to Kasuga Taisha. Depart early - arrive before 9am to beat tour buses.",
         None),
        (31, "activity", "2026-03-25", "Nara",  "Kasuga Taisha Shrine",
         "160 Kasuganocho, Nara 630-8212", None,
         "Roughly 3,000 bronze and stone lanterns. Less crowded than Todai-ji. 10 min walk from deer park.",
         None),
        (32, "activity", "2026-03-25", "Nara",  "Nara Park - walk toward Todai-ji",
         "Zoshicho, Nara 630-8212", None,
         "Walk north through deer park toward Todai-ji. Cherry blossom peak late March.",
         None),
        (33, "activity", "2026-03-25", "Nara",  "Todai-ji Temple - Daibutsuden (Great Buddha Hall)",
         "406-1 Zoshicho, Nara", None,
         "Arrive before tour buses. Great Buddha Hall (Daibutsuden).",
         None),
        (34, "activity", "2026-03-25", "Nara",  "Nigatsu-do Hall - city view",
         None, None,
         "Walk up path behind Todai-ji main hall. Elevated city view.",
         None),
        (35, "shopping", "2026-03-25", "Nara",  "Higashimuki Shopping Street",
         "Higashimuki, Nara", None,
         "Covered shopping arcade in Nara city centre.",
         None),
        (36, "activity", "2026-03-25", "Osaka", "Return to Airbnb + Nakazakicho evening stroll",
         None, None,
         "Back to Airbnb. Evening stroll through Nakazakicho vintage neighbourhood near the Airbnb.",
         None),
    ]
    for seq, lt, dt, city, title, addr, addr_ja, notes, st in legs_0325:
        cur.execute(
            "INSERT INTO trip_itinerary (leg_sequence,leg_type,date_local,city,title,address_en,address_ja,notes_en,start_time) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (seq, lt, dt, city, title, addr, addr_ja, notes, st))
    print(f"BATCH 3 — 3/25 Nara: {len(legs_0325)} rows")

    # ── BATCH 4: 3/26 USJ ────────────────────────────────────────────
    legs_0326 = [
        (40, "activity", "2026-03-26", "Osaka", "Universal Studios - Jujutsu Kaisen",
         None, None, "Timed entry per Brenda schedule.", "11:10"),
        (41, "activity", "2026-03-26", "Osaka", "Universal Studios - Hollywood Dream Ride",
         None, None, "Per Brenda schedule.", "13:40"),
        (42, "activity", "2026-03-26", "Osaka", "Universal Studios - Flight of Hippogriff",
         None, None, "Per Brenda schedule.", "16:50"),
    ]
    for seq, lt, dt, city, title, addr, addr_ja, notes, st in legs_0326:
        cur.execute(
            "INSERT INTO trip_itinerary (leg_sequence,leg_type,date_local,city,title,address_en,address_ja,notes_en,start_time) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (seq, lt, dt, city, title, addr, addr_ja, notes, st))
    print(f"BATCH 4 — 3/26 USJ: {len(legs_0326)} rows")

    # ── BATCH 5: 3/27 Osaka ──────────────────────────────────────────
    legs_0327 = [
        (50, "activity",   "2026-03-27", "Osaka", "Umeda Sky Building",
         "1-1-88 Oyodonaka, Kita Ward, Osaka", None, None, None),
        (51, "shopping",   "2026-03-27", "Osaka", "HANKYU SANBAN GAI",
         "1 Chome-1-3 Shibata, Kita Ward, Osaka 530-0012", None,
         "Large shopping complex. Kiddyland inside.", None),
        (52, "shopping",   "2026-03-27", "Osaka", "Meganeichiba Umedachayamachiten - prescription eyewear",
         "NU Chayamachi Plus 1F, 8-11 Chayamachi, Kita Ward, Osaka 530-0013", None,
         "Prescription eyewear. Brenda stop.", None),
        (53, "shopping",   "2026-03-27", "Osaka", "OWNDAYS Hankyu Sanbangai - prescription eyewear",
         "Hankyu Sanbangai Kitakan 1F, 1 Chome-1-3 Shibata, Kita Ward, Osaka 530-0012", None,
         "Prescription frames. Brenda stop.", None),
        (54, "shopping",   "2026-03-27", "Osaka", "JINS Hankyu-Umeda-Sambangai - prescription eyewear",
         "Hankyu Sanbangai Minamikan B1F, 1 Chome-1-3 Shibata, Kita Ward, Osaka 530-0012", None,
         "Prescription frames. Brenda stop.", None),
        (55, "activity",   "2026-03-27", "Osaka", "Kema Sakuranomiya Park - sakura and food stalls",
         "Sakuranomiya, Kita Ward, Osaka", None,
         "Osaka Loop Line 2 stops from Osaka Station to Sakuranomiya. Sakura peak late March. Food stalls along river then off to Osaka Castle.", None),
        (56, "activity",   "2026-03-27", "Osaka", "Osaka Castle + Nishinomaru Garden",
         "Chuo Ward, Osaka", None,
         "Higashi-Umeda to Tanimachi Line 3 stops to Tanimachi 4-chome, then 20 min walk. Nishinomaru Garden for sakura viewing.", None),
        (57, "shopping",   "2026-03-27", "Osaka", "Shinsaibashi-suji Shopping Street",
         "2 Chome-2-22 Shinsaibashisuji, Chuo Ward, Osaka 542-0085", None,
         "Major covered shopping arcade.", None),
        (58, "activity",   "2026-03-27", "Osaka", "Dotonbori + Hozen-ji Temple",
         "Dotonbori, Chuo Ward, Osaka", None,
         "Hozen-ji temple tucked in alley behind Dotonbori. Evening canal atmosphere.", None),
        (59, "restaurant", "2026-03-27", "Osaka", "Saka Ichimonji Mitsuhide - dinner",
         "14-8 Nanbasennichimae, Chuo Ward, Osaka 542-0075", None,
         "Dotonbori area. Brenda dinner pick for 3/27.", None),
    ]
    for seq, lt, dt, city, title, addr, addr_ja, notes, st in legs_0327:
        cur.execute(
            "INSERT INTO trip_itinerary (leg_sequence,leg_type,date_local,city,title,address_en,address_ja,notes_en,start_time) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (seq, lt, dt, city, title, addr, addr_ja, notes, st))
    print(f"BATCH 5 — 3/27 Osaka: {len(legs_0327)} rows")

    # ── BATCH 6: 3/28 Sakai + Osaka ─────────────────────────────────
    legs_0328 = [
        (60, "activity", "2026-03-28", "Sakai", "Sakai Traditional Crafts Museum",
         "1 Chome-1-30 Zaimokuchonishi, Sakai Ward, Sakai, Osaka 590-0941", None,
         "Hands-on craft experience. Traditional Sakai trades.", None),
        (61, "shopping", "2026-03-28", "Sakai", "Baba Hamono - traditional knife forge",
         "3 Chome-3-22 Shukuyachohigashi, Sakai Ward, Sakai, Osaka 590-0936", None,
         "Traditional knife maker and shop. Forge on site.", None),
        (62, "shopping", "2026-03-28", "Sakai", "Knife shop and forge De Sakai",
         "1 Chome-1-5 Yanaginochohigashi, Sakai Ward, Sakai, Osaka 590-0933", None,
         "Working forge and retail shop.", None),
        (63, "shopping", "2026-03-28", "Sakai", "Enami Cutlery Factory",
         "2 Chome-2-25 Kukenchonishi, Sakai Ward, Sakai, Osaka 590-0939", None,
         "Cutlery maker. Factory visit.", None),
        (64, "activity", "2026-03-28", "Osaka", "Nipponbashi Denden Town",
         "Ebisucho Station, Naniwa Ward, Osaka", None,
         "Surugaya Nipponbashi (retro games/anime/manga). SenNichiMae Doguyasuji cookware shopping street nearby.", None),
        (65, "activity", "2026-03-28", "Osaka", "Tsutenkaku Tower",
         "Shinsekai, Naniwa Ward, Osaka", None, None, None),
        (66, "shopping", "2026-03-28", "Osaka", "Tower Knives",
         "Near Tsutenkaku, Shinsekai, Osaka", None,
         "Knife shop near Tsutenkaku.", None),
        (67, "shopping", "2026-03-28", "Osaka", "Orange Street",
         "Minami-Horie, Nishi Ward, Osaka", None,
         "Design, furniture, independent boutiques.", None),
    ]
    for seq, lt, dt, city, title, addr, addr_ja, notes, st in legs_0328:
        cur.execute(
            "INSERT INTO trip_itinerary (leg_sequence,leg_type,date_local,city,title,address_en,address_ja,notes_en,start_time) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (seq, lt, dt, city, title, addr, addr_ja, notes, st))
    print(f"BATCH 6 — 3/28 Sakai+Osaka: {len(legs_0328)} rows")

    # ── BATCH 7: 3/29 Kyoto ──────────────────────────────────────────
    legs_0329 = [
        (70, "transit",  "2026-03-29", "Kyoto", "Osaka to Kyoto to Ginkakuji",
         None, None,
         "90 min to Ginkakuji. Train Osaka to Kyoto Station then Bus #100 or #5 to Ginkakuji-mae. Depart Osaka 8:00 AM.",
         "08:00"),
        (71, "activity", "2026-03-29", "Kyoto", "Ginkakuji (Silver Pavilion)",
         "2 Ginkakujicho, Sakyo-ku, Kyoto", None,
         "Opens 8:30 AM. Arrive early to avoid crowds. Dry sand garden. Tour pavilion before Philosophers Path.",
         "08:30"),
        (72, "activity", "2026-03-29", "Kyoto", "Philosophers Path (Tetsugaku-no-Michi)",
         "Tetsugaku no Michi, Sakyo-ku, Kyoto", None,
         "35-45 min walk south along cherry tree-lined canal. Optional stop: Honen-in (quiet temple off the path).",
         None),
        (73, "activity", "2026-03-29", "Kyoto", "Nanzenji Temple",
         "Nanzenji Fukuchicho, Sakyo-ku, Kyoto", None,
         "Via Eikando Temple. Massive Sanmon gate and Meiji-period brick aqueduct.",
         None),
        (74, "activity", "2026-03-29", "Kyoto", "Heian Shrine",
         "Okazakicho, Sakyo-ku, Kyoto", None,
         "10-15 min walk west from Nanzenji. Massive red torii gate. Stroll through shrine gardens.",
         None),
        (75, "activity", "2026-03-29", "Kyoto", "Maruyama Park + Yasaka Shrine",
         "Maruyama, Higashiyama-ku, Kyoto", None,
         "15 min south toward Gion. Famous weeping cherry tree in Maruyama Park. Walk through park into Yasaka Shrine (center of Gion).",
         None),
        (76, "activity", "2026-03-29", "Kyoto", "Higashiyama Streets - Ninenzaka and Sannenzaka",
         "Higashiyama, Kyoto", None,
         "Traditional pedestrian stone streets with shops and cafes. Very crowded during sakura season - go early or late afternoon.",
         None),
        (77, "activity", "2026-03-29", "Kyoto", "Kiyomizudera Temple",
         "Kiyomizu, Higashiyama-ku, Kyoto", None,
         "10-15 min uphill from Sannenzaka. Iconic wooden stage with sunset views over Kyoto. End the day here.",
         None),
    ]
    for seq, lt, dt, city, title, addr, addr_ja, notes, st in legs_0329:
        cur.execute(
            "INSERT INTO trip_itinerary (leg_sequence,leg_type,date_local,city,title,address_en,address_ja,notes_en,start_time) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (seq, lt, dt, city, title, addr, addr_ja, notes, st))
    print(f"BATCH 7 — 3/29 Kyoto: {len(legs_0329)} rows")

    # ── BATCH 8: 3/30 Kanazawa additions ─────────────────────────────
    legs_0330 = [
        (80, "accommodation", "2026-03-30", "Kanazawa",
         "Inova Hotel - alternative booking (confirm with Brenda)",
         "Kanazawa, Ishikawa", None,
         "Brenda listed Inova Hotel. Existing booking is Hotel Sanraku. Confirm with Brenda which is the confirmed reservation before 3/30.",
         None),
        (81, "activity", "2026-03-30", "Kanazawa", "Omicho Market",
         "50 Kamiomicho, Kanazawa, Ishikawa 920-0905", None,
         "5 min walk from Hotel Sanraku. Fresh seafood, local produce. Afternoon arrival activity.",
         None),
    ]
    for seq, lt, dt, city, title, addr, addr_ja, notes, st in legs_0330:
        cur.execute(
            "INSERT INTO trip_itinerary (leg_sequence,leg_type,date_local,city,title,address_en,address_ja,notes_en,start_time) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (seq, lt, dt, city, title, addr, addr_ja, notes, st))
    print(f"BATCH 8 — 3/30 Kanazawa additions: {len(legs_0330)} rows")

    conn.commit()
    print()
    print("=== trip_itinerary COMMITTED ===")
    cur.execute("SELECT COUNT(*) FROM trip_itinerary")
    print(f"Total rows: {cur.fetchone()[0]}")
    cur.execute("SELECT date_local, city, COUNT(*) FROM trip_itinerary GROUP BY date_local, city ORDER BY date_local, city")
    for r in cur.fetchall():
        print(f"  {r[0]} | {r[1]:<12} | {r[2]} legs")

except Exception as e:
    conn.rollback()
    print(f"ERROR - rolled back: {e}")
    import traceback; traceback.print_exc()
finally:
    cur.close(); conn.close()
