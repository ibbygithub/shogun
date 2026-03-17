"""
seed_osaka_kanazawa_knowledge.py — Seed Osaka and Kanazawa knowledge into shogun_v1.

Inserts curated knowledge items into the knowledge_items table.
Deduplicates on (topic, city) — skips if a record with the same topic+city exists.

Usage:
  python tools/seed_osaka_kanazawa_knowledge.py

Connection: DATABASE_URL env var, or defaults to local dev connection string.
"""

import os
import sys
import psycopg2

# ── Configuration ────────────────────────────────────────────────────────────

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://shogun_app:shogun_app@shogun-db.ibbytech.com:5432/shogun_v1",
)

# ── Knowledge Data ───────────────────────────────────────────────────────────
# Each tuple: (city, category, topic, content_summary, source_url, anchor)

KNOWLEDGE_ITEMS = [
    # ═══════════════════════════════════════════════════════════════════════════
    # OSAKA — restaurant (30+)
    # ═══════════════════════════════════════════════════════════════════════════
    ("osaka", "restaurant", "Ichiran Ramen Dotonbori",
     "Famous tonkotsu ramen chain with solo booth dining. Customizable broth richness, noodle firmness, garlic level. Expect queues. ~¥990/bowl.",
     "https://ichiran.com/", "dotonbori"),
    ("osaka", "restaurant", "Mizuno Okonomiyaki",
     "Dotonbori landmark since 1945. Known for yama-imo (mountain yam) okonomiyaki cooked on teppan in front of you. ¥1,200+.",
     None, "dotonbori"),
    ("osaka", "restaurant", "Takoyaki Wanaka",
     "Best takoyaki near Namba. Crispy outside, creamy inside. Multiple sauce options. ~¥500 for 8 pieces.",
     None, "namba"),
    ("osaka", "restaurant", "Kukuru Takoyaki",
     "Giant takoyaki shop at Dotonbori. Dashi-flavored balls with generous octopus pieces. ~¥600.",
     None, "dotonbori"),
    ("osaka", "restaurant", "Daruma Kushikatsu",
     "Shinsekai famous deep-fried skewers (kushikatsu). Iconic 'no double-dipping!' rule for communal sauce. ¥100-200 per stick.",
     None, "shinsekai"),
    ("osaka", "restaurant", "Zuboraya Fugu",
     "Shinsekai pufferfish restaurant with giant blowfish lantern sign. Fugu set menus from ¥3,000. Safe — licensed chefs only.",
     None, "shinsekai"),
    ("osaka", "restaurant", "Pablo Cheese Tart",
     "Shinsaibashi location. Freshly baked cheese tarts with rare/medium/well-done options. ~¥800.",
     None, "shinsaibashi"),
    ("osaka", "restaurant", "Rikuro's Cheesecake (Rikuro Ojisan)",
     "Namba, famous jiggly souffle cheesecake branded with a smiling old man. ¥965 for a whole cake. Queue moves fast.",
     None, "namba"),
    ("osaka", "restaurant", "Creo-Ru Curry",
     "Shinsaibashi Osaka-style curry rice. Rich, dark roux cooked for days. Simple but deeply flavorful. ~¥800.",
     None, "shinsaibashi"),
    ("osaka", "restaurant", "Menya Jikon (麺や而今)",
     "Tenjinbashi area ramen shop. Shoyu-based with clear refined broth. Michelin Bib Gourmand. ~¥950. Expect a wait.",
     None, "tenjinbashi"),
    ("osaka", "restaurant", "Hozenji Yokocho Alley restaurants",
     "Atmospheric stone-paved alley near Dotonbori with lantern-lit traditional izakayas. Intimate dining, reservations helpful.",
     None, "dotonbori"),
    ("osaka", "restaurant", "Torikizoku",
     "Popular budget chain izakaya. All food and drink items ¥350. Great for casual drinking and yakitori on a budget.",
     None, None),
    ("osaka", "restaurant", "Ajinoya Okonomiyaki",
     "Namba okonomiyaki spot where chef cooks Osaka-style pancakes in front of you with special house sauce. ~¥1,100.",
     None, "namba"),
    ("osaka", "restaurant", "Luke's Lobster Shinsaibashi",
     "Lobster rolls — rare find in Japan. Maine-style lobster, crab, or shrimp rolls. ~¥1,580.",
     None, "shinsaibashi"),
    ("osaka", "restaurant", "Kani Doraku",
     "Dotonbori crab restaurant with iconic moving mechanical crab sign. Full crab course meals. Lunch sets from ¥3,300.",
     None, "dotonbori"),
    ("osaka", "restaurant", "Kinryu Ramen",
     "Dotonbori 24-hour ramen shop with recognizable dragon sign. Cheap and filling. ~¥700. Good for late night.",
     None, "dotonbori"),
    ("osaka", "restaurant", "Imai Udon",
     "Near Hozenji temple. Osaka's oldest udon shop, operating since 1946. Famous kitsune udon (sweet tofu) ~¥900.",
     None, "dotonbori"),
    ("osaka", "restaurant", "Matsusakagyu Yakiniku M",
     "Namba premium yakiniku (grilled meat) specializing in Matsusaka beef — one of Japan's top wagyu brands. Lunch from ¥2,200.",
     None, "namba"),
    ("osaka", "restaurant", "Harukoma Sushi",
     "Tenjinbashi shotengai standing sushi bar. Extremely fresh fish at low prices. ¥150-400 per piece. Cash only.",
     None, "tenjinbashi"),
    ("osaka", "restaurant", "Tenjinbashisuji Shotengai food stalls",
     "Japan's longest shopping street (2.6km). Street food vendors throughout — korokke, taiyaki, ikayaki (grilled squid).",
     None, "tenjinbashi"),
    ("osaka", "restaurant", "Chibo Okonomiyaki",
     "Dotonbori high-end okonomiyaki with canal views. Multiple floors. ¥1,500+. Good for groups wanting a sit-down experience.",
     None, "dotonbori"),
    ("osaka", "restaurant", "Yodobashi Umeda food court",
     "Massive electronics store with excellent basement food court. Dozens of restaurants. Great rainy day option near Osaka Station.",
     None, "umeda"),
    ("osaka", "restaurant", "Tetsu Gyoza",
     "Crispy pan-fried dumplings (gyoza) in Tenjinbashi area. Thin skin, juicy filling. ~¥350 for 6 pieces.",
     None, "tenjinbashi"),
    ("osaka", "restaurant", "Tsuruhashi Korean Town",
     "Largest Korean district in Japan, near Tsuruhashi Station. Korean BBQ restaurants and kimchi shops everywhere. Lunch ~¥1,500.",
     None, "tsuruhashi"),
    ("osaka", "restaurant", "Bills Osaka",
     "Australian-style brunch in Kitahama area. Famous ricotta pancakes and scrambled eggs. ~¥1,800. Weekend reservations recommended.",
     None, "kitahama"),
    ("osaka", "restaurant", "Gram Premium Pancakes",
     "Shinsaibashi soufflé pancakes — limit 20 servings, served 3 times daily (11am, 3pm, 6pm). Arrive early. ~¥1,100.",
     None, "shinsaibashi"),
    ("osaka", "restaurant", "Kura Sushi",
     "Conveyor belt sushi chain. ¥110 per plate. Touch panel ordering in English. Gacha game every 5 plates. Fun for families.",
     None, None),
    ("osaka", "restaurant", "Cafe Absinthe",
     "Amerikamura (American Village) bohemian cafe. Italian-Japanese fusion cuisine. Lunch ~¥900. Relaxed atmosphere.",
     None, "amerikamura"),
    ("osaka", "restaurant", "Sumiyoshi Taisha area tea houses",
     "Near Sumiyoshi shrine. Traditional matcha and wagashi (Japanese confections). ~¥500. Peaceful setting.",
     None, "sumiyoshi"),
    ("osaka", "restaurant", "Osaka Station Daimaru depachika",
     "Department store basement food hall at Osaka Station. Premium bento, fresh pastries, wagashi. ¥800-2,000.",
     None, "umeda"),

    # ═══════════════════════════════════════════════════════════════════════════
    # OSAKA — shopping (15+)
    # ═══════════════════════════════════════════════════════════════════════════
    ("osaka", "shopping", "Tenjinbashisuji Shotengai",
     "Japan's longest covered shopping arcade at 2.6km. Over 600 shops with local prices. Less touristy than Shinsaibashi.",
     None, "tenjinbashi"),
    ("osaka", "shopping", "Shinsaibashi-suji",
     "Main Osaka shopping street. Mix of international brands (Zara, H&M, Uniqlo) and local boutiques. Covered arcade.",
     None, "shinsaibashi"),
    ("osaka", "shopping", "Amerikamura (American Village)",
     "Osaka's Harajuku equivalent. Vintage clothing, streetwear, record shops. ¥500-3,000 range. Young creative vibe.",
     None, "amerikamura"),
    ("osaka", "shopping", "Den Den Town (Nipponbashi)",
     "Osaka's Akihabara. Retro video games, anime figures, electronics, maid cafes. Multiple floors of otaku culture.",
     None, "nipponbashi"),
    ("osaka", "shopping", "Kuromon Market",
     "\"Osaka's Kitchen\" — fresh seafood, premium fruit, tamagoyaki, street food. Open 9am-5pm. Go hungry. Busiest 10am-2pm.",
     None, "namba"),
    ("osaka", "shopping", "Namba Parks",
     "Garden-themed mall with dramatic rooftop terrace and greenery. Fashion shops, restaurants, cinema. Near Namba Station.",
     None, "namba"),
    ("osaka", "shopping", "Grand Front Osaka",
     "Premium shopping complex near Osaka Station. Flagship stores, restaurants, innovation labs. Good rainy day activity.",
     None, "umeda"),
    ("osaka", "shopping", "Don Quijote (Donki) Dotonbori",
     "24-hour discount megastore. Souvenirs, snacks, cosmetics, electronics, tax-free. Iconic Ferris wheel on building.",
     None, "dotonbori"),
    ("osaka", "shopping", "Matsumoto Kiyoshi Shinsaibashi",
     "Largest drugstore in the area. Japanese skincare (Hada Labo, KOSE, SK-II), cosmetics, tax-free counter for tourists.",
     None, "shinsaibashi"),
    ("osaka", "shopping", "ABC-Mart Shinsaibashi",
     "Japanese shoe retailer. Limited edition sneakers, Japanese brands (Onitsuka Tiger, ASICS), affordable prices.",
     None, "shinsaibashi"),
    ("osaka", "shopping", "LOFT Umeda",
     "Japanese lifestyle goods store. Stationery, home items, beauty, unique gifts. Great for souvenirs.",
     None, "umeda"),
    ("osaka", "shopping", "Tokyu Hands Shinsaibashi",
     "DIY, crafts, gadgets, travel goods. Quirky Japanese items you won't find elsewhere. Multiple floors.",
     None, "shinsaibashi"),
    ("osaka", "shopping", "Mandarake Grand Chaos",
     "Nipponbashi mega-store for anime, manga, vintage toys, cosplay items. Multi-floor otaku paradise.",
     None, "nipponbashi"),
    ("osaka", "shopping", "Dagashi-ya in Shinsekai",
     "Old-school Japanese penny candy shops (dagashi-ya). Nostalgic retro sweets ¥10-100. Fun for kids and adults.",
     None, "shinsekai"),
    ("osaka", "shopping", "Rinku Premium Outlets",
     "Near Kansai Airport. 200+ shops with 30-80% off. Good for last-day shopping before flight. Shuttle from airport.",
     None, None),

    # ═══════════════════════════════════════════════════════════════════════════
    # OSAKA — temple (8+)
    # ═══════════════════════════════════════════════════════════════════════════
    ("osaka", "temple", "Sumiyoshi Taisha",
     "Oldest shrine in Osaka (3rd century). Iconic arched Taiko-bashi bridge. Predates Buddhist influence on shrine architecture. Free entry.",
     None, "sumiyoshi"),
    ("osaka", "temple", "Shitennoji Temple",
     "Japan's first officially commissioned Buddhist temple (593 AD). Monthly flea market on 21st-22nd. ¥300 inner precinct.",
     None, "tennoji"),
    ("osaka", "temple", "Osaka Castle",
     "Iconic Osaka landmark and museum. ¥600 entry. Observation deck with city views. Surrounding park is prime cherry blossom spot.",
     None, "osaka-castle"),
    ("osaka", "temple", "Hozenji Temple",
     "Tiny temple tucked in Dotonbori alley. Moss-covered Fudo Myo-o statue — splash water on it for good luck in love/business.",
     None, "dotonbori"),
    ("osaka", "temple", "Namba Yasaka Shrine",
     "Striking giant lion-head stage building (Ema-den). Very photogenic. Said to swallow bad fortune. Free entry.",
     None, "namba"),
    ("osaka", "temple", "Tsuyunoten Shrine",
     "Near Tenjinbashisuji shotengai. Patron shrine of performing arts. Beautiful plum trees bloom in February.",
     None, "tenjinbashi"),
    ("osaka", "temple", "Isshinji Temple",
     "Unique temple near Shinsekai. Okotsu-butsu statues made from cremation ashes of the deceased. Fascinating and respectful.",
     None, "shinsekai"),
    ("osaka", "temple", "Tamatsukuri Inari Shrine",
     "Fox shrine near Osaka Castle with vermillion torii gates. Less crowded alternative to Kyoto's Fushimi Inari.",
     None, "osaka-castle"),

    # ═══════════════════════════════════════════════════════════════════════════
    # OSAKA — transit (8+)
    # ═══════════════════════════════════════════════════════════════════════════
    ("osaka", "transit", "ICOCA card",
     "Rechargeable transit card. Buy at any JR or Metro station (¥500 deposit). Works on all Osaka trains, buses, and at convenience stores.",
     None, None),
    ("osaka", "transit", "Osaka Metro overview",
     "9 subway lines covering most tourist areas. Single ride ¥180-380. Midosuji Line (red) is the main north-south trunk.",
     None, None),
    ("osaka", "transit", "Enjoy Eco Card",
     "¥820/day unlimited Osaka Metro + city bus. ¥620 on weekends and holidays. Buy at any Metro station ticket machine.",
     None, None),
    ("osaka", "transit", "Osaka to Nara day trip transit",
     "Kintetsu Railway from Namba — 35 min, ¥680, drops you closer to deer park. JR from Tennoji — 45 min, ¥480, covered by JR Pass.",
     None, None),
    ("osaka", "transit", "Osaka to USJ transit",
     "JR Yumesaki Line from Osaka Station or Nishikujo Station. 15 min ride, ¥180. Direct train, no transfer needed from Osaka Station.",
     None, None),
    ("osaka", "transit", "Kansai Airport to Osaka",
     "Nankai Rapi:t express to Namba (34 min, ¥1,450, retro-futuristic train). JR Haruka to Tennoji (30 min) or Shin-Osaka (50 min).",
     None, None),
    ("osaka", "transit", "Tenjinbashisuji-Rokuchome Station",
     "Major interchange: Sakaisuji Line + Tanimachi Line. Direct to Namba in 15 min. Convenient if staying in Tenjinbashi area.",
     None, "tenjinbashi"),
    ("osaka", "transit", "Osaka night transport",
     "Osaka Metro stops around midnight. Night buses available on major routes. Taxis expensive (¥2,000+ for short rides). Plan last train.",
     None, None),

    # ═══════════════════════════════════════════════════════════════════════════
    # OSAKA — practical (12+)
    # ═══════════════════════════════════════════════════════════════════════════
    ("osaka", "practical", "International ATM locations Osaka",
     "7-Eleven (7-Bank), JP Post Office, Lawson ATM — all accept Visa/Mastercard. 7-Eleven is most reliable and everywhere.",
     None, None),
    ("osaka", "practical", "Coin lockers Osaka Station",
     "¥400 small, ¥500 medium, ¥700 large per day. Located at JR Osaka Station Central Exit. Fill up by midday on weekends.",
     None, "umeda"),
    ("osaka", "practical", "Coin lockers Namba",
     "Under Namba Walk underground mall. ¥400-600. Fill up by noon on weekends. Alternative: luggage storage at tourist info counter.",
     None, "namba"),
    ("osaka", "practical", "Osaka Tourist Info Namba",
     "Namba Station B1F level. English maps, attraction guides, Enjoy Eco Card purchase. Staff speak English.",
     None, "namba"),
    ("osaka", "practical", "Free WiFi Osaka",
     "Osaka Free WiFi available at Metro stations and major tourist spots. 30-minute sessions, re-register to extend. Konbini WiFi also free.",
     None, None),
    ("osaka", "practical", "Tax-free shopping Japan",
     "Spend ¥5,000+ at one store same day. Bring passport. Look for Tax-Free signs. Consumables (food, cosmetics) sealed in bag, cannot open in Japan.",
     None, None),
    ("osaka", "practical", "Konbini (convenience stores)",
     "7-Eleven, Lawson, FamilyMart on every block. ATM, hot food (onigiri, nikuman), printing, tickets, bill payment. Open 24/7.",
     None, None),
    ("osaka", "practical", "Luggage forwarding (takkyubin)",
     "Yamato (Kuroneko) or Sagawa Express. Send bags between hotels for ¥2,000-3,000. Arrange at hotel front desk or any konbini.",
     None, None),
    ("osaka", "practical", "Tipping etiquette Japan",
     "Never tip in Japan. It can be considered rude or confusing. Service charge is included. Simply say 'gochisousama deshita' (thank you for the meal).",
     None, None),
    ("osaka", "practical", "Trash disposal Japan",
     "Carry your trash — very few public bins. Konbini bins are technically for store purchases only. Hotels have trash sorting (burnable, plastic, cans).",
     None, None),
    ("osaka", "practical", "Daiso near Tenjinbashi",
     "100-yen shop for travel supplies, kitchen items, umbrellas, phone accessories. Everything ¥100 (some ¥200-500). Multiple Osaka locations.",
     None, "tenjinbashi"),
    ("osaka", "practical", "Emergency numbers Japan",
     "110 for police, 119 for fire/ambulance. US Embassy Tokyo: 03-3224-5000. Osaka has English-speaking emergency support via 06-6773-6533.",
     None, None),

    # ═══════════════════════════════════════════════════════════════════════════
    # OSAKA — nara_daytrip (6+)
    # ═══════════════════════════════════════════════════════════════════════════
    ("osaka", "nara_daytrip", "Nara Park deer",
     "1,200 free-roaming sacred deer. Buy shika-senbei (deer crackers) ¥200 at park vendors. Deer bow when you bow. Watch bags — they nibble everything.",
     None, None),
    ("osaka", "nara_daytrip", "Todai-ji Temple",
     "World's largest wooden building housing a 15m bronze Great Buddha. ¥600 entry. Try squeezing through the pillar hole for enlightenment.",
     None, None),
    ("osaka", "nara_daytrip", "Kasuga Taisha",
     "Ancient shrine with 3,000 stone and bronze lanterns. Atmospheric forest path. ¥500 for inner sanctuary. Lantern festivals in Feb and Aug.",
     None, None),
    ("osaka", "nara_daytrip", "Naramachi district",
     "Preserved Edo-era merchant district. Free museums, charming cafes, traditional machiya townhouses. Look for red sarubobo monkey charms.",
     None, None),
    ("osaka", "nara_daytrip", "Nara food — Kakinoha-zushi",
     "Persimmon leaf-wrapped sushi is Nara's signature dish. Try Tanaka near Kintetsu Nara Station. Also: warabi mochi and kuzu desserts.",
     None, None),
    ("osaka", "nara_daytrip", "Kintetsu Nara vs JR Nara station",
     "Kintetsu Nara is closer to deer park (5 min walk). JR Nara is 15 min walk. Kintetsu is faster from Namba; JR is covered by JR Pass.",
     None, None),

    # ═══════════════════════════════════════════════════════════════════════════
    # OSAKA — usj (5+)
    # ═══════════════════════════════════════════════════════════════════════════
    ("osaka", "usj", "USJ Express Pass",
     "¥7,800-12,800 depending on day and attractions. HIGHLY recommended for Super Nintendo World and Harry Potter. Buy online in advance.",
     "https://www.usj.co.jp/", None),
    ("osaka", "usj", "Super Nintendo World",
     "Timed entry required on busy days. Get numbered ticket or buy Express Pass. Power-Up wristband (¥3,200) for interactive games.",
     None, None),
    ("osaka", "usj", "First train to USJ from Tenjinbashi",
     "Metro Sakaisuji Line to Nishikujo, transfer JR Yumesaki Line. ~45 min total. Arrive by 8:00 for rope drop. Park opens 8:30-9:00.",
     None, "tenjinbashi"),
    ("osaka", "usj", "USJ food options",
     "Butterbeer ¥700 (Harry Potter area), Toadstool Cafe ¥1,200 (Nintendo World, long queue). Better value food at Universal CityWalk outside.",
     None, None),
    ("osaka", "usj", "Universal CityWalk",
     "Restaurant and shopping complex outside USJ gates — no ticket needed. TK Ramen, Bubba Gump Shrimp, takoyaki stalls. Good for dinner after park.",
     None, None),

    # ═══════════════════════════════════════════════════════════════════════════
    # KANAZAWA — restaurant (12+)
    # ═══════════════════════════════════════════════════════════════════════════
    ("kanazawa", "restaurant", "Omicho Market kaisendon",
     "Seafood bowls (kaisendon) at market stalls. Fresh from Sea of Japan. ¥2,000-3,500. Best selection before 10am when fishermen deliver.",
     None, "omicho"),
    ("kanazawa", "restaurant", "Omicho Market Yamasan",
     "Premium sushi counter inside Omicho Market. Omakase (chef's choice) from ¥3,500. Counter seats, watch chef prepare local neta.",
     None, "omicho"),
    ("kanazawa", "restaurant", "Ippuku Sushi",
     "Near Omicho Market, affordable rotating sushi with Kanazawa-specific fish (nodoguro, buri). ¥100-350 per plate.",
     None, "omicho"),
    ("kanazawa", "restaurant", "Tamazushi",
     "Kanazawa Station area premium sushi. Uses local Sea of Japan fish. Lunch sets from ¥2,500. Good arrival/departure meal option.",
     None, "kanazawa-station"),
    ("kanazawa", "restaurant", "Itaru Honten",
     "Famous izakaya near Korinbo. Known for sashimi and jibuni stew (Kanazawa's signature duck/wheat-gluten dish). Reserve ahead. ~¥900 for jibuni.",
     None, "korinbo"),
    ("kanazawa", "restaurant", "Fumuroya Cafe",
     "Higashi Chaya area cafe specializing in fu (wheat gluten) dishes and matcha. Traditional Kanazawa sweets. Elegant atmosphere.",
     None, "higashi-chaya"),
    ("kanazawa", "restaurant", "Hacchobo",
     "Kaiseki (traditional multi-course) restaurant near Kenroku-en. Seasonal ingredients, beautiful presentation. Lunch from ¥5,500.",
     None, "kenrokuen"),
    ("kanazawa", "restaurant", "Curry Champion (Go Go Curry)",
     "Kanazawa-style curry: dark, thick roux served on steel plate with shredded cabbage and tonkatsu. ¥750. Hearty comfort food.",
     None, None),
    ("kanazawa", "restaurant", "Turban Curry",
     "Rival Kanazawa curry institution. Katsu curry ¥850. Near Katamachi entertainment district. Dark rich roux is the signature.",
     None, "katamachi"),
    ("kanazawa", "restaurant", "Noda-ya unagi",
     "Eel (unagi) restaurant near Omicho Market. Kabayaki and hitsumabushi styles. Kanazawa unagi has lighter seasoning. ~¥2,500.",
     None, "omicho"),
    ("kanazawa", "restaurant", "A&K craft beer bar",
     "Craft beer bar with 10 taps including local Kanazawa and Hokuriku breweries. Near Katamachi nightlife area.",
     None, "katamachi"),
    ("kanazawa", "restaurant", "8 Banquet (Kanazawa Station)",
     "Restaurant floor in Kanazawa Station building. Multiple options — sushi, ramen, curry, izakaya. Convenient for dinner on arrival.",
     None, "kanazawa-station"),

    # ═══════════════════════════════════════════════════════════════════════════
    # KANAZAWA — shopping (8+)
    # ═══════════════════════════════════════════════════════════════════════════
    ("kanazawa", "shopping", "Hakuichi Gold Leaf shop",
     "Higashi Chaya flagship store. Famous gold leaf ice cream (¥891). Gold leaf cosmetics, crafts, and edible gold souvenirs.",
     None, "higashi-chaya"),
    ("kanazawa", "shopping", "Kanazawa Station Rinto",
     "Shopping mall inside Kanazawa Station. Local crafts, Kanazawa sweets, omiyage (souvenirs). Convenient last-stop shopping.",
     None, "kanazawa-station"),
    ("kanazawa", "shopping", "Kutani pottery shops",
     "Colorful Kanazawa ceramics (Kutani-yaki). Bold reds, greens, yellows. Kutani Kosen shop near Kenroku-en. ¥1,000-50,000 range.",
     None, "kenrokuen"),
    ("kanazawa", "shopping", "Kaga Yuzen silk",
     "Traditional hand-dyed silk — Kanazawa's textile art form. Kimono fabric, scarves, handkerchiefs from ¥500. Workshops available.",
     None, None),
    ("kanazawa", "shopping", "Omicho Market souvenir shops",
     "Dried fish, gold leaf products, local sake, pickles. Good for edible souvenirs. Shops open 9am-5pm.",
     None, "omicho"),
    ("kanazawa", "shopping", "Hirosaka area boutiques",
     "Upscale shopping district between Kanazawa Castle and Katamachi. Independent boutiques, galleries, cafes.",
     None, "hirosaka"),
    ("kanazawa", "shopping", "Kanazawa Hyakubangai",
     "Station-adjacent shopping mall. Local food souvenirs, Yukizuri candy, craft goods. Open until 8:30pm.",
     None, "kanazawa-station"),
    ("kanazawa", "shopping", "Tatemachi Street",
     "Fashionable shopping street between 21st Century Museum and Katamachi. Cafes, boutiques, select shops.",
     None, "tatemachi"),

    # ═══════════════════════════════════════════════════════════════════════════
    # KANAZAWA — temple (8+)
    # ═══════════════════════════════════════════════════════════════════════════
    ("kanazawa", "temple", "Kenroku-en Garden",
     "One of Japan's top 3 gardens. Stunning in every season — snow-covered yukitsuri in winter, cherry blossoms spring. ¥320 entry. Allow 1-2 hours.",
     None, "kenrokuen"),
    ("kanazawa", "temple", "Kanazawa Castle Park",
     "Reconstructed Edo-era gates and turrets. Park grounds are free. ¥320 for interior exhibits. Adjacent to Kenroku-en.",
     None, "kenrokuen"),
    ("kanazawa", "temple", "Higashi Chaya District",
     "Beautifully preserved geisha district with wooden tea houses from 1820s. Gold leaf shops, traditional cafes. Most photogenic area in Kanazawa.",
     None, "higashi-chaya"),
    ("kanazawa", "temple", "Nishi Chaya District",
     "Smaller, quieter geisha quarter on the west side. Fewer tourists. Myoryuji (Ninja Temple) is nearby.",
     None, "nishi-chaya"),
    ("kanazawa", "temple", "Myoryuji (Ninja Temple)",
     "Hidden trap doors, secret passages, trick stairs. ¥1,000 entry. Reservation required. Tour in Japanese only (English pamphlet available).",
     None, "nishi-chaya"),
    ("kanazawa", "temple", "D.T. Suzuki Museum",
     "Minimalist museum honoring Zen Buddhist philosopher. Beautiful Water Mirror Garden for contemplation. ¥310. Near 21st Century Museum.",
     None, None),
    ("kanazawa", "temple", "Oyama Shrine",
     "Unique gate with Dutch-style stained glass windows — unusual for a Shinto shrine. Free entry. Beautiful illumination at night.",
     None, None),
    ("kanazawa", "temple", "Nagamachi Samurai District",
     "Preserved samurai residences with earthen walls and water channels. Nomura-ke house ¥550, one of Japan's best samurai homes.",
     None, "nagamachi"),

    # ═══════════════════════════════════════════════════════════════════════════
    # KANAZAWA — museum (4+)
    # ═══════════════════════════════════════════════════════════════════════════
    ("kanazawa", "museum", "21st Century Museum of Contemporary Art",
     "Iconic circular glass building. Free public zone with Leandro Erlich's 'Swimming Pool'. Paid exhibitions ¥1,200. Central location.",
     None, None),
    ("kanazawa", "museum", "Ishikawa Prefectural Museum of Art",
     "Houses National Treasure 'Iroji' textile (Kaga Yuzen masterwork). Japanese art and crafts. ¥370. Near Kenroku-en.",
     None, "kenrokuen"),
    ("kanazawa", "museum", "Kanazawa Noh Museum",
     "Free museum showcasing traditional Noh theater. Costumes, masks, artifacts. Kanazawa has strongest Noh tradition outside Tokyo/Kyoto.",
     None, None),
    ("kanazawa", "museum", "Kanazawa Phonograph Museum",
     "Collection of 600+ antique phonographs. Listening sessions where staff play records on vintage machines. ¥310.",
     None, None),

    # ═══════════════════════════════════════════════════════════════════════════
    # KANAZAWA — transit (5+)
    # ═══════════════════════════════════════════════════════════════════════════
    ("kanazawa", "transit", "Osaka to Kanazawa — JR Thunderbird",
     "JR Thunderbird limited express from Osaka Station. 2h40m, ¥7,260. Reserved seat recommended (unreserved can fill up). Scenic route.",
     None, None),
    ("kanazawa", "transit", "Kanazawa to Tokyo — Hokuriku Shinkansen",
     "Kagayaki (fastest, 2h30m, ¥14,120) or Hakutaka (stops more, 3h). Covered by JR Pass. Reserve window seat for mountain views.",
     None, None),
    ("kanazawa", "transit", "Kanazawa Loop Bus",
     "¥200 per ride or ¥600 day pass. Covers all major tourist spots in a loop. Runs every 15 min. Right Loop and Left Loop — check direction.",
     None, None),
    ("kanazawa", "transit", "Kenrokuen Shuttle",
     "Free shuttle bus from Kanazawa Station to Kenroku-en area on weekends and holidays. Saves ¥200 each way.",
     None, None),
    ("kanazawa", "transit", "Kanazawa walkability",
     "Kanazawa is very walkable. Omicho Market to Kenroku-en: 15 min walk. Higashi Chaya from Omicho: 10 min. Flat terrain.",
     None, None),

    # ═══════════════════════════════════════════════════════════════════════════
    # KANAZAWA — practical (5+)
    # ═══════════════════════════════════════════════════════════════════════════
    ("kanazawa", "practical", "Coin lockers Kanazawa Station",
     "East Exit of station. ¥400-700 per day. Fill up on weekends. Alternative: send luggage ahead via Yamato (Kuroneko) takkyubin service.",
     None, "kanazawa-station"),
    ("kanazawa", "practical", "Kanazawa tourist information",
     "East Exit of Kanazawa Station. English maps, bus passes, attraction tickets. Staff speak English. Open 8:30am-8pm.",
     None, "kanazawa-station"),
    ("kanazawa", "practical", "Kanazawa weather and rain",
     "Kanazawa proverb: 'Bento wasure temo, kasa wasure na' — forget your lunch, but not your umbrella. Rain is frequent year-round. Always carry one.",
     None, None),
    ("kanazawa", "practical", "Kanazawa gold leaf",
     "99% of Japan's gold leaf (kinpaku) is produced in Kanazawa. Edible gold on ice cream, sweets, even beer. Good souvenir — lightweight.",
     None, None),
    ("kanazawa", "practical", "Hotel Sanraku location tips",
     "Located in Owaricho. 5 min walk to Omicho Market, 10 min to Higashi Chaya District. Central location for exploring on foot.",
     None, "owaricho"),
]

