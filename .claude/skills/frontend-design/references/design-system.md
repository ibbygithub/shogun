# Shogun Design System -- Detailed Reference

This file provides concrete code examples for building Shogun UI components.
The existing codebase uses **inline styles** as the primary styling approach,
with CSS classes reserved for layout shell, theme transitions, and leg-type badges.

---

## Color Palette -- Complete Reference

### CSS Custom Properties (defined in globals.css)

```css
/* Base/default theme */
--city-primary:   #1a1a2e;
--city-accent:    #c0392b;
--city-highlight: #f39c12;
--city-surface:   #f5f5f5;

/* Tokyo */
--city-primary:   #0d1b2e;   /* midnight navy */
--city-accent:    #e91e8c;   /* neon magenta */
--city-highlight: #00d4ff;   /* cyan */
--city-surface:   #f0f4ff;   /* ice blue */

/* Nara */
--city-primary:   #2d3a1e;   /* deep forest */
--city-accent:    #8b6914;   /* amber gold */
--city-highlight: #c4956a;   /* sand */
--city-surface:   #f7f3ec;   /* warm cream */

/* Osaka */
--city-primary:   #1a0a00;   /* burnt black */
--city-accent:    #ff4500;   /* neon orange */
--city-highlight: #f5c518;   /* golden */
--city-surface:   #fff8f0;   /* warm white */

/* Kyoto */
--city-primary:   #1a0f0a;   /* dark lacquer */
--city-accent:    #8b1a1a;   /* deep crimson */
--city-highlight: #f7b8c4;   /* sakura pink */
--city-surface:   #faf6f0;   /* soft cream */
```

### Tailwind Bridge Classes (from tailwind.config.js)

```
bg-city-primary    text-city-primary    border-city-primary
bg-city-accent     text-city-accent     border-city-accent
bg-city-highlight  text-city-highlight  border-city-highlight
bg-city-surface    text-city-surface    border-city-surface
```

### Fixed Color Tokens

```
/* Text hierarchy */
#111827  -- primary text (headings, titles)
#4b5563  -- body text
#6b7280  -- secondary text
#94a3b8  -- muted/placeholder text

/* On-dark text (sidebar, heroes, dark cards) */
white                       -- primary
rgba(255,255,255,0.75)      -- secondary
rgba(255,255,255,0.65)      -- labels
rgba(255,255,255,0.5)       -- muted
rgba(255,255,255,0.35-0.4)  -- section headers
rgba(255,255,255,0.1)       -- divider lines

/* Semantic */
#10b981  -- success green (checkmarks)
#1d4ed8  -- link blue
#3b82f6  -- info blue (rain indicator)
#d97706  -- warning amber
#991b1b  -- error red

/* Surfaces */
#f9fafb  -- page background
white    -- card background
#f8fafc  -- subtle card fill (forecast tiles)
#f1f5f9  -- empty/TBD state fill
```

---

## Component Code Snippets

### Standard White Card

```tsx
<div style={{
  background: "white",
  borderRadius: "12px",
  padding: "1rem",
  boxShadow: "0 1px 3px rgba(0,0,0,0.08)",
}}>
  <h2 style={{ fontWeight: 700, fontSize: "0.9rem", marginBottom: "0.75rem" }}>
    Card Title
  </h2>
  {/* Card content */}
</div>
```

### Gradient Status Card (city-themed)

```tsx
<div style={{
  background: "linear-gradient(135deg, var(--city-primary), color-mix(in srgb, var(--city-primary) 70%, var(--city-accent)))",
  borderRadius: "12px",
  padding: "1.25rem",
  color: "white",
}}>
  <div style={{
    fontSize: "0.75rem",
    color: "rgba(255,255,255,0.65)",
    textTransform: "uppercase",
    letterSpacing: "0.08em",
  }}>
    Label
  </div>
  <div style={{ fontSize: "1.75rem", fontWeight: 800, marginTop: "0.25rem" }}>
    Main Value
  </div>
  <div style={{ fontSize: "0.875rem", color: "rgba(255,255,255,0.75)", marginTop: "0.25rem" }}>
    Supporting text
  </div>
</div>
```

### Data Tile (compact dashboard widget)

```tsx
<div style={{
  background: "white",
  borderRadius: "12px",
  padding: "1rem",
  boxShadow: "0 1px 3px rgba(0,0,0,0.08)",
}}>
  <div style={{
    fontSize: "0.7rem",
    color: "#94a3b8",
    marginBottom: "0.5rem",
    textTransform: "uppercase",
    letterSpacing: "0.06em",
  }}>
    Widget Label
  </div>
  <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
    <span style={{ fontSize: "2.25rem" }}>🌡️</span>
    <div>
      <div style={{ fontSize: "1.75rem", fontWeight: 700, lineHeight: 1 }}>42</div>
      <div style={{ fontSize: "0.85rem", color: "#6b7280", lineHeight: 1.2 }}>units</div>
    </div>
  </div>
</div>
```

