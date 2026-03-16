# Shogun Web — Per-City Visual Theme Specification
Date: 2026-03-13
Status: Approved

Each city gets a unique themed entry/landing page at `/city/[slug]`.
The base design system (navy, torii red, gold, warm white) applies globally.
Each city theme overlays a city-specific color accent, hero concept, and mood
on top of the base system. These are CSS variable overrides — one block per city,
no new components needed.

The overall UI aesthetic is **traditional Japanese architecture meets modern
digital dashboard** — wood grain textures, shoji screen geometry, torii gate
shapes as structural elements. The sidebar evokes a shogun house entry corridor.

---

## Cities with Themed Pages

### 1. Tokyo
**Route:** `/city/tokyo`
**Slug:** `tokyo`
**Dates:** Mar 23–31 (8 nights — first city, arrival)

**Mood:** Arrival. Anticipation. Electric energy meeting ancient stillness.

**City color overrides:**
```css
/* City: Tokyo */
--city-primary:   #0d1b2e;   /* deep midnight — Shibuya at 3am */
--city-accent:    #e91e8c;   /* neon magenta — Shibuya crossing LED screens */
--city-highlight: #00d4ff;   /* electric blue — pachinko, neon reflections */
--city-surface:   #f0f4ff;   /* cool white with blue tinge */
```

**Hero concept:**
Shibuya Crossing at dusk — dark asphalt reflecting neon signs, crowds blurred
in motion. Foreground: the silhouette of a traditional torii gate frame composited
into the crossing geometry. The contrast between ancient form and modern chaos
is the visual statement. Cherry blossoms in the upper right quadrant (trip timing
— peak bloom is late March).

**Key symbols to incorporate:**
- Shibuya crossing scramble (motion lines in CSS or SVG)
- Tokyo Tower (red and white — echoes torii red)
- Senso-ji temple gate (Asakusa — traditional counterpoint)
- Cherry blossoms against neon
- Tokyo Skytree silhouette

**Entry page sections:**
1. Hero with neon overlay and Tokyo at night
2. Trip context card: "Day 1 of 8 in Tokyo — Arriving Mar 23"
3. Current blossom status (peak expected late March)
4. Weather strip (current + 3-day)
5. "Today in Tokyo" — day's itinerary teaser
6. Top Tokyo POIs (cards with EN + JA names)
7. Chat CTA: "Ask Shogun about Tokyo →"

**Tone copy direction:** Bold, first-sentence excitement. "You've landed. 34 million
people, 13,000 restaurants, 900 years of temple history. Let's start."

---

### 2. Nara
**Route:** `/city/nara`
**Slug:** `nara`
**Dates:** Apr 1–2 (2 nights)

**Mood:** Quiet. Ancient. Deer walk where emperors walked.

**City color overrides:**
```css
/* City: Nara */
--city-primary:   #2d3a1e;   /* deep forest green — Kasuga Taisha cedar forest */
--city-accent:    #8b6914;   /* antique gold — temple bronzework, lanterns */
--city-highlight: #c4956a;   /* warm terra — deer, stone lanterns, old wood */
--city-surface:   #f7f3ec;   /* aged paper white */
```

**Hero concept:**
A lone deer in late afternoon golden light, standing in front of the Nandaimon
Great South Gate of Todaiji Temple. Depth of field soft behind the deer. The gate's
massive wooden pillars frame the composition. Cherry blossom petals (early April
— late peak for Nara) falling across the frame. Warm amber hour light.

**Key symbols to incorporate:**
- Sika deer (protected, 1,200+ roam freely)
- Todaiji Temple — Daibutsuden (largest wooden structure in the world)
- Kasuga Taisha stone lanterns — hundreds lining the path
- Nandaimon gate guardian statues (Nio)
- Great Buddha (Daibutsu) — 15 meters tall

**Entry page sections:**
1. Hero: deer + Todaiji gate, golden hour
2. Trip context card: "Day 9–10 — Nara, Apr 1–2"
3. Blossom status (late season, Mt. Yoshino cherry blossoms nearby)
4. Weather strip
5. Practical reminder card: "Bring your passport — Todaiji museum requires ID"
6. Top Nara POIs (Todaiji, Kasuga Taisha, Nara Park, Yoshikien Garden)
7. Chat CTA: "Ask Shogun about Nara →"

**Tone copy direction:** Reverent, quiet wonder. "Nara has been Japan's sacred
heart for 1,300 years. The deer are not a tourist attraction — they are residents
with legal protection older than most nations."

---

### 3. Osaka
**Route:** `/city/osaka`
**Slug:** `osaka`
**Dates:** Apr 3–6 (~4 nights)

**Mood:** Loud. Delicious. Unapologetically alive. Japan's kitchen.

**City color overrides:**
```css
/* City: Osaka */
--city-primary:   #1a0a00;   /* deep black — Dotonbori canal at night */
--city-accent:    #ff4500;   /* vivid red-orange — Glico man, takoyaki stalls */
--city-highlight: #f5c518;   /* bright yellow — lanterns, yakitori glaze */
--city-surface:   #fff8f0;   /* warm cream — street food glow */
```

**Hero concept:**
Dotonbori canal at night — the iconic neon corridor reflected in still water.
The Glico running man billboard dominant in frame. Massive mechanical crab and
puffer fish signs of the restaurant strip. Warm food glow from street stalls.
A sense of abundance and noise. Cherry blossoms on the canal banks (early April
— Osaka Castle Park peak bloom).

