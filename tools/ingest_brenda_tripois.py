#!/usr/bin/env python3
"""BATCH 9 — Insert Brenda trip_pois (33 rows). Standalone re-run after rollback."""
import psycopg2, os

conn = psycopg2.connect(os.environ["DATABASE_URL"])
conn.autocommit = False
cur = conn.cursor()

try:
    pois = [
        # Osaka — restaurants
        ("Osaka", "Hitotsuzuki",                          None, "restaurant",         "1 Chome-6-4 Ukida, Kita Ward, Osaka 530-0021",                                          None, None, None, ["okonomiyaki","brenda_pick","near_airbnb"], None, None, "brenda_trip_plan"),
        ("Osaka", "Umeda Okonomiyaki Izakaya Fuwatoro",   None, "restaurant",         "Kita Ward, Osaka",                                                                      None, None, None, ["okonomiyaki","brenda_pick","near_airbnb"], None, None, "brenda_trip_plan"),
        ("Osaka", "GODROCK BURGER",                       None, "restaurant",         "530-0015 Osaka, Kita Ward, Nakazakinishi, 1 Chome-8-101",                               None, None, None, ["burger","casual","near_airbnb"], None, None, "brenda_trip_plan"),
        ("Osaka", "Saka Ichimonji Mitsuhide",             None, "restaurant",         "14-8 Nanbasennichimae, Chuo Ward, Osaka 542-0075",                                      None, None, None, ["dotonbori","brenda_pick","dinner"], None, None, "brenda_trip_plan"),
        # Osaka — markets + neighbourhoods
        ("Osaka", "Tenma Market",                         None, "market",             "3-1 Ikedacho, Kita Ward, Osaka 530-0033",                                               None, None, None, ["market","local","near_airbnb"], None, "Morning market, local produce and food stalls", "brenda_trip_plan"),
        ("Osaka", "Nakazakicho Area",                     None, "neighborhood",       "Nakazakicho, Kita Ward, Osaka",                                                         None, None, None, ["vintage","indie","near_airbnb"], None, "Walkable from Airbnb. Vintage shops and independent cafes.", "brenda_trip_plan"),
        ("Osaka", "Doguyasuji Cookware Street",           None, "market",             "SenNichiMae, Chuo Ward, Osaka",                                                         None, None, None, ["cookware","professional","chefs"], None, "Professional cookware district near Nipponbashi", "brenda_trip_plan"),
        ("Osaka", "Orange Street",                        None, "neighborhood",       "Minami-Horie, Nishi Ward, Osaka",                                                       None, None, None, ["design","furniture","indie"], None, "Design, furniture, independent boutiques", "brenda_trip_plan"),
        # Osaka — shopping
        ("Osaka", "HANKYU SANBAN GAI",                   None, "shopping_department","1 Chome-1-3 Shibata, Kita Ward, Osaka 530-0012",                                        None, None, None, ["department","kiddyland","shopping"], None, None, "brenda_trip_plan"),
        ("Osaka", "Meganeichiba Umedachayamachiten",      None, "shopping_eyewear",   "NU Chayamachi Plus 1F, 8-11 Chayamachi, Kita Ward, Osaka 530-0013",                    None, None, None, ["eyewear","prescription","brenda"], None, None, "brenda_trip_plan"),
        ("Osaka", "OWNDAYS Hankyu Sanbangai",             None, "shopping_eyewear",   "Hankyu Sanbangai Kitakan 1F, 1 Chome-1-3 Shibata, Kita Ward, Osaka 530-0012",         None, None, None, ["eyewear","prescription","affordable","brenda"], None, None, "brenda_trip_plan"),
        ("Osaka", "JINS Hankyu-Umeda-Sambangai",          None, "shopping_eyewear",   "Hankyu Sanbangai Minamikan B1F, 1 Chome-1-3 Shibata, Kita Ward, Osaka 530-0012",      None, None, None, ["eyewear","prescription","affordable","brenda"], None, None, "brenda_trip_plan"),
        ("Osaka", "Shinsaibashi-suji Shopping Street",    None, "shopping",           "2 Chome-2-22 Shinsaibashisuji, Chuo Ward, Osaka 542-0085",                              None, None, None, ["shopping","covered","arcade"], None, None, "brenda_trip_plan"),
        ("Osaka", "Surugaya Nipponbashi",                 None, "shopping",           "Nipponbashi, Naniwa Ward, Osaka",                                                       None, None, None, ["retro","anime","manga","games","madeline"], None, None, "brenda_trip_plan"),
        ("Osaka", "Tower Knives",                         None, "shopping_crafts",    "Near Tsutenkaku, Shinsekai, Osaka",                                                     None, None, None, ["knives","crafts","shinsekai"], None, None, "brenda_trip_plan"),
        ("Osaka", "Nipponbashi Denden Town",              None, "shopping",           "Ebisucho, Naniwa Ward, Osaka",                                                          None, None, None, ["electronics","anime","manga","denden"], None, None, "brenda_trip_plan"),
        # Osaka — sightseeing + parks
        ("Osaka", "Umeda Sky Building",                   None, "sightseeing",        "1-1-88 Oyodonaka, Kita Ward, Osaka",                                                    None, None, None, ["views","architecture","landmark"], None, None, "brenda_trip_plan"),
        ("Osaka", "Kema Sakuranomiya Park",               None, "park",               "Sakuranomiya, Kita Ward, Osaka",                                                        None, None, None, ["sakura","park","riverside","food_stalls"], "Sakura peak late March. Very busy during cherry blossom season.", "Best late March for sakura", "brenda_trip_plan"),
        ("Osaka", "Osaka Castle + Nishinomaru Garden",    None, "sightseeing",        "1-1 Osakajo, Chuo Ward, Osaka",                                                         None, None, None, ["castle","sakura","history","nishinomaru"], None, "Nishinomaru Garden for sakura viewing", "brenda_trip_plan"),
        ("Osaka", "Hozen-ji Temple",                      None, "temple",             "1-2-16 Nanba, Chuo Ward, Osaka",                                                        None, None, None, ["temple","dotonbori","hidden","nighttime"], None, "Tucked in alley behind Dotonbori. Moss-covered Fudo-Myoo statue.", "brenda_trip_plan"),
        # Sakai — crafts + knife district
        ("Sakai", "Sakai Traditional Crafts Museum",      None, "museum",             "1 Chome-1-30 Zaimokuchonishi, Sakai Ward, Sakai 590-0941",                              None, None, None, ["crafts","museum","hands_on","knives"], None, None, "brenda_trip_plan"),
        ("Sakai", "Baba Hamono",                          None, "shopping_crafts",    "3 Chome-3-22 Shukuyachohigashi, Sakai Ward, Sakai 590-0936",                            None, None, None, ["knives","forge","traditional","sakai"], None, "Traditional knife maker with forge on site", "brenda_trip_plan"),
        ("Sakai", "Knife shop and forge De Sakai",        None, "shopping_crafts",    "1 Chome-1-5 Yanaginochohigashi, Sakai Ward, Sakai 590-0933",                            None, None, None, ["knives","forge","sakai"], None, None, "brenda_trip_plan"),
        ("Sakai", "Enami Cutlery Factory",                None, "shopping_crafts",    "2 Chome-2-25 Kukenchonishi, Sakai Ward, Sakai 590-0939",                                None, None, None, ["knives","cutlery","factory","sakai"], None, None, "brenda_trip_plan"),
        # Nara
        ("Nara",  "Higashimuki Shopping Street",          None, "shopping",           "Higashimuki, Nara",                                                                     None, None, None, ["shopping","covered","nara"], None, None, "brenda_trip_plan"),
        # Kyoto — day trip
        ("Kyoto", "Ginkakuji (Silver Pavilion)",          None, "sightseeing",        "2 Ginkakujicho, Sakyo-ku, Kyoto",                                                       None, None, None, ["silver_pavilion","zen","sand_garden","early"], "Opens 8:30 AM, arrive early to avoid crowds", "Start here at opening. Tour pavilion and dry sand garden.", "brenda_trip_plan"),
        ("Kyoto", "Nanzenji Temple",                      None, "temple",             "Nanzenji Fukuchicho, Sakyo-ku, Kyoto",                                                  None, None, None, ["temple","zen","aqueduct","sanmon"], None, "Massive Sanmon gate and Meiji brick aqueduct. End of Philosophers Path.", "brenda_trip_plan"),
        ("Kyoto", "Heian Shrine",                         None, "shrine",             "Okazakicho, Sakyo-ku, Kyoto",                                                           None, None, None, ["shrine","torii","gardens","okazaki"], None, "Massive red torii gate. Okazaki area.", "brenda_trip_plan"),
        ("Kyoto", "Maruyama Park",                        None, "park",               "Maruyama, Higashiyama-ku, Kyoto",                                                       None, None, None, ["park","sakura","weeping_cherry","gion"], "Famous weeping cherry tree packed in sakura season", "Famous weeping cherry tree. Gateway to Gion.", "brenda_trip_plan"),
        ("Kyoto", "Yasaka Shrine",                        None, "shrine",             "625 Gionmachi Kitagawa, Higashiyama-ku, Kyoto",                                         None, None, None, ["shrine","gion","lanterns","festivals"], None, "Center of Gion. Walk through from Maruyama Park.", "brenda_trip_plan"),
        ("Kyoto", "Higashiyama Streets (Ninenzaka/Sannenzaka)", None, "neighborhood", "Higashiyama, Kyoto",                                                                    None, None, None, ["historic","shopping","traditional","pedestrian"], "Very crowded during sakura and autumn leaf seasons", "Traditional stone pedestrian streets with shops and cafes. Leads up to Kiyomizudera.", "brenda_trip_plan"),
        ("Kyoto", "Kiyomizudera Temple",                  None, "temple",             "Kiyomizu, Higashiyama-ku, Kyoto",                                                       None, None, None, ["temple","wooden_stage","views","sunset"], None, "Iconic wooden stage with panoramic views over Kyoto. Best at sunset.", "brenda_trip_plan"),
        ("Kyoto", "Honen-in Temple",                      None, "temple",             "30 Shishigataninanzenji Yamaboecho, Sakyo-ku, Kyoto",                                   None, None, None, ["temple","quiet","philosophers_path","hidden"], "Quiet, off the main path", "Quiet temple off Philosophers Path. Worth a short detour.", "brenda_trip_plan"),
    ]

    poi_count = 0
    for city, name_en, name_ja, category, addr_en, addr_ja, lat, lng, tags, crowd, best_time, source in pois:
        cur.execute(
            """INSERT INTO trip_pois
               (city, name_en, name_ja, category, address_en, address_ja, lat, lng, tags, crowd_notes, best_time_notes, source)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (city, name_en, name_ja, category, addr_en, addr_ja, lat, lng, tags, crowd, best_time, source))
        poi_count += 1

    conn.commit()
    print(f"BATCH 9 — trip_pois: {poi_count} rows inserted")
    print()

    cur.execute("SELECT city, COUNT(*) FROM trip_pois GROUP BY city ORDER BY city")
    print("trip_pois by city:")
    for r in cur.fetchall():
        print(f"  {r[0]:<15} {r[1]}")

except Exception as e:
    conn.rollback()
    print(f"ERROR - rolled back: {e}")
    import traceback; traceback.print_exc()
finally:
    cur.close(); conn.close()