### POI Card (city-pastel background)

```tsx
const CITY_BG: Record<string, string> = {
  osaka: "#FFF0E6",
  nara: "#E8F5E9",
  kanazawa: "#FFF8E1",
  tokyo: "#EEF2FF",
  kyoto: "#FCE4EC",
};

<div style={{
  background: CITY_BG[city] || "#F5F5F5",
  borderRadius: "10px",
  padding: "0.875rem",
  boxShadow: "0 1px 3px rgba(0,0,0,0.07)",
  cursor: "pointer",
  transition: "transform 0.15s, box-shadow 0.15s",
}}>
  {/* Category badge */}
  <span style={{
    display: "inline-block",
    fontSize: "0.7rem",
    fontWeight: 700,
    background: "#FED7AA",
    color: "#9A3412",
    padding: "3px 10px",
    borderRadius: "9999px",
    letterSpacing: "0.02em",
    textTransform: "capitalize",
  }}>
    Restaurant
  </span>

  <div style={{ fontWeight: 700, fontSize: "0.95rem", color: "#111827", marginTop: "0.4rem" }}>
    Place Name
  </div>
  <div style={{ fontSize: "0.8rem", color: "#6b7280" }}>
    日本語の名前
  </div>
  <p style={{
    marginTop: "0.4rem",
    fontSize: "0.8rem",
    color: "#4b5563",
    lineHeight: 1.4,
    display: "-webkit-box",
    WebkitLineClamp: 2,
    WebkitBoxOrient: "vertical",
    overflow: "hidden",
  }}>
    Description text truncated to two lines...
  </p>
</div>
```

### Tag Chip

```tsx
<span style={{
  fontSize: "0.7rem",
  background: "rgba(255,255,255,0.65)",
  color: "#1d4ed8",
  padding: "2px 6px",
  borderRadius: "4px",
}}>
  tag-name
</span>
```

### City Pill Badge

```tsx
<span style={{
  fontSize: "0.7rem",
  background: "rgba(255,255,255,0.7)",
  color: "#475569",
  padding: "2px 8px",
  borderRadius: "9999px",
  whiteSpace: "nowrap",
}}>
  osaka
</span>
```

### Primary CTA Button (pill)

```tsx
<a href="/target" style={{
  display: "inline-block",
  background: "var(--city-accent)",
  color: "white",
  padding: "0.75rem 2rem",
  borderRadius: "9999px",
  fontWeight: 700,
  fontSize: "0.95rem",
  textDecoration: "none",
}}>
  Action Label
</a>
```

### Compact Action Button

```tsx
<button style={{
  fontSize: "0.72rem",
  fontWeight: 600,
  background: "rgba(255,255,255,0.75)",
  color: "#374151",
  border: "1px solid rgba(0,0,0,0.1)",
  borderRadius: "6px",
  padding: "3px 10px",
  cursor: "pointer",
  transition: "background 0.2s, color 0.2s",
}}>
  Save
</button>
```

### Inline Note/Callout

```tsx
<div style={{
  marginTop: "0.375rem",
  fontSize: "0.8rem",
  background: "#fef9c3",
  borderRadius: 4,
  padding: "4px 8px",
  color: "#92400e",
}}>
  Note text here
</div>
```

### Warning Banner

```tsx
<div style={{
  padding: "1rem",
  background: "#fff7ed",
  borderRadius: "12px",
  color: "#9a3412",
  fontSize: "0.85rem",
  border: "1px solid #fed7aa",
  marginBottom: "1rem",
}}>
  Warning message
</div>
```

### Error Card

```tsx
<div style={{
  background: "#fee2e2",
  borderRadius: "12px",
  padding: "1rem",
  color: "#991b1b",
  fontSize: "0.85rem",
}}>
  Error description
</div>
```

### Loading Placeholder

```tsx
<div style={{
  background: "white",
  borderRadius: "12px",
  padding: "1rem",
  boxShadow: "0 1px 3px rgba(0,0,0,0.08)",
  minHeight: "140px",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  color: "#94a3b8",
  fontSize: "0.85rem",
}}>
  Loading data...
</div>
```

### Navigation Link (sidebar, on dark background)

