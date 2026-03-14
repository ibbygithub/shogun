#!/usr/bin/env python3
"""
Seed tool — trip_pois table.

Clears and reloads all city POI data including Madeline layer and crowd intelligence.
Idempotent — safe to re-run.

Run from brainnode-01:
    cd /opt/git/work/shogun/app-services/shogun-core
    source venv/bin/activate && python tools/seed_pois.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv()

import psycopg2
import psycopg2.extras

conn_params = dict(
    host=os.environ["DB_HOST"],
    port=int(os.environ.get("DB_PORT", 5432)),
    dbname=os.environ["DB_NAME"],
    user=os.environ["DB_USER"],
    password=os.environ["DB_PASSWORD"],
)

# ── POI data ─────────────────────────────────────────────────────────────────
# Tags guide:
#   group        — good for all three travelers
#   todd         — Todd-specific interest
#   madeline     — Madeline-specific interest
#   brenda       — Brenda-specific interest
#   food         — dining, markets, food streets
#   seafood      — seafood focus (Brenda excellent fit)
#   anime        — anime/manga/figures
#   ghibli       — Studio Ghibli specific
#   electronics  — maker/ESP32 (Todd)
#   cameras      — vintage cameras (Todd + Madeline)
#   ceramics     — Kutani ware etc. (Todd)
#   knives       — cutlery (Todd)
#   vintage      — thrift/vintage clothing (Madeline)
#   retro-gaming — handheld/retro consoles (Madeline)
#   sightseeing  — temples, shrines, gardens
#   early-morning — best before 9am
#   crowd-warning — gets very crowded
#   cherry-blossom — cherry blossom timing note

POIS = [

    # ════════════════════════════════════════════
    # OSAKA
    # ════════════════════════════════════════════

    {
        "city": "osaka",
        "name_en": "Dotonbori",
        "name_ja": "道頓堀",
        "category": "food",
        "lat": 34.6686,
        "lng": 135.5013,
        "address_en": "Dotonbori, Chuo-ku, Osaka",
        "address_ja": "大阪市中央区道頓堀",
        "tags": ["group", "food", "crowd-warning", "evening"],
        "crowd_notes": "Packed after 6pm, extremely so on weekends during cherry blossom. Midday is manageable. Neon lights best at night.",
        "best_time_notes": "11am-1pm for lunch without long waits, or 9pm+ for late dinner. Giant Glico running man sign on Ebisubashi bridge. Group-friendly — tons of variety covering all dietary profiles.",
        "source": "seed",
    },
    {
        "city": "osaka",
        "name_en": "Kuromon Ichiba Market",
        "name_ja": "黒門市場",
        "category": "food",
        "lat": 34.6694,
        "lng": 135.5066,
        "address_en": "2 Nipponbashi, Chuo-ku, Osaka",
        "address_ja": "大阪市中央区日本橋2丁目",
        "tags": ["group", "food", "seafood", "brenda"],
        "crowd_notes": "Busiest 9am-noon. Many stalls wind down or close by 3pm — it is a morning market.",
        "best_time_notes": "Arrive 9am for freshest selection. Brenda: exceptional seafood on sticks and fresh fish. Group: try takoyaki, grilled scallops, uni. Most stalls ready by 9:30am.",
        "source": "seed",
    },
    {
        "city": "osaka",
        "name_en": "Den Den Town (Nipponbashi)",
        "name_ja": "でんでんタウン（日本橋）",
        "category": "shopping",
        "lat": 34.6580,
        "lng": 135.5055,
        "address_en": "Nipponbashi, Naniwa-ku, Osaka",
        "address_ja": "大阪市浪速区日本橋",
        "tags": ["madeline", "todd", "anime", "electronics", "retro-gaming", "cameras"],
        "crowd_notes": "Weekends packed with domestic otaku tourists. Weekday mornings quiet. Many shops open 11am.",
        "best_time_notes": "Weekday morning for easiest browsing. Osaka's equivalent of Akihabara but more local. Animate, Mandarake, Super Potato branches here. Todd: some electronics component shops on side streets.",
        "source": "seed",
    },
    {
        "city": "osaka",
        "name_en": "Tenjinbashi-dori Shotengai",
        "name_ja": "天神橋筋商店街",
        "category": "shopping",
        "lat": 34.7121,
        "lng": 135.5134,
        "address_en": "Tenjinbashi, Kita-ku, Osaka",
        "address_ja": "大阪市北区天神橋",
        "tags": ["group", "food", "local", "shotengai"],
        "crowd_notes": "Japan's longest covered shopping street (~2.6km). Extremely local — almost no foreign tourists. Low crowds most times.",
        "best_time_notes": "Morning 10am onward. Traditional food stalls, local sweets, daily goods. Good for breakfast or a morning wander from the Tenjinbashi Airbnb.",
        "source": "seed",
    },
    {
        "city": "osaka",
        "name_en": "Shinsekai (Kushikatsu District)",
        "name_ja": "新世界",
        "category": "food",
        "lat": 34.6526,
        "lng": 135.5063,
        "address_en": "Shinsekai, Naniwa-ku, Osaka",
        "address_ja": "大阪市浪速区新世界",
        "tags": ["group", "food", "local"],
        "crowd_notes": "Touristy but authentic. Evenings draw both locals and visitors for kushikatsu (deep-fried skewers). More relaxed than Dotonbori.",
        "best_time_notes": "Dinner 6-8pm. Kushikatsu restaurants line the streets — the rule is never double-dip in the shared sauce. Also Tsutenkaku Tower for views. Group dietary note: kushikatsu offers vegetable/fish skewers for Brenda.",
        "source": "seed",
    },
    {
        "city": "osaka",
        "name_en": "Namba Parks / Namba area",
        "name_ja": "なんばパークス",
        "category": "food",
        "lat": 34.6644,
        "lng": 135.5002,
        "address_en": "2-10-70 Nanbanaka, Naniwa-ku, Osaka",
        "address_ja": "大阪市浪速区難波中2-10-70",
        "tags": ["group", "food"],
        "crowd_notes": "Urban mall with rooftop garden — less overwhelming than street-level Dotonbori. Good for a group meal with options for all dietary profiles.",
        "best_time_notes": "Lunch or dinner. Multiple restaurant floors covering Japanese, ramen, sushi. Kintetsu Nara Line access for Nara day trip.",
        "source": "seed",
    },

    # ════════════════════════════════════════════
    # NARA
    # ════════════════════════════════════════════

    {
        "city": "nara",
        "name_en": "Nara Park (Deer Park)",
        "name_ja": "奈良公園",
        "category": "sightseeing",
        "lat": 34.6853,
        "lng": 135.8427,
        "address_en": "Zoshicho, Nara City, Nara 630-8212",
        "address_ja": "奈良市雑司町630-8212",
        "tags": ["group", "sightseeing", "early-morning", "crowd-warning", "cherry-blossom"],
        "crowd_notes": "Tour buses arrive 9am-10am in waves. After 10am it is very crowded during cherry blossom peak. ~1,200 wild deer roam freely — they bow for shika senbei (deer crackers) sold at kiosks.",
        "best_time_notes": "ARRIVE BEFORE 9AM. Late March = cherry blossom peak — early morning light through the blossoms with deer is exceptional. Buy deer crackers at kiosks (150 yen). Hold bag away from your body.",
        "source": "seed",
    },
    {
        "city": "nara",
        "name_en": "Todai-ji Temple (Great Buddha)",
        "name_ja": "東大寺（大仏）",
        "category": "sightseeing",
        "lat": 34.6888,
        "lng": 135.8398,
        "address_en": "406-1 Zoshicho, Nara City, Nara",
        "address_ja": "奈良市雑司町406-1",
        "tags": ["group", "sightseeing", "early-morning", "crowd-warning"],
        "crowd_notes": "Opens 7:30am. World's largest wooden building. Most tour groups arrive after 10am. Entry fee ~600 yen.",
        "best_time_notes": "7:30-9am. The Great Buddha (15m bronze Vairocana) is genuinely awe-inspiring. Also look for the pillar with the nostril-sized hole — fitting through it is said to grant enlightenment.",
        "source": "seed",
    },
    {
        "city": "nara",
        "name_en": "Kasugataisha Shrine",
        "name_ja": "春日大社",
        "category": "sightseeing",
        "lat": 34.6814,
        "lng": 135.8449,
        "address_en": "160 Kasuganocho, Nara City, Nara 630-8212",
        "address_ja": "奈良市春日野町160 630-8212",
        "tags": ["group", "sightseeing", "early-morning"],
        "crowd_notes": "Far fewer tourists than Todai-ji despite being equally significant. 10 min walk from the main deer area. The approach path lined with 3,000 stone lanterns is stunning.",
        "best_time_notes": "Open 6am. Morning is best — lantern-lined approach through forest is atmospheric. If the lantern festival dates coincide (~Feb/Aug) it is extraordinary.",
        "source": "seed",
    },
    {
        "city": "nara",
        "name_en": "Naramachi Historic District",
        "name_ja": "ならまち",
        "category": "sightseeing",
        "lat": 34.6795,
        "lng": 135.8390,
        "address_en": "Naramachi, Nara City, Nara",
        "address_ja": "奈良市ならまち",
        "tags": ["group", "sightseeing", "early-morning"],
        "crowd_notes": "Almost tourist-free before 10am. Preserved Edo-period merchant townhouses (machiya). Boutique cafes and craft shops.",
        "best_time_notes": "Before 10am for the streets. Most cafes open 10-11am — circle back after the deer park for a late-morning coffee and browse.",
        "source": "seed",
    },

    # ════════════════════════════════════════════
    # KYOTO (day trip from Osaka, date TBD)
    # ════════════════════════════════════════════

    {
        "city": "kyoto",
        "name_en": "Fushimi Inari Taisha",
        "name_ja": "伏見稲荷大社",
        "category": "sightseeing",
        "lat": 34.9671,
        "lng": 135.7727,
        "address_en": "68 Fukakusa Yabunouchi-cho, Fushimi-ku, Kyoto",
        "address_ja": "京都市伏見区深草藪之内町68",
        "tags": ["group", "sightseeing", "early-morning", "crowd-warning"],
        "crowd_notes": "Gates never close. By 9am the base torii is overrun with photographers. The upper mountain trails stay manageable even at 8am — most tourists turn back at the first shrine plateau.",
        "best_time_notes": "DAWN ONLY — 6am is otherworldly. The full trail to the summit takes 2+ hours; even just the first 30 min up is incredible before crowds. Accessible: Namba → Kintetsu to Tofukuji → JR to Inari (2 min walk to gates).",
        "source": "seed",
    },
    {
        "city": "kyoto",
        "name_en": "Arashiyama Bamboo Grove",
        "name_ja": "嵐山竹林",
        "category": "sightseeing",
        "lat": 35.0170,
        "lng": 135.6726,
        "address_en": "Sagaogurayama Tabuchiyama-cho, Ukyo-ku, Kyoto",
        "address_ja": "京都市右京区嵯峨小倉山田淵山町",
        "tags": ["group", "sightseeing", "early-morning", "crowd-warning"],
        "crowd_notes": "The 5-minute bamboo path is tourist-overrun by 10am. At 7am you may have it nearly to yourself.",
        "best_time_notes": "7am. The grove path is short (5-10 min walk) — pair with Tenryu-ji garden (opens 8:30am, 500 yen) and Okochi Sanso villa. Monkeys on the hillside at Iwatayama park nearby.",
        "source": "seed",
    },
    {
        "city": "kyoto",
        "name_en": "Philosopher's Path (Tetsugaku-no-Michi)",
        "name_ja": "哲学の道",
        "category": "sightseeing",
        "lat": 35.0148,
        "lng": 135.7944,
        "address_en": "Tetsugaku no Michi, Sakyo-ku, Kyoto",
        "address_ja": "京都市左京区哲学の道",
        "tags": ["group", "sightseeing", "cherry-blossom"],
        "crowd_notes": "Cherry blossom peak makes this one of Kyoto's most photographed spots. Morning is manageable; afternoon gets crowded.",
        "best_time_notes": "Morning walk during cherry blossom season. 2km canal-side path flanked by ~500 cherry trees. Leads from Nanzen-ji to Ginkaku-ji (Silver Pavilion).",
        "source": "seed",
    },
    {
        "city": "kyoto",
        "name_en": "Gion District (Hanamikoji-dori)",
        "name_ja": "祇園（花見小路通）",
        "category": "sightseeing",
        "lat": 35.0038,
        "lng": 135.7748,
        "address_en": "Gion, Higashiyama-ku, Kyoto",
        "address_ja": "京都市東山区祇園",
        "tags": ["group", "sightseeing", "evening"],
        "crowd_notes": "Midday is the worst — packed with selfie sticks. Dusk (6-8pm) is when Gion is atmospheric and most likely to spot geiko/maiko walking to appointments.",
        "best_time_notes": "DUSK — 6-8pm on Hanamikoji-dori. Do NOT block geiko or maiko — it is considered very rude and there are now signs prohibiting it. Just observe from the side of the street.",
        "source": "seed",
    },
    {
        "city": "kyoto",
        "name_en": "Kyoto International Manga Museum",
        "name_ja": "京都国際マンガミュージアム",
        "category": "entertainment",
        "lat": 35.0117,
        "lng": 135.7574,
        "address_en": "452 Kinbukicho, Nakagyo-ku, Kyoto 604-0846",
        "address_ja": "京都市中京区金吹町452 604-0846",
        "tags": ["madeline", "anime", "entertainment"],
        "crowd_notes": "Rarely crowded — good rainy day option. Extensive manga library you can read in the courtyard.",
        "best_time_notes": "Open 10am. Allow 2-3 hours. Madeline layer: rotating exhibitions, large manga archive (~300,000 volumes), cosplay events. Adults ~900 yen.",
        "source": "seed",
    },

    # ════════════════════════════════════════════
    # SAKAI (day trip from Osaka, date TBD)
    # ════════════════════════════════════════════

    {
        "city": "sakai",
        "name_en": "Sakai Knife District (Sakai-higashi area)",
        "name_ja": "堺刃物のまち（堺東エリア）",
        "category": "shopping",
        "lat": 34.5744,
        "lng": 135.4838,
        "address_en": "Sakai-higashi, Sakai City, Osaka Prefecture",
        "address_ja": "大阪府堺市堺区",
        "tags": ["todd", "knives", "craft"],
        "crowd_notes": "Not touristy — this is where professional chefs come to buy knives. Workshops and retail shops along the main knife street.",
        "best_time_notes": "Shops open ~10am. Allow half a day minimum. Todd: Japanese kitchen knives and nail/grooming kits in local Sakai steel are the primary targets. Specialist retailers will let you handle blades. Some shops offer custom engraving.",
        "source": "seed",
    },

    # ════════════════════════════════════════════
    # KANAZAWA
    # ════════════════════════════════════════════

    {
        "city": "kanazawa",
        "name_en": "Kenroku-en Garden",
        "name_ja": "兼六園",
        "category": "sightseeing",
        "lat": 36.5626,
        "lng": 136.6621,
        "address_en": "1 Kenrokumachi, Kanazawa, Ishikawa 920-0936",
        "address_ja": "石川県金沢市兼六町1 920-0936",
        "tags": ["group", "sightseeing", "cherry-blossom"],
        "crowd_notes": "One of Japan's three great gardens. Cherry blossoms may still be in peak late March-early April window — Kanazawa is slightly later than Osaka.",
        "best_time_notes": "Opens 7am in spring (free before 8am). Pair with Kanazawa Castle Park adjacent (no extra charge). The famous Kotoji lantern on the pond is the most photographed spot.",
        "source": "seed",
    },
    {
        "city": "kanazawa",
        "name_en": "Higashi Chaya District",
        "name_ja": "東茶屋街",
        "category": "sightseeing",
        "lat": 36.5705,
        "lng": 136.6638,
        "address_en": "Higashiyama 1-chome, Kanazawa, Ishikawa",
        "address_ja": "石川県金沢市東山1丁目",
        "tags": ["group", "todd", "sightseeing", "ceramics"],
        "crowd_notes": "Less crowded than Kyoto's equivalent geisha districts. Many Kutani ware ceramics shops on and around the main street.",
        "best_time_notes": "Morning (10am open). The preserved teahouse street is walkable in 30 min. Todd: multiple dedicated Kutani ware (九谷焼) retailers — look for bold overglaze enamel painting on porcelain. Some shops allow watching craftspeople.",
        "source": "seed",
    },
    {
        "city": "kanazawa",
        "name_en": "Omicho Market",
        "name_ja": "近江町市場",
        "category": "food",
        "lat": 36.5648,
        "lng": 136.6578,
        "address_en": "50 Kamiomicho, Kanazawa, Ishikawa 920-0906",
        "address_ja": "石川県金沢市上近江町50 920-0906",
        "tags": ["brenda", "group", "food", "seafood"],
        "crowd_notes": "Kanazawa is Japan Sea country — exceptional seafood quality, especially winter crab (zuwaigani) and yellowtail (buri/kanburi). Busiest 9-11am.",
        "best_time_notes": "Arrive 9am. Covered market with 170+ stalls. Brenda: outstanding fish and seafood options. Restaurant stalls inside offer sushi and kaisen-don (seafood rice bowls). Fresh crab to go or at seated restaurants.",
        "source": "seed",
    },
    {
        "city": "kanazawa",
        "name_en": "21st Century Museum of Contemporary Art",
        "name_ja": "金沢21世紀美術館",
        "category": "entertainment",
        "lat": 36.5620,
        "lng": 136.6604,
        "address_en": "1-2-1 Hirosaka, Kanazawa, Ishikawa 920-8509",
        "address_ja": "石川県金沢市広坂1-2-1 920-8509",
        "tags": ["group", "entertainment"],
        "crowd_notes": "Not typically crowded. Some permanent installations have timed entry (book at desk).",
        "best_time_notes": "Afternoon works well. Famous 'swimming pool' installation by Leandro Erlich — you stand underwater looking up through glass at people standing at the bottom of a drained pool. Free to enter main areas; paid zone ~360 yen.",
        "source": "seed",
    },

    # ════════════════════════════════════════════
    # TOKYO
    # ════════════════════════════════════════════

    {
        "city": "tokyo",
        "name_en": "Sugamo Jizo-dori Shotengai",
        "name_ja": "巣鴨地蔵通り商店街",
        "category": "shopping",
        "lat": 35.7333,
        "lng": 139.7295,
        "address_en": "Sugamo, Toshima-ku, Tokyo",
        "address_ja": "東京都豊島区巣鴨",
        "tags": ["group", "local", "shotengai"],
        "crowd_notes": "Known colloquially as 'harajuku for grandmas' — almost no foreign tourists, very local. Traditional sweets and daily goods.",
        "best_time_notes": "Morning from 9am. Pink daifuku mochi at Maruyama Sugamo is a local speciality. A 10-min morning stroll — the base is literally outside the Airbnb.",
        "source": "seed",
    },
    {
        "city": "tokyo",
        "name_en": "Ikebukuro — Animate, Pokemon Center, Jump Shop",
        "name_ja": "池袋（アニメイト、ポケモンセンター、ジャンプショップ）",
        "category": "entertainment",
        "lat": 35.7296,
        "lng": 139.7102,
        "address_en": "Ikebukuro, Toshima-ku, Tokyo",
        "address_ja": "東京都豊島区池袋",
        "tags": ["madeline", "todd", "anime", "entertainment"],
        "crowd_notes": "Animate flagship and Sunshine City complex are busiest on weekends. Weekday afternoon is better for browsing.",
        "best_time_notes": "Madeline primary zone. 1 stop from Sugamo on Yamanote or Mita Line. Animate flagship (anime merchandise), Pokemon Center (Sunshine City B1F), Jump Shop, also Sunshine Aquarium for a break. P'Parco building for more anime retailers.",
        "source": "seed",
    },
    {
        "city": "tokyo",
        "name_en": "Nakano Broadway",
        "name_ja": "中野ブロードウェイ",
        "category": "shopping",
        "lat": 35.7084,
        "lng": 139.6659,
        "address_en": "5-52-15 Nakano, Nakano-ku, Tokyo 164-0001",
        "address_ja": "東京都中野区中野5-52-15 164-0001",
        "tags": ["madeline", "todd", "anime", "cameras", "retro-gaming"],
        "crowd_notes": "Less tourist-overrun than Akihabara. This is where serious collectors shop. Mandarake has multiple floors dedicated to vintage anime figures, cameras, and retro games.",
        "best_time_notes": "Open 12pm-8pm. Mandarake floors 2-4 are the destination for both Todd and Madeline. Todd: vintage cameras and photo equipment on dedicated floors. Madeline: vintage anime figures and retro games. Route: Sugamo → Yamanote south → Shinjuku → JR Chuo/Sobu to Nakano (~25 min).",
        "source": "seed",
    },
    {
        "city": "tokyo",
        "name_en": "Shimokitazawa — Vintage and Thrift District",
        "name_ja": "下北沢（古着）",
        "category": "shopping",
        "lat": 35.6613,
        "lng": 139.6677,
        "address_en": "Shimokitazawa, Setagaya-ku, Tokyo",
        "address_ja": "東京都世田谷区下北沢",
        "tags": ["madeline", "vintage", "shopping"],
        "crowd_notes": "Tokyo's indie/vintage fashion district. Very local vibe — multiple blocks of used clothing boutiques, record shops, and independent cafes. Weekends busy but manageable vs. Harajuku.",
        "best_time_notes": "Afternoon — most vintage shops open 12pm-1pm. Allow 2-3 hours minimum. Madeline: primary destination for thrift/used clothing. Cat Street (parallel lane) has higher-end vintage. Route: Sugamo → Yamanote to Shibuya → Keio Inokashira Line to Shimokitazawa (~40 min).",
        "source": "seed",
    },
    {
        "city": "tokyo",
        "name_en": "Akihabara Electric Town",
        "name_ja": "秋葉原電気街",
        "category": "shopping",
        "lat": 35.6984,
        "lng": 139.7730,
        "address_en": "Sotokanda, Chiyoda-ku, Tokyo",
        "address_ja": "東京都千代田区外神田",
        "tags": ["todd", "madeline", "electronics", "anime", "retro-gaming", "cameras"],
        "crowd_notes": "Main Chuo-dori strip is tourist-heavy. The maker electronics shops (Akizuki, Marutsu, Aitendo) are 2 blocks off the main strip — far less crowded.",
        "best_time_notes": "Todd MUST-VISIT: Akizuki Denshi (秋月電子通商) and Marutsu Denki (マルツ電波) for ESP32/sensors/kits — open ~11am, weekday preferred. Aitendo nearby for modules. Madeline: Super Potato (3F/4F area, retro gaming) and Animate Akihabara. Route: Sugamo → Yamanote to Akihabara (~20 min).",
        "source": "seed",
    },
    {
        "city": "tokyo",
        "name_en": "Harajuku Takeshita Street",
        "name_ja": "原宿竹下通り",
        "category": "shopping",
        "lat": 35.6703,
        "lng": 139.7076,
        "address_en": "Jingumae 1-chome, Shibuya-ku, Tokyo",
        "address_ja": "東京都渋谷区神宮前1丁目",
        "tags": ["madeline", "vintage", "fashion"],
        "crowd_notes": "Extremely packed on weekends — nearly impassable. Weekday morning is the only manageable time. Very short street (~350m).",
        "best_time_notes": "Weekday morning only. Cat Street (parallel, runs behind Omotesando) is calmer and has better quality vintage shops. Harajuku station on Yamanote. Combine with Omotesando for a broader browse.",
        "source": "seed",
    },
    {
        "city": "tokyo",
        "name_en": "Asakusa Senso-ji Temple",
        "name_ja": "浅草寺",
        "category": "sightseeing",
        "lat": 35.7148,
        "lng": 139.7967,
        "address_en": "2-3-1 Asakusa, Taito-ku, Tokyo 111-0032",
        "address_ja": "東京都台東区浅草2-3-1 111-0032",
        "tags": ["group", "sightseeing", "early-morning", "crowd-warning"],
        "crowd_notes": "Tokyo's most visited temple. 6am-8am is peaceful — the grounds never close. After 10am it becomes extremely crowded with tour groups.",
        "best_time_notes": "Early morning (6am) for photos without crowds. Nakamise shopping street opens ~10am (great for souvenirs and Japanese snacks). Combine with Kappabashi-dori (cookware street, 5 min walk) — Brenda and Todd both relevant.",
        "source": "seed",
    },
    {
        "city": "tokyo",
        "name_en": "Ghibli Museum, Mitaka",
        "name_ja": "三鷹の森ジブリ美術館",
        "category": "entertainment",
        "lat": 35.6962,
        "lng": 139.5703,
        "address_en": "1-1-83 Shimorenjaku, Mitaka, Tokyo 181-0013",
        "address_ja": "東京都三鷹市下連雀1-1-83 181-0013",
        "tags": ["madeline", "todd", "ghibli", "anime", "entertainment"],
        "crowd_notes": "TIMED ENTRY ONLY — must buy tickets in advance. No re-entry. Booking: 7961560155 (noon Apr 3). The museum is small and magical — built by Miyazaki Hayao, every corner is designed.",
        "best_time_notes": "BOOKING: 7961560155. Entry noon Apr 3. Depart Sugamo by 10:45am. Route: Yamanote to Shinjuku → JR Chuo rapid to Mitaka (20 min) → 10 min walk to museum (or shuttle bus 200 yen from south exit). The rooftop robot soldier from Castle in the Sky is real and on the roof.",
        "source": "seed",
    },
    {
        "city": "tokyo",
        "name_en": "Map Camera, Shinjuku",
        "name_ja": "マップカメラ（新宿）",
        "category": "shopping",
        "lat": 35.6932,
        "lng": 139.7031,
        "address_en": "1-12-2 Nishishinjuku, Shinjuku-ku, Tokyo",
        "address_ja": "東京都新宿区西新宿1-12-2",
        "tags": ["todd", "madeline", "cameras"],
        "crowd_notes": "Japan's largest used camera dealer. 5 floors — not typically crowded. Staff knowledgeable.",
        "best_time_notes": "Open 11am-8pm. Todd + Madeline: vintage point-and-shoot cameras are a specialty. Near Shinjuku station west exit (5 min walk). Yodobashi Camera and Bic Camera also nearby if looking for new gear.",
        "source": "seed",
    },
    {
        "city": "tokyo",
        "name_en": "Shibuya Crossing and Shibuya Scramble",
        "name_ja": "渋谷スクランブル交差点",
        "category": "sightseeing",
        "lat": 35.6595,
        "lng": 139.7004,
        "address_en": "Shibuya, Shibuya-ku, Tokyo",
        "address_ja": "東京都渋谷区渋谷",
        "tags": ["group", "sightseeing"],
        "crowd_notes": "Busiest intersection in the world. Best viewed from above — Mag's Park rooftop (free) or Starbucks Reserve Roastery second floor.",
        "best_time_notes": "Evening for the light show effect. Daytime is still impressive. Good transit hub for Madeline (Shibuya → Keio Inokashira to Shimokitazawa). Also Shibuya 109 for Madeline's fashion interest.",
        "source": "seed",
    },
]


def main():
    conn = psycopg2.connect(**conn_params)
    psycopg2.extras.register_default_jsonb(conn)
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM trip_pois")
            print("Cleared trip_pois.")

            by_city: dict[str, int] = {}
            for poi in POIS:
                cur.execute(
                    """
                    INSERT INTO trip_pois
                        (city, name_en, name_ja, category, lat, lng,
                         address_en, address_ja, tags, crowd_notes, best_time_notes, source)
                    VALUES
                        (%(city)s, %(name_en)s, %(name_ja)s, %(category)s, %(lat)s, %(lng)s,
                         %(address_en)s, %(address_ja)s, %(tags)s, %(crowd_notes)s, %(best_time_notes)s, %(source)s)
                    """,
                    {
                        "name_ja": None, "lat": None, "lng": None,
                        "address_en": None, "address_ja": None,
                        "crowd_notes": None, "best_time_notes": None, "source": None,
                        **poi,
                    },
                )
                city = poi["city"]
                by_city[city] = by_city.get(city, 0) + 1
                print(f"  [{city:10s}] {poi['name_en']}")

        conn.commit()
        print(f"\n✅ Inserted {len(POIS)} POIs across {len(by_city)} cities:")
        for city, count in sorted(by_city.items()):
            print(f"       {city:12s}: {count}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
