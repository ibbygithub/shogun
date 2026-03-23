#!/usr/bin/env python3
"""BATCH 10 — Insert Brenda trip knowledge_items (27 rows)."""
import psycopg2, os

conn = psycopg2.connect(os.environ["DATABASE_URL"])
cur = conn.cursor()

try:
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
        # Nara
        ("Nara", "sightseeing", "Higashimuki Shopping Street - covered arcade near deer park",
         None, "Higashimukicho, Nara. Covered shopping arcade close to Nara Park. Mix of souvenir shops, local snacks, and cafes. Good for shopping after Todai-ji.", None),
    ]

    ki_count = 0
    for city, category, topic, source_url, content_summary, raw_content in items:
        cur.execute(
            """INSERT INTO knowledge_items (city, category, topic, source_url, content_summary, raw_content)
               VALUES (%s,%s,%s,%s,%s,%s)""",
            (city, category, topic, source_url, content_summary, raw_content))
        ki_count += 1

    conn.commit()
    print(f"BATCH 10 — knowledge_items: {ki_count} rows inserted")
    print()

    cur.execute("SELECT city, COUNT(*) FROM knowledge_items GROUP BY city ORDER BY city")
    print("knowledge_items by city:")
    for r in cur.fetchall():
        print(f"  {(r[0] or 'NULL'):<12} {r[1]}")

    cur.execute("SELECT city, COUNT(*) FROM trip_pois GROUP BY city ORDER BY city")
    print("\ntrip_pois by city:")
    for r in cur.fetchall():
        print(f"  {r[0]:<12} {r[1]}")

except Exception as e:
    conn.rollback()
    print(f"ERROR - rolled back: {e}")
    import traceback; traceback.print_exc()
finally:
    cur.close(); conn.close()