```tsx
<a href="/page" style={{
  display: "flex",
  alignItems: "center",
  gap: "0.625rem",
  padding: "0.625rem 1rem",
  color: active ? "white" : "rgba(255,255,255,0.65)",
  background: active ? "rgba(255,255,255,0.12)" : "transparent",
  textDecoration: "none",
  fontSize: "0.875rem",
  fontWeight: active ? 600 : 400,
  borderRight: active ? "3px solid var(--city-highlight)" : "3px solid transparent",
  transition: "all 0.15s",
}}>
  <span>icon</span>
  Label
</a>
```

### Section Label (on dark background)

```tsx
<div style={{
  padding: "0.6rem 1rem 0.25rem",
  fontSize: "0.65rem",
  color: "rgba(255,255,255,0.35)",
  textTransform: "uppercase",
  letterSpacing: "0.08em",
  marginTop: "0.25rem",
}}>
  Section Name
</div>
```

### Section Label (on light background)

```tsx
<div style={{
  fontSize: "0.7rem",
  color: "#94a3b8",
  marginBottom: "0.5rem",
  textTransform: "uppercase",
  letterSpacing: "0.06em",
}}>
  Widget Label
</div>
```

---

## Page Layout Templates

### Standard Page

```tsx
export default function MyPage() {
  return (
    <div style={{ padding: "1.5rem", maxWidth: "900px" }}>
      <h1 style={{ fontSize: "1.5rem", fontWeight: 900, marginBottom: "1.25rem" }}>
        Page Title
      </h1>

      {/* Two-column grid for tiles */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem", marginBottom: "1rem" }}>
        {/* Tile components */}
      </div>

      {/* Full-width section */}
      <div style={{ marginBottom: "1rem" }}>
        {/* Content */}
      </div>

      {/* Card section */}
      <div style={{
        background: "white",
        borderRadius: "12px",
        padding: "1rem",
        boxShadow: "0 1px 3px rgba(0,0,0,0.06)",
      }}>
        <h2 style={{ fontWeight: 700, fontSize: "0.9rem", marginBottom: "0.75rem" }}>
          Section Title
        </h2>
        {/* Section content */}
      </div>
    </div>
  );
}
```

### City Page Layout

```tsx
export default async function CityPage({ params }: { params: { slug: string } }) {
  const slug = params.slug as CitySlug;
  const city = CITIES[slug];

  return (
    <div>
      {/* Theme switcher + hero -- full-bleed, no padding */}
      <CityTheme slug={slug} />
      <CityHero slug={slug} />

      {/* Content area -- padded, max-width */}
      <div style={{ padding: "1.5rem", maxWidth: "1100px" }}>

        {/* Map + POI split (desktop: side-by-side, mobile: stacked) */}
        <div style={{ marginBottom: "1.5rem" }}>
          <h2 style={{ fontWeight: 700, marginBottom: "0.75rem" }}>
            Places in {city.name}
          </h2>
          <div className="city-map-grid" style={{ display: "grid", gap: "1rem" }}>
            {/* POI card grid */}
            <div style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fill, minmax(240px, 1fr))",
              gap: "0.75rem",
            }}>
              {/* PoiCard components */}
            </div>
            {/* Map (sticky on desktop) */}
            <div style={{ position: "sticky", top: "1rem" }}>
              {/* Map component */}
            </div>
          </div>
        </div>

        {/* Context strip -- two-column */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem", marginBottom: "1rem" }}>
          {/* Weather, blossom, etc. */}
        </div>

        {/* CTA */}
        <div style={{ marginTop: "1.5rem", textAlign: "center" }}>
          <a href="/chat" style={{
            display: "inline-block",
            background: "var(--city-accent)",
            color: "white",
            padding: "0.75rem 2rem",
            borderRadius: "9999px",
            fontWeight: 700,
            fontSize: "0.95rem",
            textDecoration: "none",
          }}>
            Ask Shogun about {city.name}
          </a>
        </div>
      </div>
    </div>
  );
}
```

### Dashboard Tile Grid

```tsx
{/* Hero tiles -- gradient, full theme */}
<div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem", marginBottom: "1rem" }}>
  <TripStatusCard />
  <ShogunHealthCard />
</div>

{/* Ambient data -- weather + stacked small tiles */}
<div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.75rem", marginBottom: "0.75rem" }}>
  <WeatherCard data={weather} />
  <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
    <AqiBadge data={aqi} />
    <ExchangeRate data={exchange} />
    <TransitAlert data={transit} />
  </div>
</div>
```

---

## Responsive Breakpoints

| Breakpoint | Behavior |
|-----------|----------|
| `max-width: 768px` | Sidebar hidden, bottom tab bar shown, main content gets bottom padding (60px) |
| `min-width: 769px` | Sidebar shown (240px), tab bar hidden |
| `max-width: 767px` | City map grid stacks vertically, map moves to top (order: -1) |

