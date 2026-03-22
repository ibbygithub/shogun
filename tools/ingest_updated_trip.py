#!/usr/bin/env python3
"""
ingest_updated_trip.py — Seed trip_pois + knowledge_items from updated-trip.md

New content vs brenda-trip-plan.md:
  - Cosme Osaka (new on 3/27)
  - Kanazawa (3/30-3/31): 9 places
  - Tokyo (4/1-4/8): 38 itinerary-specific trip_pois
    (Tokyo knowledge_items already seeded via seed_tokyo_knowledge.py)

Usage (on brainnode-01):
    DATABASE_URL=postgresql://... python tools/ingest_updated_trip.py
"""
import os
import psycopg2

conn = psycopg2.connect(os.environ["DATABASE_URL"])
conn.autocommit = False
cur = conn.cursor()

try:
    # ── trip_pois ──────────────────────────────────────────────────────────────
    # Schema: city, name_en, name_ja, category, address_en, address_ja,
    #         lat, lng, tags, crowd_notes, best_time_notes, source
    pois = [

        # ── OSAKA addition ─────────────────────────────────────────────────────
        ("Osaka", "@Cosme Osaka Lucua Isle", None, "skincare",
         "Lucua Isle 3F, 3 Chome-1-3 Umeda, Kita Ward, Osaka 530-8558",
         None, None, None,
         ["skincare", "cosme", "beauty", "umeda", "brenda"],
         None, "3F of Lucua Isle connected to Osaka Station", "updated_trip_plan"),

        # ── KANAZAWA ───────────────────────────────────────────────────────────
        ("Kanazawa", "Omicho Market", None, "market",
         "50 Kamiomicho, Kanazawa, Ishikawa 920-0905",
         None, None, None,
         ["market", "fish", "seafood", "local", "lunch"],
         "Busy during lunch hours", "Best for lunch — fresh seafood and sushi stalls", "updated_trip_plan"),

        ("Kanazawa", "Kazuemachi Chaya District", None, "neighborhood",
         "Kazuemachi, Kanazawa, Ishikawa",
         None, None, None,
         ["chaya", "teahouse", "geisha", "traditional", "evening"],
         None, "Smaller and quieter than Higashi Chaya. Best in the evening.", "updated_trip_plan"),

        ("Kanazawa", "Higashi Chaya District", None, "neighborhood",
         "Higashiyama 1-chome, Kanazawa, Ishikawa",
         None, None, None,
         ["chaya", "teahouse", "gold_leaf", "historic", "touristy"],
         "Crowded midday; calmer in morning",
         "Most famous chaya district. Gold leaf shops, tea houses, ochaya. Go in the morning.",
         "updated_trip_plan"),

        ("Kanazawa", "Kanazawa Castle Park", None, "sightseeing",
         "1-1 Marunouchi, Kanazawa, Ishikawa",
         None, None, None,
         ["castle", "park", "history", "ishikawa"],
         None, "Ishikawa Gate is the landmark entrance. Combine with Kenrokuen next door.", "updated_trip_plan"),

        ("Kanazawa", "Kenrokuen Garden", None, "park",
         "1 Kenrokucho, Kanazawa, Ishikawa",
         None, None, None,
         ["garden", "three_great_gardens", "seasonal", "sakura", "snow"],
         "Popular during sakura and autumn",
         "One of Japan's three great gardens. Adjacent to Kanazawa Castle. Beautiful in late March.",
         "updated_trip_plan"),

        ("Kanazawa", "D.T. Suzuki Museum", None, "museum",
         "3-4-20 Honda-machi, Kanazawa, Ishikawa",
         None, None, None,
         ["zen", "suzuki", "philosophy", "architecture", "reflective"],
         None, "Museum dedicated to Zen philosopher D.T. Suzuki. Minimalist architecture. Exit south from Kenrokuen.", "updated_trip_plan"),

        ("Kanazawa", "Oyama Shrine", None, "shrine",
         "1-1 Oyamamachi, Kanazawa, Ishikawa",
         None, None, None,
         ["shrine", "stained_glass", "unusual", "dutch_gate"],
         None, "Unusual shrine with Dutch-style stained glass gate (Dutch Gate). Central location.", "updated_trip_plan"),

        ("Kanazawa", "Nagamachi Samurai District", None, "neighborhood",
         "Nagamachi, Kanazawa, Ishikawa",
         None, None, None,
         ["samurai", "historic", "earthen_walls", "traditional", "preserved"],
         None, "Preserved samurai residential neighborhood with earthen walls and narrow lanes.", "updated_trip_plan"),

        ("Kanazawa", "Myoryuji (Ninja Temple)", None, "temple",
         "1-2-12 Nomachi, Kanazawa, Ishikawa",
         None, None, None,
         ["ninja", "hidden_rooms", "reservation_required", "trap_doors"],
         "Advance reservation required — cannot enter without booking",
         "Guided tour only. Book in advance. 29 staircases, 23 rooms, hidden passages.", "updated_trip_plan"),

        # ── TOKYO (4/1 — Sugamo) ───────────────────────────────────────────────
        ("Tokyo", "Sugamo Jizo-dori Shopping Street", None, "shopping",
         "4-35-1 Sugamo, Toshima City, Tokyo",
         None, None, None,
         ["jizo", "local", "old_tokyo", "near_airbnb", "snacks"],
         None, "Walkable from Airbnb. Local shopping street known as 'Grandma's Harajuku'. Traditional snacks and clothing.", "updated_trip_plan"),

        # ── TOKYO (4/2 — Ikebukuro / Sunshine City) ───────────────────────────
        ("Tokyo", "Sunshine City", None, "shopping",
         "3-1-3 Higashi-Ikebukuro, Toshima City, Tokyo",
         None, None, None,
         ["mall", "ikebukuro", "character", "multiple_floors"],
         "Crowded on weekends",
         "Large mall complex in Ikebukuro. Houses Pokemon Center Mega Tokyo, Kiddyland, and Chiikawa Land.",
         "updated_trip_plan"),

        ("Tokyo", "Pokemon Center Mega Tokyo", None, "shopping",
         "Sunshine City Alpa 2F, 3-1-2 Higashi-Ikebukuro, Toshima City, Tokyo",
         None, None, None,
         ["pokemon", "mega", "sunshine_city", "ikebukuro", "madeline"],
         "Can get very busy. Go early.",
         "Largest Pokemon Center in Japan. 2F of Sunshine City Alpa, Ikebukuro.", "updated_trip_plan"),

        ("Tokyo", "Chiikawa Land Ikebukuro", None, "shopping",
         "Sunshine City, 3-1-3 Higashi-Ikebukuro, Toshima City, Tokyo",
         None, None, None,
         ["chiikawa", "character", "sunshine_city", "madeline"],
         "May have queue; limited stock",
         "Chiikawa character goods store in Sunshine City, Ikebukuro.", "updated_trip_plan"),

        # ── TOKYO (4/3 — Kichijoji / Mitaka) ──────────────────────────────────
        ("Tokyo", "Ghibli Museum Mitaka", None, "museum",
         "1-1-83 Shimorenjaku, Mitaka, Tokyo 181-0013",
         None, None, None,
         ["ghibli", "miyazaki", "advance_ticket", "mitaka", "lottery"],
         "Advance lottery ticket required — cannot walk in",
         "Lottery tickets only, book months ahead. Bus from Kichijoji Station or 15 min walk.", "updated_trip_plan"),

        ("Tokyo", "Inokashira Park", None, "park",
         "1-18 Gotenyama, Musashino, Tokyo",
         None, None, None,
         ["park", "sakura", "swans", "kichijoji", "boating"],
         "Very crowded during sakura season",
         "Beautiful park next to Kichijoji Station. Sakura in late March/April. Swan boats on the pond.", "updated_trip_plan"),

        ("Tokyo", "Shirohige's Cream Puff Factory", None, "restaurant",
         "2 Chome-7-5 Kichijoji Minamicho, Musashino, Tokyo 180-0003",
         None, None, None,
         ["cream_puff", "totoro", "character", "kichijoji", "brenda"],
         "Sells out — go early",
         "Totoro-shaped cream puffs. Unofficial Ghibli association. Near Kichijoji Station.", "updated_trip_plan"),

        ("Tokyo", "Lumiere Café Kichijoji", None, "restaurant",
         "Kichijoji, Musashino, Tokyo",
         None, None, None,
         ["cafe", "kichijoji", "brenda_pick"],
         None, "Café in Kichijoji area. Brenda pick for 4/3.", "updated_trip_plan"),

        # ── TOKYO (4/4 — Ueno / Akihabara) ────────────────────────────────────
        ("Tokyo", "Tokyo National Museum", None, "museum",
         "13-9 Uenokoen, Taito City, Tokyo",
         None, None, None,
         ["museum", "national", "artifacts", "ueno", "history"],
         None, "Japan's largest museum. Ancient artifacts, samurai armor, ceramics. Allow 2-3 hours.", "updated_trip_plan"),

        ("Tokyo", "Ueno Park", None, "park",
         "Uenokoen, Taito City, Tokyo",
         None, None, None,
         ["park", "sakura", "ueno", "hanami", "zoo"],
         "Packed during sakura season — one of Tokyo's most popular hanami spots",
         "Major sakura spot in Tokyo. Museums, zoo, Bentendo temple island, food stalls in season.", "updated_trip_plan"),

        ("Tokyo", "Yamashiroya Ueno", None, "shopping",
         "4-9-8 Ueno, Taito City, Tokyo",
         None, None, None,
         ["toys", "figures", "anime", "ueno", "madeline"],
         None, "Multi-floor toy and figure store near Ueno Station. Good for anime figures, gashapons, character goods.", "updated_trip_plan"),

        ("Tokyo", "Ameyoko Market", None, "market",
         "4-7-8 Ueno, Taito City, Tokyo",
         None, None, None,
         ["market", "street_food", "discount", "shopping", "ueno"],
         "Busy but that's part of the charm",
         "Bustling open-air market between Ueno and Okachimachi stations. Street food, discount goods, dried seafood.", "updated_trip_plan"),

        ("Tokyo", "Akihabara Electric Town", None, "shopping",
         "Soto-Kanda, Chiyoda City, Tokyo",
         None, None, None,
         ["electronics", "anime", "manga", "otaku", "radio_kaikan", "madeline"],
         None, "Tokyo's electronics and anime district. Radio Kaikan building for figures/models. Chuo Dori is the main street.", "updated_trip_plan"),

        # ── TOKYO (4/5 — Asakusa) ──────────────────────────────────────────────
        ("Tokyo", "Senso-ji Temple", None, "temple",
         "2-3-1 Asakusa, Taito City, Tokyo",
         None, None, None,
         ["temple", "lantern", "oldest", "asakusa", "iconic"],
         "Very crowded from 9am — arrive before 8am",
         "Tokyo's oldest temple. Giant red lantern at Kaminarimon gate. Go early morning to avoid crowds.", "updated_trip_plan"),

        ("Tokyo", "Nakamise Shopping Street", None, "shopping",
         "1-36-3 Asakusa, Taito City, Tokyo",
         None, None, None,
         ["shopping", "souvenirs", "traditional", "senso_ji", "snacks"],
         None, "Traditional shopping arcade leading to Senso-ji. Souvenirs, ningyo-yaki, traditional snacks.", "updated_trip_plan"),

        ("Tokyo", "Sumida Park", None, "park",
         "Hanakawado, Taito City, Tokyo",
         None, None, None,
         ["park", "sakura", "sumida_river", "asakusa"],
         "Popular sakura spot in late March/April",
         "Along Sumida River near Asakusa. One of Tokyo's top sakura spots. SkyTree views.", "updated_trip_plan"),

        ("Tokyo", "Washoku Gyuuna yadoki Asakusa", None, "restaurant",
         "Asakusa, Taito City, Tokyo",
         None, None, None,
         ["reservation", "beef", "wagyu", "dinner", "asakusa"],
         None, "Reservation 4/5 at 5:30 PM, party of 3. Washoku beef restaurant in Asakusa.", "updated_trip_plan"),

        # ── TOKYO (4/6 — Shinjuku) ─────────────────────────────────────────────
        ("Tokyo", "Samurai Restaurant Shinjuku", None, "restaurant",
         "1 Chome-7-7 Kabukicho, Shinjuku City, Tokyo 160-0021",
         None, None, None,
         ["samurai", "show", "dinner", "reservation", "kabukicho"],
         None, "Dinner show with samurai performance. B1 of Taro's Bldg, Kabukicho. 4/6 10:30 AM show. ~30 min from Airbnb.", "updated_trip_plan"),

        ("Tokyo", "Godzilla Head Shinjuku", None, "sightseeing",
         "1 Chome-19-1 Kabukicho, Shinjuku City, Tokyo",
         None, None, None,
         ["godzilla", "rooftop", "kabukicho", "landmark", "free"],
         None, "Giant Godzilla head on the Hotel Gracery rooftop. Kabukicho Toho Cinema building. Free to view from street.", "updated_trip_plan"),

        ("Tokyo", "Omoide Yokocho (Memory Lane)", None, "neighborhood",
         "1 Chome-2 Nishishinjuku, Shinjuku City, Tokyo 160-0023",
         None, None, None,
         ["yakitori", "memory_lane", "shinjuku", "alley", "old_tokyo"],
         "Gets crowded; seats limited in tiny stalls",
         "Narrow alley of tiny yakitori and izakaya stalls next to Shinjuku Station west exit. Atmospheric, old Tokyo feel.", "updated_trip_plan"),

        ("Tokyo", "Hanazono Shrine", None, "shrine",
         "5-17-3 Shinjuku, Shinjuku City, Tokyo",
         None, None, None,
         ["shrine", "shinjuku", "lanterns", "flea_market"],
         None, "Shinto shrine in Kabukicho. Antique flea market on Sundays. Lit up beautifully at night.", "updated_trip_plan"),

        ("Tokyo", "Shinjuku Gyoen National Garden", None, "park",
         "11 Naito-machi, Shinjuku City, Tokyo",
         None, None, None,
         ["garden", "sakura", "national", "peaceful", "no_alcohol"],
         "Very popular during sakura — arrive early",
         "One of Tokyo's best sakura spots. Mix of Japanese, French, and English garden styles. No alcohol allowed.", "updated_trip_plan"),

        ("Tokyo", "Tokyo Metropolitan Government Building", None, "sightseeing",
         "2 Chome-8-1 Nishishinjuku, Shinjuku City, Tokyo 163-8001",
         None, None, None,
         ["free", "views", "observatory", "night", "shinjuku"],
         None, "Free observation deck on Building 1 North Tower. Night light show starts 6 PM. One of best free views in Tokyo.", "updated_trip_plan"),

        ("Tokyo", "Don Quijote Shinjuku", None, "shopping",
         "Kabukicho, Shinjuku City, Tokyo",
         None, None, None,
         ["don_quijote", "souvenirs", "24hr", "shinjuku", "snacks"],
         None, "Multi-floor discount store open 24hrs. Good for souvenirs, snacks, cosmetics, character goods.", "updated_trip_plan"),

        # ── TOKYO (4/7 — Harajuku / Shibuya) ──────────────────────────────────
        ("Tokyo", "Chiikawa Bakery Tokyo", None, "shopping",
         "Tokyo",
         None, None, None,
         ["chiikawa", "character_bakery", "timed_entry", "madeline"],
         "Timed entry may be required; sells out",
         "Chiikawa-themed bakery. 4/7 visit at 11:15 AM. 40-60 min travel from Airbnb.", "updated_trip_plan"),

        ("Tokyo", "Shibuya Crossing", None, "sightseeing",
         "Dogenzaka, Shibuya City, Tokyo",
         None, None, None,
         ["crossing", "scramble", "busiest", "landmark", "iconic"],
         "Most dramatic during rush hour or evening",
         "World's busiest pedestrian scramble crossing. View from Starbucks second floor or Mag's Park.", "updated_trip_plan"),

        ("Tokyo", "Parco Shibuya", None, "shopping",
         "15-1 Udagawacho, Shibuya City, Tokyo",
         None, None, None,
         ["shibuya", "anime", "character", "contemporary", "floor6"],
         None, "Floor 6 has Nintendo Tokyo, Pokemon Center, and character shops. Art and culture focus.", "updated_trip_plan"),

        ("Tokyo", "Shibuya 109", None, "shopping",
         "2-29-1 Dogenzaka, Shibuya City, Tokyo",
         None, None, None,
         ["fashion", "youth", "trends", "shibuya", "109"],
         None, "Iconic cylindrical fashion building in Shibuya. Youth and trendy brands.", "updated_trip_plan"),

        ("Tokyo", "Loft Shibuya", None, "shopping",
         "21-1 Udagawacho, Shibuya City, Tokyo",
         None, None, None,
         ["stationery", "design", "loft", "shibuya", "gifts"],
         None, "Multi-floor lifestyle and stationery store. Great for design gifts, travel goods, Japanese stationery.", "updated_trip_plan"),

        ("Tokyo", "Kiddyland Omotesando", None, "shopping",
         "6-1-9 Jingumae, Shibuya City, Tokyo",
         None, None, None,
         ["toys", "character", "kiddyland", "omotesando", "madeline"],
         None, "Flagship Kiddyland on Omotesando. Multiple floors of character goods, toys, Sanrio, Disney, etc.", "updated_trip_plan"),

        ("Tokyo", "Meiji Jingu Shrine", None, "shrine",
         "1-1 Yoyogikamizonocho, Shibuya City, Tokyo",
         None, None, None,
         ["shrine", "forest", "peaceful", "harajuku", "serene"],
         None, "Large forested Shinto shrine dedicated to Emperor Meiji. 5-minute walk from Harajuku Station. Free entry.", "updated_trip_plan"),

        ("Tokyo", "Yoyogi Park", None, "park",
         "Yoyogikamizonocho, Shibuya City, Tokyo",
         None, None, None,
         ["park", "hanami", "picnic", "harajuku", "open"],
         "Popular hanami spot in sakura season",
         "Large open park adjacent to Meiji Jingu. Great for hanami picnics. Next to Harajuku Station.", "updated_trip_plan"),

        ("Tokyo", "Takeshita Street", None, "neighborhood",
         "1-17-5 Jingumae, Shibuya City, Tokyo",
         None, None, None,
         ["harajuku", "youth", "fashion", "crepes", "kawaii"],
         "Extremely crowded afternoon and weekends",
         "Start at top near Harajuku Station at ~10am when shops open. Go down to cross street, explore back streets, then to Cat Street.", "updated_trip_plan"),

        ("Tokyo", "Cat Street (Ura-Harajuku)", None, "neighborhood",
         "Jingumae, Shibuya City, Tokyo",
         None, None, None,
         ["indie", "boutiques", "backstreets", "harajuku", "omotesando"],
         None, "Pedestrian street linking Harajuku backstreets to Omotesando. Independent boutiques, cafes, streetwear.", "updated_trip_plan"),

        ("Tokyo", "Omotesando", None, "neighborhood",
         "Jingumae, Shibuya City, Tokyo",
         None, None, None,
         ["luxury", "fashion", "architecture", "zelkova", "boulevard"],
         None, "Tree-lined boulevard with flagship luxury stores and interesting architecture. Leads from Harajuku to Aoyama.", "updated_trip_plan"),

        ("Tokyo", "@Cosme Tokyo Harajuku", None, "skincare",
         "1 Chome-14-27 Jingumae, Shibuya, Tokyo 150-0001",
         None, None, None,
         ["skincare", "cosme", "harajuku", "beauty", "brenda"],
         None, "Japan's largest @Cosme beauty store in Harajuku. Curated selection of top-rated Japanese skincare and makeup.", "updated_trip_plan"),

        ("Tokyo", "Mega Don Quijote Shibuya", None, "shopping",
         "28-6 Udagawacho, Shibuya City, Tokyo",
         None, None, None,
         ["don_quijote", "mega", "souvenirs", "shibuya", "24hr"],
         None, "Mega-sized Don Quijote in Shibuya. Open late. Souvenirs, snacks, electronics, costumes.", "updated_trip_plan"),

        # ── TOKYO (4/8 — Ginza) ────────────────────────────────────────────────
        ("Tokyo", "Uniqlo Ginza Flagship", None, "shopping",
         "6-9-5 Ginza, Chuo City, Tokyo",
         None, None, None,
         ["uniqlo", "flagship", "ginza", "all_floors", "utme"],
         None, "Uniqlo's 12-floor global flagship store in Ginza. Includes UTme! customization studio. Ginza-exclusive items.", "updated_trip_plan"),
    ]

    poi_count = 0
    for city, name_en, name_ja, category, addr_en, addr_ja, lat, lng, tags, crowd, best_time, source in pois:
        cur.execute(
            """INSERT INTO trip_pois
               (city, name_en, name_ja, category, address_en, address_ja,
                lat, lng, tags, crowd_notes, best_time_notes, source)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (city, name_en, name_ja, category, addr_en, addr_ja,
             lat, lng, tags, crowd, best_time, source))
        poi_count += 1
    print(f"trip_pois: {poi_count} rows inserted")


    # ── knowledge_items ────────────────────────────────────────────────────────
    # Schema: city, category, topic, source_url, content_summary, raw_content
    items = [

        # ── OSAKA addition ─────────────────────────────────────────────────────
        ("Osaka", "skincare",
         "@Cosme Osaka Lucua Isle - beauty and skincare store Umeda",
         None, "Japan's largest @Cosme beauty store in Lucua Isle 3F, connected to Osaka Station. Curated selection of top-rated Japanese skincare and makeup. Brenda stop on 3/27.", None),

        # ── KANAZAWA ───────────────────────────────────────────────────────────
        ("Kanazawa", "market",
         "Omicho Market - fresh seafood market for lunch and shopping",
         None, "50 Kamiomicho, Kanazawa. Kanazawa's largest fresh market. Best for lunch — seafood bowls, sushi, fresh fish. Go late morning to beat the crowd. 3/30 afternoon arrival plan.", None),

        ("Kanazawa", "neighborhood",
         "Kazuemachi Chaya District - quiet traditional teahouse district",
         None, "Kazuemachi, Kanazawa. Smaller and quieter than Higashi Chaya. Traditional ochaya teahouses along the Asano River. Best visited in the evening when lanterns are lit.", None),

        ("Kanazawa", "neighborhood",
         "Higashi Chaya District - Kanazawa's most famous geisha district",
         None, "Higashiyama, Kanazawa. Most famous of Kanazawa's three chaya districts. Gold leaf shops, tea houses, traditional machiya. Go in the morning before tour groups arrive. UNESCO candidate area.", None),

        ("Kanazawa", "sightseeing",
         "Kanazawa Castle Park - Ishikawa Gate and Kanazawa Castle ruins",
         None, "1-1 Marunouchi, Kanazawa. Castle park surrounding Kanazawa Castle. Ishikawa Gate (1788) is the main landmark. Combine with Kenrokuen Garden directly adjacent.", None),

        ("Kanazawa", "park",
         "Kenrokuen Garden - one of Japan's three great landscape gardens",
         None, "1 Kenrokucho, Kanazawa. Edo-period garden considered one of Japan's three great gardens (along with Kairakuen and Korakuen). Beautiful late March for sakura. Adjacent to Kanazawa Castle.", None),

        ("Kanazawa", "museum",
         "D.T. Suzuki Museum - Zen philosophy and minimalist architecture",
         None, "3-4-20 Honda-machi, Kanazawa. Museum dedicated to Zen Buddhist philosopher D.T. Suzuki, born in Kanazawa. Minimalist architecture with water mirror courtyard. Exit south from Kenrokuen.", None),

        ("Kanazawa", "shrine",
         "Oyama Shrine - unusual shrine with Dutch stained glass gate",
         None, "1-1 Oyamamachi, Kanazawa. Dedicated to Maeda Toshiie, founder of Kanazawa domain. Dutch-style Shinmon Gate with stained glass windows on the third story — unique in Japan.", None),

        ("Kanazawa", "neighborhood",
         "Nagamachi Samurai District - preserved samurai residential quarter",
         None, "Nagamachi, Kanazawa. Well-preserved samurai residential neighborhood with mud walls (dozo), narrow lanes, and water channels. Nomura Samurai House offers entry to authentic interior.", None),

        ("Kanazawa", "temple",
         "Myoryuji (Ninja Temple) - Rinzai temple with hidden rooms and traps",
         None, "1-2-12 Nomachi, Kanazawa. Officially Myoryuji Rinzai temple, nicknamed Ninja Temple for its 29 staircases, 23 rooms, hidden passages, and trap doors — designed to protect the Maeda clan. Advance reservation required for guided tour.", None),

        # ── TOKYO (itinerary-specific) ─────────────────────────────────────────
        ("Tokyo", "shopping",
         "Sugamo Jizo-dori (Togenuki Jizo) - local shopping street near Airbnb",
         None, "4-35-1 Sugamo, Toshima City. Known as 'Grandma's Harajuku'. Traditional snacks, clothing, Jizo statues. 5 min walk from Sugamo Station. Near the Airbnb (4-37-6 Sugamo).", None),

        ("Tokyo", "shopping",
         "Sunshine City Ikebukuro - mall with Pokemon Center and Chiikawa Land",
         None, "3-1-3 Higashi-Ikebukuro, Toshima. Large mall complex in Ikebukuro. Houses Pokemon Center Mega Tokyo (2F Alpa) and Chiikawa Land. 15 min from Sugamo Airbnb. 4/2 plan.", None),

        ("Tokyo", "museum",
         "Ghibli Museum Mitaka - advance ticket required, lottery system",
         None, "1-1-83 Shimorenjaku, Mitaka. Studio Ghibli museum. Tickets by advance lottery only — buy months ahead from Lawson ticket website. Cat Bus exhibit, rooftop robot soldier. 15 min bus from Kichijoji Station. 4/3 plan.", None),

        ("Tokyo", "park",
         "Inokashira Park Kichijoji - sakura park with swan boats",
         None, "Kichijoji/Musashino. Large park with pond directly next to Kichijoji Station. Swan boats for rent. One of Tokyo's best sakura spots in late March/April. Studio Ghibli Museum is a 15 min walk.", None),

        ("Tokyo", "shopping",
         "Shirohige's Cream Puff Factory - Totoro cream puffs in Kichijoji",
         None, "2 Chome-7-5 Kichijoji Minamicho, Musashino. Totoro-shaped cream puffs (shu cream). Popular; sells out. Near Kichijoji Station south exit. 4/3 plan.", None),

        ("Tokyo", "museum",
         "Tokyo National Museum Ueno - Japan's largest museum",
         None, "13-9 Uenokoen, Taito. Japan's largest and oldest national museum. Ancient pottery, samurai armor, Buddhist sculpture, ukiyo-e, ceramics. Allow 2-3 hours. In Ueno Park. 4/4 plan.", None),

        ("Tokyo", "market",
         "Ameyoko Market Ueno - open-air market with street food and discount goods",
         None, "Between Ueno and Okachimachi stations, Taito. Bustling post-war style market street. Fresh food, dried seafood, discount cosmetics, streetwear, nuts. Good for cheap snacks and souvenirs. 4/4 plan.", None),

        ("Tokyo", "shopping",
         "Akihabara Electric Town - anime, manga, electronics district",
         None, "Soto-Kanda, Chiyoda. Tokyo's electronics and otaku culture center. Radio Kaikan building: figures, models, retro games (8 floors). Chuo Dori is the main pedestrian street on Sundays. Arcades, maid cafes. 4/4 plan.", None),

        ("Tokyo", "temple",
         "Senso-ji Asakusa - Tokyo's oldest and most visited temple",
         None, "2-3-1 Asakusa, Taito. Tokyo's oldest temple (645 AD). Kaminarimon gate with giant red lantern is the landmark. Nakamise shopping arcade leads to main hall. Arrive before 8am to avoid peak crowds. 4/5 plan.", None),

        ("Tokyo", "park",
         "Sumida Park Asakusa - riverside sakura park near SkyTree",
         None, "Hanakawado, Taito. Along Sumida River near Asakusa. One of Tokyo's top hanami spots. Beautiful views of Tokyo SkyTree from the park. Good before or after Senso-ji. 4/5 plan.", None),

        ("Tokyo", "restaurant",
         "Washoku Gyuuna yadoki Asakusa - beef dinner reservation 4/5",
         None, "Asakusa, Taito. Reservation: Sunday 4/5 at 5:30 PM, party of 3. Washoku beef (wagyu) restaurant in Asakusa area.", None),

        ("Tokyo", "restaurant",
         "Samurai Restaurant Shinjuku - samurai dinner show experience",
         None, "B1 Taro's Bldg, 1 Chome-7-7 Kabukicho, Shinjuku. Dinner show with samurai performance. 4/6 at 10:30 AM show. Approximately 30 minutes from Sugamo Airbnb. Book in advance.", None),

        ("Tokyo", "neighborhood",
         "Omoide Yokocho Memory Lane Shinjuku - tiny yakitori alley",
         None, "1 Chome-2 Nishishinjuku, Shinjuku. Narrow alley of tiny yakitori and izakaya stalls beside Shinjuku Station west exit. Old Tokyo atmosphere. Atmospheric at night. 4/6 evening plan.", None),

        ("Tokyo", "park",
         "Shinjuku Gyoen National Garden - best hanami spot in Shinjuku",
         None, "11 Naito-machi, Shinjuku. National garden with Japanese, French, and English sections. Top sakura destination. No alcohol allowed. Admission fee. 4/6 plan.", None),

        ("Tokyo", "sightseeing",
         "Tokyo Metropolitan Government Building - free observatory and night show",
         None, "2 Chome-8-1 Nishishinjuku, Shinjuku 163-8001. Free observation deck on North Tower (202m). Night show starts from 6 PM. One of best free views in Tokyo. 4/6 evening plan.", None),

        ("Tokyo", "sightseeing",
         "Shibuya Crossing - world's busiest pedestrian scramble",
         None, "Dogenzaka, Shibuya. World's most famous pedestrian scramble crossing. Most dramatic during rush hour or evening. View from Starbucks 2F or Mag's Park rooftop. 4/7 plan.", None),

        ("Tokyo", "shopping",
         "Parco Shibuya floor 6 - Nintendo, Pokemon, character shops",
         None, "15-1 Udagawacho, Shibuya. Contemporary art and character shopping building. Floor 6 has Nintendo Tokyo, Pokemon Center, and other character brand stores. 4/7 plan.", None),

        ("Tokyo", "shopping",
         "Takeshita Street Harajuku - youth fashion and crepes",
         None, "1-17-5 Jingumae, Shibuya. Harajuku's famous pedestrian street for kawaii fashion, crepes, character goods. Start at top (Harajuku Station end) at 10am as shops open. Walk down, explore back streets, cross to Cat Street. 4/7 plan.", None),

        ("Tokyo", "neighborhood",
         "Cat Street Harajuku to Shibuya - indie boutiques and backstreets",
         None, "Jingumae, Shibuya. Pedestrian street connecting Harajuku back streets to Omotesando. Independent boutiques, cafes, streetwear. Walk Cat Street all the way to Shibuya after exploring Takeshita. 4/7 plan.", None),

        ("Tokyo", "skincare",
         "@Cosme Tokyo Harajuku - Japan's largest beauty select store",
         None, "1 Chome-14-27 Jingumae, Shibuya 150-0001. Flagship @Cosme beauty store in Harajuku. Top-rated Japanese skincare, makeup, fragrance. Well curated. Brenda stop on 4/7.", None),

        ("Tokyo", "shrine",
         "Meiji Jingu Shrine Harajuku - forested Shinto shrine in the city",
         None, "1-1 Yoyogikamizonocho, Shibuya. Large forested shrine dedicated to Emperor Meiji and Empress Shoken. Free entry. 5 min walk from Harajuku Station. Serene contrast to Takeshita Street crowds.", None),

        ("Tokyo", "shopping",
         "Uniqlo Ginza Flagship - 12-floor global flagship with UTme studio",
         None, "6-9-5 Ginza, Chuo. Uniqlo's largest global store. 12 floors, UTme! custom print studio, Ginza-exclusive items, full range of LifeWear collections. 4/8 plan.", None),
    ]

    ki_count = 0
    for city, category, topic, source_url, content_summary, raw_content in items:
        cur.execute(
            """INSERT INTO knowledge_items
               (city, category, topic, source_url, content_summary, raw_content)
               VALUES (%s,%s,%s,%s,%s,%s)""",
            (city, category, topic, source_url, content_summary, raw_content))
        ki_count += 1
    print(f"knowledge_items: {ki_count} rows inserted")

    conn.commit()
    print()
    print("=== COMMITTED ===")

    cur.execute("SELECT city, COUNT(*) FROM trip_pois GROUP BY city ORDER BY city")
    print("trip_pois by city:")
    for r in cur.fetchall():
        print(f"  {r[0]:<15} {r[1]}")

    cur.execute("SELECT city, COUNT(*) FROM knowledge_items GROUP BY city ORDER BY city")
    print("knowledge_items by city:")
    for r in cur.fetchall():
        print(f"  {r[0] or 'NULL':<15} {r[1]}")

except Exception as e:
    conn.rollback()
    print(f"ERROR - rolled back: {e}")
    import traceback; traceback.print_exc()
finally:
    cur.close()
    conn.close()
