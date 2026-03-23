"""
Brenda trip plan — trip_pois + knowledge_items ingestion — 2026-03-20
"""
import psycopg2, os

conn = psycopg2.connect(os.environ['DATABASE_URL'])
conn.autocommit = False
cur = conn.cursor()

try:
    # ── trip_pois ─────────────────────────────────────────────────────
    pois = [
        # Osaka — restaurants
        ("Osaka", "Hitotsuzuki",                          None, "restaurant",      "1 Chome-6-4 Ukida, Kita Ward, Osaka 530-0021",             None, None, None, ["okonomiyaki","brenda_pick","near_airbnb"], None, None, "brenda_trip_plan"),
        ("Osaka", "Umeda Okonomiyaki Izakaya Fuwatoro",   None, "restaurant",      "Kita Ward, Osaka",                                          None, None, None, ["okonomiyaki","brenda_pick","near_airbnb"], None, None, "brenda_trip_plan"),
        ("Osaka", "GODROCK BURGER",                       None, "restaurant",      "530-0015 Osaka, Kita Ward, Nakazakinishi, 1 Chome-8-101",   None, None, None, ["burger","casual","near_airbnb"], None, None, "brenda_trip_plan"),
        ("Osaka", "Saka Ichimonji Mitsuhide",             None, "restaurant",      "14-8 Nanbasennichimae, Chuo Ward, Osaka 542-0075",          None, None, None, ["dotonbori","brenda_pick","dinner"], None, None, "brenda_trip_plan"),
        # Osaka — markets + neighbourhoods
        ("Osaka", "Tenma Market",                         None, "market",          "3-1 Ikedacho, Kita Ward, Osaka 530-0033",                   None, None, None, ["market","local","near_airbnb"], None, "Morning market, local produce and food stalls", "brenda_trip_plan"),
        ("Osaka", "Nakazakicho Area",                     None, "neighborhood",    "Nakazakicho, Kita Ward, Osaka",                             None, None, None, ["vintage","indie","near_airbnb"], None, "Walkable from Airbnb. Vintage shops and independent cafes.", "brenda_trip_plan"),
        ("Osaka", "Doguyasuji Cookware Street",           None, "market",          "SenNichiMae, Chuo Ward, Osaka",                             None, None, None, ["cookware","professional","chefs"], None, "Professional cookware district near Nipponbashi", "brenda_trip_plan"),
        ("Osaka", "Orange Street",                        None, "neighborhood",    "Minami-Horie, Nishi Ward, Osaka",                           None, None, None, ["design","furniture","indie"], None, "Design, furniture, independent boutiques", "brenda_trip_plan"),
        # Osaka — shopping
        ("Osaka", "HANKYU SANBAN GAI",                   None, "shopping_department", "1 Chome-1-3 Shibata, Kita Ward, Osaka 530-0012",        None, None, None, ["department","kiddyland","shopping"], None, None, "brenda_trip_plan"),
        ("Osaka", "Meganeichiba Umedachayamachiten",      None, "shopping_eyewear", "NU Chayamachi Plus 1F, 8-11 Chayamachi, Kita Ward, Osaka 530-0013", None, None, None, ["eyewear","prescription","brenda"], None, None, "brenda_trip_plan"),
        ("Osaka", "OWNDAYS Hankyu Sanbangai",             None, "shopping_eyewear", "Hankyu Sanbangai Kitakan 1F, 1 Chome-1-3 Shibata, Kita Ward, Osaka 530-0012", None, None, None, ["eyewear","prescription","affordable","brenda"], None, None, "brenda_trip_plan"),
        ("Osaka", "JINS Hankyu-Umeda-Sambangai",          None, "shopping_eyewear", "Hankyu Sanbangai Minamikan B1F, 1 Chome-1-3 Shibata, Kita Ward, Osaka 530-0012", None, None, None, ["eyewear","prescription","affordable","brenda"], None, None, "brenda_trip_plan"),
        ("Osaka", "Shinsaibashi-suji Shopping Street",    None, "shopping",        "2 Chome-2-22 Shinsaibashisuji, Chuo Ward, Osaka 542-0085",  None, None, None, ["shopping","covered","arcade"], None, None, "brenda_trip_plan"),
        ("Osaka", "Surugaya Nipponbashi",                 None, "shopping",        "Nipponbashi, Naniwa Ward, Osaka",                           None, None, None, ["retro","anime","manga","games","madeline"], None, None, "brenda_trip_plan"),
        ("Osaka", "Tower Knives",                         None, "shopping_crafts", "Near Tsutenkaku, Shinsekai, Osaka",                         None, None, None, ["knives","crafts","shinsekai"], None, None, "brenda_trip_plan"),
        ("Osaka", "Nipponbashi Denden Town",              None, "shopping",        "Ebisucho, Naniwa Ward, Osaka",                              None, None, None, ["electronics","anime","manga","denden"], None, None, "brenda_trip_plan"),
        # Osaka — sightseeing + parks
        ("Osaka", "Umeda Sky Building",                   None, "sightseeing",     "1-1-88 Oyodonaka, Kita Ward, Osaka",                        None, None, None, ["views","architecture","landmark"], None, None, "brenda_trip_plan"),
        ("Osaka", "Kema Sakuranomiya Park",               None, "park",            "Sakuranomiya, Kita Ward, Osaka",                            None, None, None, ["sakura","park","riverside","food_stalls"], "Sakura peak late March. Very busy during cherry blossom season.", "Best late March for sakura", "brenda_trip_plan"),
        ("Osaka", "Osaka Castle + Nishinomaru Garden",    None, "sightseeing",     "1-1 Osakajo, Chuo Ward, Osaka",                             None, None, None, ["castle","sakura","history","nishinomaru"], None, "Nishinomaru Garden for sakura viewing", "brenda_trip_plan"),
        ("Osaka", "Hozen-ji Temple",                      None, "temple",          "1-2-16 Nanba, Chuo Ward, Osaka",                            None, None, None, ["temple","dotonbori","hidden","nighttime"], None, "Tucked in alley behind Dotonbori. Moss-covered Fudo-Myoo statue.", "brenda_trip_plan"),
        # Sakai — crafts + knife district
        ("Sakai", "Sakai Traditional Crafts Museum",     None, "museum",          "1 Chome-1-30 Zaimokuchonishi, Sakai Ward, Sakai 590-0941",   None, None, None, ["crafts","museum","hands_on","knives"], None, None, "brenda_trip_plan"),
        ("Sakai", "Baba Hamono",                         None, "shopping_crafts", "3 Chome-3-22 Shukuyachohigashi, Sakai Ward, Sakai 590-0936", None, None, None, ["knives","forge","traditional","sakai"], None, "Traditional knife maker with forge on site", "brenda_trip_plan"),
        ("Sakai", "Knife shop and forge De Sakai",       None, "shopping_crafts", "1 Chome-1-5 Yanaginochohigashi, Sakai Ward, Sakai 590-0933", None, None, None, ["knives","forge","sakai"], None, None, "brenda_trip_plan"),
        ("Sakai", "Enami Cutlery Factory",               None, "shopping_crafts", "2 Chome-2-25 Kukenchonishi, Sakai Ward, Sakai 590-0939",     None, None, None, ["knives","cutlery","factory","sakai"], None, None, "brenda_trip_plan"),
        # Nara — new entry (existing 4 stay)
        ("Nara",  "Higashimuki Shopping Street",         None, "shopping",        "Higashimuki, Nara",                                          None, None, None, ["shopping","covered","nara"], None, None, "brenda_trip_plan"),
        # Kyoto — Brenda day trip (Philosophers Path ID 13 already exists - skip)
        ("Kyoto", "Ginkakuji (Silver Pavilion)",         None, "sightseeing",     "2 Ginkakujicho, Sakyo-ku, Kyoto",                           None, None, None, ["silver_pavilion","zen","sand_garden","early"], "Opens 8:30 AM, arrives early to avoid crowds", "Start here at opening. Tour pavilion and dry sand garden.", "brenda_trip_plan"),
        ("Kyoto", "Nanzenji Temple",                     None, "temple",          "Nanzenji Fukuchicho, Sakyo-ku, Kyoto",                       None, None, None, ["temple","zen","aqueduct","sanmon"], None, "Massive Sanmon gate and Meiji brick aqueduct. End of Philosophers Path.", "brenda_trip_plan"),
        ("Kyoto", "Heian Shrine",                        None, "shrine",          "Okazakicho, Sakyo-ku, Kyoto",                               None, None, None, ["shrine","torii","gardens","okazaki"], None, "Massive red torii gate. Okazaki area.", "brenda_trip_plan"),
        ("Kyoto", "Maruyama Park",                       None, "park",            "Maruyama, Higashiyama-ku, Kyoto",                           None, None, None, ["park","sakura","weeping_cherry","gion"], "Famous weeping cherry tree packed in sakura season", "Famous weeping cherry tree. Gateway to Gion.", "brenda_trip_plan"),
        ("Kyoto", "Yasaka Shrine",                       None, "shrine",          "625 Gionmachi Kitagawa, Higashiyama-ku, Kyoto",              None, None, None, ["shrine","gion","lanterns","festivals"], None, "Center of Gion. Walk through from Maruyama Park.", "brenda_trip_plan"),
        ("Kyoto", "Higashiyama Streets (Ninenzaka/Sannenzaka)", None, "neighborhood", "Higashiyama, Kyoto",                                    None, None, None, ["historic","shopping","traditional","pedestrian"], "Very crowded during sakura and autumn leaf seasons", "Traditional stone pedestrian streets with shops and cafes. Leads up to Kiyomizudera.", "brenda_trip_plan"),
        ("Kyoto", "Kiyomizudera Temple",                 None, "temple",          "Kiyomizu, Higashiyama-ku, Kyoto",                           None, None, None, ["temple","wooden_stage","views","sunset"], None, "Iconic wooden stage with panoramic views over Kyoto. Best at sunset.", "brenda_trip_plan"),
        ("Kyoto", "Honen-in Temple",                     None, "temple",          "30 Shishigataninanzenji Yamaboecho, Sakyo-ku, Kyoto",        None, None, None, ["temple","quiet","philosophers_path","hidden"], "Quiet, off the main path", "Quiet temple off Philosophers Path. Worth a short detour.", "brenda_trip_plan"),
    ]

    poi_count = 0
    for city, name_en, name_ja, category, addr_en, addr_ja, lat, lng, tags, crowd, best_time, source in pois:
        cur.execute(
            """INSERT INTO trip_pois
               (city, name_en, name_ja, category, address_en, address_ja, lat, lng, tags, crowd_notes, best_time_notes, source)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (city, name_en, name_ja, category, addr_en, addr_ja, lat, lng, tags, crowd, best_time, source))
        poi_count += 1
    print(f"BATCH 9 — trip_pois: {poi_count} rows inserted")

    # ── knowledge_items ───────────────────────────────────────────────
    items = [
        # Osaka dining
        ("Osaka", "restaurant", "Hitotsuzuki - okonomiyaki near Airbnb",
         None, "Okonomiyaki restaurant at 1 Chome-6-4 Ukida, Kita Ward. Near the Airbnb. Brenda pick for dinner during Osaka stay.", None),
        ("Osaka", "restaurant", "Umeda Okonomiyaki Izakaya Fuwatoro - near Airbnb",
         None, "Okonomiyaki izakaya near Airbnb in Kita Ward. Brenda pick for dinner during Osaka stay.", None),
        ("Osaka", "restaurant", "GODROCK BURGER - casual option near Airbnb",
         None, "Burger restaurant at 530-0015 Osaka, Kita Ward, Nakazakinishi, 1 Chome-8-101. Casual dining option near Airbnb.", None),
        ("Osaka", "restaurant", "Saka Ichimonji Mitsuhide - Dotonbori dinner",
         None, "Restaurant at 14-8 Nanbasennichimae, Chuo Ward, Osaka 542-0075. Dotonbori area. Brenda dinner pick for 3/27 evening.", None),
        # Osaka markets + neighbourhoods
        ("Osaka", "market", "Tenma Market - local food market near Airbnb",
         None, "Local market at 3-1 Ikedacho, Kita Ward, Osaka 530-0033. Near the Airbnb. Morning market with local produce and food stalls.", None),
        ("Osaka", "neighborhood", "Nakazakicho - vintage neighbourhood near Airbnb",
         None, "Nakazakicho, Kita Ward. Walkable from Airbnb. Vintage clothing, indie cafes, small galleries. Good for an evening stroll after Nara day trip.", None),
        ("Osaka", "market", "Doguyasuji Cookware Street (SenNichiMae) - professional cookware",
         None, "SenNichiMae Doguyasuji Shotengai, Chuo Ward. Professional cookware district near Nipponbashi. Kitchen tools, pottery, restaurant supplies.", None),
        ("Osaka", "neighborhood", "Orange Street - design and indie boutiques",
         None, "Minami-Horie, Nishi Ward. Design shops, furniture, independent boutiques. Different vibe from Shinsaibashi - more local and curated.", None),
        # Osaka shopping
        ("Osaka", "shopping", "HANKYU SANBAN GAI - department shopping with Kiddyland",
         None, "Large shopping complex at 1 Chome-1-3 Shibata, Kita Ward, Osaka 530-0012. Multiple floors, Kiddyland toy store inside. Connected to Hankyu Umeda Station.", None),
        ("Osaka", "eyewear", "Meganeichiba Umedachayamachiten - prescription eyewear",
         None, "Eyewear shop at NU Chayamachi Plus 1F, 8-11 Chayamachi, Kita Ward, Osaka 530-0013. Prescription eyewear. Brenda stop on 3/27.", None),
        ("Osaka", "eyewear", "OWNDAYS Hankyu Sanbangai - affordable prescription frames",
         None, "Eyewear at Hankyu Sanbangai Kitakan 1F, 1 Chome-1-3 Shibata, Kita Ward, Osaka 530-0012. Affordable prescription frames. Brenda stop on 3/27.", None),
        ("Osaka", "eyewear", "JINS Hankyu-Umeda-Sambangai - prescription frames",
         None, "Eyewear at Hankyu Sanbangai Minamikan B1F, 1 Chome-1-3 Shibata, Kita Ward, Osaka 530-0012. Affordable prescription frames. Brenda stop on 3/27.", None),
        ("Osaka", "shopping", "Surugaya Nipponbashi - retro games, anime, manga",
         None, "Surugaya store in Nipponbashi Denden Town. Retro games, anime merchandise, manga. Good for Madeline.", None),
        ("Osaka", "shopping_crafts", "Tower Knives - knife shop near Tsutenkaku",
         None, "Knife shop near Tsutenkaku Tower in Shinsekai. Quality Japanese knives and cutlery for purchase.", None),
        # Sakai knife district
        ("Sakai", "shopping_crafts", "Sakai Traditional Crafts Museum - hands-on knife experience",
         None, "Museum at 1 Chome-1-30 Zaimokuchonishi, Sakai Ward, Sakai 590-0941. Hands-on craft experience. Sakai is famous for professional kitchen knives used by chefs worldwide.", None),
        ("Sakai", "shopping_crafts", "Baba Hamono - traditional knife forge and shop",
         None, "3 Chome-3-22 Shukuyachohigashi, Sakai Ward, Sakai 590-0936. Traditional knife maker with forge on site. Watch the forging process and purchase directly.", None),
        ("Sakai", "shopping_crafts", "Knife shop and forge De Sakai",
         None, "1 Chome-1-5 Yanaginochohigashi, Sakai Ward, Sakai 590-0933. Working forge and retail shop. Handmade professional knives.", None),
        ("Sakai", "shopping_crafts", "Enami Cutlery Factory",
         None, "2 Chome-2-25 Kukenchonishi, Sakai Ward, Sakai 590-0939. Cutlery manufacturer. Factory visit possible.", None),
        # Kyoto day trip
        ("Kyoto", "sightseeing", "Ginkakuji (Silver Pavilion) - Kyoto day trip start",
         None, "2 Ginkakujicho, Sakyo-ku, Kyoto. Opens 8:30 AM. Start here early to avoid crowds. Zen dry sand garden. Beginning of the Philosophers Path walk.", None),
        ("Kyoto", "sightseeing", "Philosophers Path (Tetsugaku-no-Michi) - cherry canal walk",
         None, "Tetsugaku no Michi, Sakyo-ku, Kyoto. 35-45 min walk south along cherry tree-lined canal from Ginkakuji to Nanzenji. Optional stop: Honen-in temple (quiet, off path). Very popular during sakura season.", None),
        ("Kyoto", "temple", "Nanzenji Temple - Sanmon gate and Meiji aqueduct",
         None, "Nanzenji Fukuchicho, Sakyo-ku, Kyoto. Large Zen temple complex at end of Philosophers Path. Massive Sanmon gate and unusual Meiji-period brick aqueduct. Less crowded than Kinkakuji.", None),
        ("Kyoto", "shrine", "Heian Shrine - massive red torii gate",
         None, "Okazakicho, Sakyo-ku, Kyoto. 10-15 min walk west from Nanzenji. One of the largest torii gates in Japan. Stroll through shrine gardens.", None),
        ("Kyoto", "park", "Maruyama Park - weeping cherry tree and Gion gateway",
         None, "Maruyama, Higashiyama-ku, Kyoto. Famous weeping cherry tree, packed during sakura season. Walk through park directly into Yasaka Shrine and the Gion district.", None),
        ("Kyoto", "shrine", "Yasaka Shrine - center of Gion district",
         None, "625 Gionmachi Kitagawa, Higashiyama-ku, Kyoto. Center of the Gion district. Main shrine of Gion Matsuri festival. Free entry.", None),
        ("Kyoto", "neighborhood", "Higashiyama Streets - Ninenzaka and Sannenzaka",
         None, "Traditional stone pedestrian streets in Higashiyama, Kyoto. Lined with shops and cafes in historic machiya buildings. Ninenzaka and Sannenzaka lead uphill to Kiyomizudera. Very crowded during sakura and autumn - go early or late afternoon.", None),
        ("Kyoto", "temple", "Kiyomizudera Temple - sunset views over Kyoto",
         None, "Kiyomizu, Higashiyama-ku, Kyoto. Famous for its large wooden stage extending from the main hall. Panoramic views over Kyoto city. 10-15 min uphill walk from Sannenzaka. Best at sunset.", None),
    ]

    ki_count = 0
    for city, category, topic, source_url, content_summary, raw_content in items:
        cur.execute(
            """INSERT INTO knowledge_items (city, category, topic, source_url, content_summary, raw_content)
               VALUES (%s,%s,%s,%s,%s,%s)""",
            (city, category, topic, source_url, content_summary, raw_content))
        ki_count += 1
    print(f"BATCH 10 — knowledge_items: {ki_count} rows inserted")

    conn.commit()
    print()
    print("=== trip_pois + knowledge_items COMMITTED ===")
    cur.execute("SELECT city, COUNT(*) FROM trip_pois GROUP BY city ORDER BY city")
    print("trip_pois by city:")
    for r in cur.fetchall(): print(f"  {r[0]:<12} {r[1]}")
    cur.execute("SELECT city, COUNT(*) FROM knowledge_items GROUP BY city ORDER BY city")
    print("knowledge_items by city:")
    for r in cur.fetchall(): print(f"  {r[0] or 'NULL':<12} {r[1]}")

except Exception as e:
    conn.rollback()
    print(f"ERROR - rolled back: {e}")
    import traceback; traceback.print_exc()
finally:
    cur.close(); conn.close()