**Key symbols to incorporate:**
- Dotonbori canal and neon signs
- Glico running man (45m LED billboard)
- Takoyaki — octopus balls (Osaka's signature dish)
- Osaka Castle — daytime counterpoint
- Kuromon Ichiba market (Osaka's kitchen)

**Entry page sections:**
1. Hero: Dotonbori at night, neon reflections
2. Trip context card: "Day 11–14 — Osaka, Apr 3–6"
3. Blossom status (Osaka Castle Park peak bloom — early April)
4. Weather strip
5. Food reminders: "Osaka rule: eat standing. Takoyaki at Aizuya. Kushikatsu at Daruma."
6. Top Osaka POIs (Dotonbori, Osaka Castle, Kuromon, Den Den Town)
7. Chat CTA: "Ask Shogun for dinner tonight in Osaka →"

**Tone copy direction:** Enthusiastic, food-forward, loud energy. "Osaka's civic
pride is its food. Locals eat out 14 times a week on average. You're going to
eat more here than anywhere else. This is correct."

---

### 4. Kyoto
**Route:** `/city/kyoto`
**Slug:** `kyoto`
**Dates:** Apr 6–9 (~3 nights — final city before departure)

**Mood:** Ceremonial. Refined. The Japan that people imagine before they arrive.

**City color overrides:**
```css
/* City: Kyoto */
--city-primary:   #1a0f0a;   /* ink black — traditional lacquerware */
--city-accent:    #8b1a1a;   /* deep vermilion — Fushimi Inari torii gates */
--city-highlight: #f7b8c4;   /* sakura pink — late bloom, Maruyama Park */
--city-surface:   #faf6f0;   /* aged silk white */
```

**Hero concept:**
The tunnel of torii gates at Fushimi Inari-taisha — thousands of vermilion gates
creating an infinite corridor up the mountain. Dawn light, the gates glowing
orange-red against dark cedar forest. A lone figure (silhouette) walking into
the depth of the tunnel. This is the image most associated with Japan worldwide —
and it belongs specifically to Kyoto. Late cherry blossoms visible at the base.

**Key symbols to incorporate:**
- Fushimi Inari torii gate tunnel (the iconic image)
- Arashiyama bamboo grove
- Kinkaku-ji (Golden Pavilion) reflected in Kyoko-chi pond
- Geisha district — Gion's stone lantern streets
- Nijo Castle — the shogun's Kyoto residence (most relevant to the Shogun brand)

**Entry page sections:**
1. Hero: Fushimi Inari torii tunnel at dawn
2. Trip context card: "Day 15–17 — Kyoto, Apr 6–9 (final city)"
3. Late blossom status (Maruyama Park — last bloom of the trip)
4. Weather strip
5. "Final days" mood section — reflective, unhurried pace
6. Top Kyoto POIs (Fushimi Inari, Kinkaku-ji, Arashiyama, Gion, Nijo Castle)
7. Practical: "Nijo Castle — the Shogun's palace. This is where the name comes from."
8. Chat CTA: "Ask Shogun about your last days in Japan →"

**Tone copy direction:** Contemplative, respectful of endings. "Japan's ancient
capital for 1,000 years. 1,600 Buddhist temples. 400 Shinto shrines. Three days
is not enough. It never is."

---

## Day-Trip Cities (POI tabs only, no full themed pages)

### Sakai
**Tab in /pois:** Yes
**Theme:** Artisan heritage, kofun burial mounds, forged steel. Dark earth tones.
**Key POIs:** Daisen Kofun (largest burial mound in Japan), traditional cutlery district

### Kanazawa
**Tab in /pois:** Yes (if POI data exists)
**Theme:** "Little Kyoto" — samurai heritage, Kenroku-en garden, preserved districts
**Key POIs:** Kenroku-en (one of Japan's top 3 gardens), samurai district, geisha district

---

## Per-City CSS Override Pattern

Each city page imports the base globals.css and applies a `[data-city="tokyo"]`
attribute override block. No new components — the existing card, hero, and widget
components read CSS variables automatically.

```css
/* Pattern for per-city overrides */
[data-city="tokyo"] {
  --city-primary:   #0d1b2e;
  --city-accent:    #e91e8c;
  --city-highlight: #00d4ff;
  --city-surface:   #f0f4ff;
}

[data-city="nara"] {
  --city-primary:   #2d3a1e;
  --city-accent:    #8b6914;
  --city-highlight: #c4956a;
  --city-surface:   #f7f3ec;
}

[data-city="osaka"] {
  --city-primary:   #1a0a00;
  --city-accent:    #ff4500;
  --city-highlight: #f5c518;
  --city-surface:   #fff8f0;
}

[data-city="kyoto"] {
  --city-primary:   #1a0f0a;
  --city-accent:    #8b1a1a;
  --city-highlight: #f7b8c4;
  --city-surface:   #faf6f0;
}
```

City pages set this attribute on the `<main>` or `<section>` wrapper.
The rest is automatic.

---

## Hero Image Strategy

No external image dependencies for MVP. Use CSS gradient + SVG illustration
layers as the hero approach — fast load, no CDN, no broken images.

Each city hero = a layered CSS composition:
1. **Base layer:** CSS gradient (city color palette, directional)
2. **Silhouette layer:** SVG of the key landmark (Torii gate, Todaiji, Dotonbori sign, Fushimi Inari)
3. **Texture layer:** CSS noise or paper grain overlay (subtle, city-appropriate)
4. **Typography layer:** City name in large bold + Japanese kanji (東京, 奈良, 大阪, 京都)

This renders perfectly with no external requests. When actual photos are available
(after the trip, family photo uploads), they can replace the base layer.

### City kanji for header display:
- Tokyo: 東京
- Nara: 奈良
- Osaka: 大阪
- Kyoto: 京都
- Sakai: 堺
- Kanazawa: 金沢