### Responsive Grid Pattern (CSS-in-JSX)

```tsx
<style>{`
  .my-grid {
    grid-template-columns: 1fr 1fr;
  }
  @media (max-width: 767px) {
    .my-grid {
      grid-template-columns: 1fr;
    }
  }
`}</style>
```

---

## Icon Usage

The current codebase uses **emoji** as the primary icon system. Maintain this for consistency.

### Navigation Icons
| Page | Emoji |
|------|-------|
| Dashboard | `\U0001F3E0` |
| Calendar | `\U0001F4C5` |
| Planning | `\U0001F4CB` |
| Itinerary | `\U0001F5FA` |
| Places | `\U0001F4CD` |
| Chat | `\U0001F4AC` |
| Wishlist | `\U2B50` |
| Phrases | `\U0001F5E3` |
| Transit | `\U0001F686` |
| Checklist | `\U2705` |
| Budget | `\U0001F4B4` |
| Settings | `\U2699` |
| Admin | `\U0001F527` |

### Data/Content Icons
| Concept | Emoji |
|---------|-------|
| Time/clock | `\U23F0` |
| Rain/precipitation | `\U0001F4A7` |
| Note/memo | `\U0001F4DD` |
| Copy | `\U0001F4CB` |
| Success check | `\U2713` (text, not emoji) styled green |
| Trip complete | `\U0001F38C` |
| Save/favorite | `\U2B50` |

### Leg Type Icons
| Type | Label Format |
|------|-------------|
| Flight | `\U2708 Flight` |
| Hotel | `\U0001F3E8 Hotel` |
| Activity | `\U0001F3AF Activity` |
| Transit | `\U0001F683 Transit` |
| Restaurant | `\U0001F35C Restaurant` |

### Weather Icons (WMO codes)
| Condition | Emoji |
|-----------|-------|
| Clear | `\U2600` |
| Mainly clear | `\U0001F324` |
| Partly cloudy | `\U26C5` |
| Overcast | `\U2601` |
| Fog | `\U0001F32B` |
| Drizzle/light rain | `\U0001F326` |
| Rain | `\U0001F327` |
| Snow | `\U0001F328` / `\U2744` |
| Thunderstorm | `\U26C8` |

---

## Adding a New Page

1. Create the page file at `src/app/(app)/my-page/page.tsx`
2. The `(app)` layout group automatically provides the sidebar + mobile tab bar
3. Use the standard page template (see above)
4. If city-specific, use `CityTheme` component and `var(--city-*)` properties
5. Add navigation entry in both `Sidebar.tsx` (MAIN_NAV, TOOLS_NAV, or ADMIN_NAV) and `MobileTabBar.tsx` (TABS)
6. Keep styling consistent: inline styles, 12px border-radius cards, system font stack

## Adding a New Widget/Tile

1. Create component at `src/components/<category>/MyWidget.tsx`
2. Accept data as props (fetched by parent page or dashboard)
3. Use the standard card wrapper (white, rounded-12, padded, shadowed)
4. Include a loading state (centered muted text) and error state (red or amber card)
5. Use the section label pattern for the widget title (uppercase, small, muted)
6. Data values should be prominent (large font weight 700) with supporting text smaller and muted

## Adding a New Card to a City Page

1. Import component in `src/app/(app)/city/[slug]/page.tsx`
2. Place within the padded content area (`maxWidth: 1100px`)
3. Use `var(--city-accent)` for accent elements so it adapts to city theme
4. Follow the existing card wrapper pattern
5. Consider two-column grid placement vs full-width based on content density

---

## Key Files Reference

| File | Purpose |
|------|---------|
| `src/app/globals.css` | Theme variables, shell layout, leg/badge CSS classes |
| `src/lib/cities.ts` | City config: names, kanji, dates, theme colors, coordinates |
| `tailwind.config.js` | Tailwind bridge for CSS custom properties |
| `src/app/(app)/layout.tsx` | App shell: sidebar + main + mobile tab bar |
| `src/components/layout/Sidebar.tsx` | Desktop navigation |
| `src/components/layout/MobileTabBar.tsx` | Mobile bottom navigation |
| `src/components/city/CityTheme.tsx` | Sets `data-city` attribute for theme switching |
| `src/components/city/CityHero.tsx` | City page hero with gradient, kanji, landmark SVG |
| `src/components/pois/PoiCard.tsx` | POI card with city pastel bg, category badges, tags |
| `src/components/ambient/AmbientDashboard.tsx` | Dashboard ambient data grid layout |
| `src/components/ambient/WeatherCard.tsx` | Weather tile with current + 3-day forecast |
| `src/components/widgets/TripStatusCard.tsx` | Gradient countdown/status card |