# ── SQL ──────────────────────────────────────────────────────────────────────

CHECK_DUPLICATE_SQL = """
SELECT 1 FROM knowledge_items WHERE topic = %s AND city = %s LIMIT 1;
"""

INSERT_SQL = """
INSERT INTO knowledge_items (city, category, topic, content_summary, source_url, anchor)
VALUES (%s, %s, %s, %s, %s, %s)
ON CONFLICT DO NOTHING;
"""

COUNT_SQL = """
SELECT city, category, count(*)
FROM knowledge_items
WHERE city IN ('osaka', 'kanazawa')
GROUP BY city, category
ORDER BY city, category;
"""


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    print(f"Connecting to database...")
    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = False
    except Exception as exc:
        print(f"[ERROR] Failed to connect: {exc}", file=sys.stderr)
        sys.exit(1)

    inserted = 0
    skipped = 0
    errors = 0

    print(f"Processing {len(KNOWLEDGE_ITEMS)} knowledge items...")

    for city, category, topic, content_summary, source_url, anchor in KNOWLEDGE_ITEMS:
        try:
            with conn.cursor() as cur:
                cur.execute(INSERT_SQL, (city, category, topic, content_summary, source_url, anchor))
                if cur.rowcount == 1:
                    inserted += 1
                else:
                    skipped += 1  # ON CONFLICT DO NOTHING — row already existed
        except Exception as exc:
            conn.rollback()
            print(f"  [ERROR] Failed to insert '{topic}' ({city}): {exc}", file=sys.stderr)
            errors += 1
            continue

    conn.commit()

    # ── Verification ─────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("SEEDING COMPLETE")
    print(f"  Inserted : {inserted}")
    print(f"  Skipped  : {skipped} (already existed)")
    print(f"  Errors   : {errors}")
    print("=" * 60)

    # Count by city and category
    try:
        with conn.cursor() as cur:
            cur.execute(COUNT_SQL)
            rows = cur.fetchall()
    except Exception as exc:
        print(f"[ERROR] Verification query failed: {exc}", file=sys.stderr)
        conn.close()
        sys.exit(1)

    print("\nKnowledge items by city/category:")
    osaka_total = 0
    kanazawa_total = 0
    for city, category, count in rows:
        print(f"  {city:12s} / {category:20s} : {count}")
        if city == "osaka":
            osaka_total += count
        elif city == "kanazawa":
            kanazawa_total += count

    print(f"\n  Osaka total    : {osaka_total}")
    print(f"  Kanazawa total : {kanazawa_total}")
    print(f"  Combined total : {osaka_total + kanazawa_total}")

    # Validation checks
    print("\nValidation:")
    osaka_pass = osaka_total >= 80
    kanazawa_pass = kanazawa_total >= 40
    print(f"  Osaka >= 80    : {'PASS' if osaka_pass else 'FAIL'} ({osaka_total})")
    print(f"  Kanazawa >= 40 : {'PASS' if kanazawa_pass else 'FAIL'} ({kanazawa_total})")

    conn.close()

    if not (osaka_pass and kanazawa_pass):
        print("\n[WARN] Minimum item counts not met.", file=sys.stderr)
        sys.exit(1)

    print("\nDone.")


if __name__ == "__main__":
    main()
