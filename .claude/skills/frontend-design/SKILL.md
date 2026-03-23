---
name: frontend-design
description: Design system knowledge for building beautiful Shogun web UI components. Provides color palettes, component patterns, layout conventions, and visual quality standards for the Japan travel concierge app.
user-invocable: true
---

# Shogun Design System

## Overview

Shogun is a travel concierge app for a family trip to Japan (Mar-Apr 2026). The web UI serves 3 family members who will primarily use it on phones while walking around Tokyo, Nara, Osaka, and Kyoto.

The visual identity should feel **warm, organized, and culturally respectful** -- clean lines and intentional empty space with selective bold accents, inspired by Japanese aesthetic sensibility.

**Tech stack:** Next.js (App Router), React, Tailwind CSS, inline styles (existing pattern), Lucide icons.

**Reference files:**
- Theme variables: `src/app/globals.css`
- City config: `src/lib/cities.ts`
- Tailwind config: `tailwind.config.js`
- Layout shell: `src/app/(app)/layout.tsx`

---

## City Theme System

Shogun uses CSS custom properties that change per city via `data-city` attribute on `<html>`. The Tailwind config bridges these as `city-primary`, `city-accent`, `city-highlight`, and `city-surface`.

| City | Primary | Accent | Highlight | Surface | Character |
|------|---------|--------|-----------|---------|-----------|
| **Tokyo** | `#0d1b2e` midnight navy | `#e91e8c` neon magenta | `#00d4ff` cyan | `#f0f4ff` ice blue | Electric, futuristic |
| **Nara** | `#2d3a1e` deep forest | `#8b6914` amber gold | `#c4956a` sand | `#f7f3ec` warm cream | Ancient, natural |
| **Osaka** | `#1a0a00` burnt black | `#ff4500` neon orange | `#f5c518` golden | `#fff8f0` warm white | Bold, energetic |
| **Kyoto** | `#1a0f0a` dark lacquer | `#8b1a1a` deep crimson | `#f7b8c4` sakura pink | `#faf6f0` soft cream | Refined, traditional |
| **Default** | `#1a1a2e` deep indigo | `#c0392b` red | `#f39c12` amber | `#f5f5f5` light grey | Pre-trip neutral |

### Using City Colors

```tsx
// In CSS / inline styles:
background: "var(--city-primary)"
color: "var(--city-accent)"

// In Tailwind classes (via tailwind.config.js bridge):
className="bg-city-primary text-city-accent border-city-highlight"

// Gradient pattern used in hero and status cards:
background: "linear-gradient(135deg, var(--city-primary), color-mix(in srgb, var(--city-primary) 70%, var(--city-accent)))"
```

---

## Color Palette -- Fixed Colors

These are used across all cities regardless of theme:

### POI City Backgrounds (pastel tiles)
| City | Background |
|------|-----------|
| Osaka | `#FFF0E6` |
| Nara | `#E8F5E9` |
| Kanazawa | `#FFF8E1` |
| Tokyo | `#EEF2FF` |
| Kyoto | `#FCE4EC` |

### Category Badge Colors
| Category | Background | Text |
|----------|-----------|------|
| Temple/Shrine | `#FEE2E2` | `#991B1B` |
| Food/Restaurant | `#FED7AA` | `#9A3412` |
| Shopping | `#EDE9FE` | `#5B21B6` |
| Nature/Park | `#D1FAE5` | `#065F46` |
| Museum/Culture | `#DBEAFE` | `#1E40AF` |
| Entertainment | `#FCE7F3` | `#9D174D` |
| Transit | `#E5E7EB` | `#374151` |
| Electronics/Tech | `#CFFAFE` | `#0E7490` |
| Default | `#F3F4F6` | `#4B5563` |

### Leg Type Colors (calendar/itinerary)
| Type | Background | Text |
|------|-----------|------|
| Flight | `#dbeafe` | `#1e40af` |
| Hotel | `#e0e7ff` | `#3730a3` |
| Activity | `#d1fae5` | `#065f46` |
| Transit | `#fef9c3` | `#713f12` |
| Restaurant | `#ffe4e6` | `#9f1239` |
| TBD | `#f1f5f9` | `#94a3b8` (dashed border `#cbd5e1`) |

### Status Colors
| Status | Background | Text |
|--------|-----------|------|
| Pending | `#fef3c7` | `#92400e` |
| Approved/Success | `#d1fae5` | `#065f46` |
| Rejected/Error | `#fee2e2` | `#991b1b` |
| Warning | `#fff7ed` border `#fed7aa` | `#9a3412` |
| Info | `#eff6ff` | `#1e40af` |
| Tip | `#ecfdf5` | `#059669` |

### Text Colors
| Role | Color |
|------|-------|
| Primary heading | `#111827` |
| Body text | `#4b5563` |
| Secondary/muted | `#6b7280` |
| Placeholder/tertiary | `#94a3b8` |
| Link/accent blue | `#1d4ed8` |
| Success green | `#10b981` |

### Background Colors
| Role | Color |
|------|-------|
| Page background | `#f9fafb` (or `var(--city-surface)` per city) |
| Card background | `white` |
| Subtle card fill | `#f8fafc` |
| Note callout | `#fef9c3` text `#92400e` |

---

## Typography

The app uses the system font stack: `-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif`.

| Element | Size | Weight | Other |
|---------|------|--------|-------|
| Page title | `1.5rem` | 900 | -- |
| Section heading | `1rem` | 700 | -- |
| City hero name | `2.5rem` | 900 | `line-height: 1` |
| Card title | `0.95rem` | 700 | -- |
| Body text | `0.85-0.875rem` | 400 | `line-height: 1.4` |
| Small/secondary | `0.8rem` | 400 | `opacity: 0.75` or muted color |
| Label/meta | `0.7-0.75rem` | 400-700 | `text-transform: uppercase; letter-spacing: 0.06-0.1em` |
| Badge text | `0.7rem` | 700 | `letter-spacing: 0.02em; text-transform: capitalize` |
| Tab bar label | `0.6rem` | 400 | -- |
| Tiny data | `0.65rem` | 400-600 | -- |

---

## Component Patterns

### Cards
The standard card pattern used throughout the app:
```
background: white
borderRadius: 12px
padding: 1rem
boxShadow: 0 1px 3px rgba(0,0,0,0.06-0.08)
```

### Gradient Status Cards
Used for primary status/hero tiles:
```
background: linear-gradient(135deg, var(--city-primary), color-mix(in srgb, var(--city-primary) 70%, var(--city-accent)))
borderRadius: 12px
padding: 1.25rem
color: white
```

### POI Tiles
City-colored pastel background, rounded corners, subtle shadow:
```
background: <city pastel color>
borderRadius: 10px
padding: 0.875rem
boxShadow: 0 1px 3px rgba(0,0,0,0.07)
transition: transform 0.15s, box-shadow 0.15s
```

### Badges (pill-shaped)
```
display: inline-block
fontSize: 0.7rem
fontWeight: 700
background: <category bg>
color: <category text>
padding: 3px 10px
borderRadius: 9999px
```

### Section Labels
```
fontSize: 0.65-0.7rem
color: rgba(255,255,255,0.35-0.4) (on dark) or #94a3b8 (on light)
textTransform: uppercase
letterSpacing: 0.08em
```

### Buttons -- Primary CTA
```
display: inline-block
background: var(--city-accent)
color: white
padding: 0.75rem 2rem
borderRadius: 9999px (pill) or 6px (compact)
fontWeight: 700
fontSize: 0.95rem
```

### Loading/Empty States
Use centered text with muted color:
```
minHeight: 140px
display: flex
alignItems: center
justifyContent: center
color: #94a3b8
fontSize: 0.85rem
```

### Error Banners
```
background: #fee2e2 (error) or #fff7ed (warning)
borderRadius: 12px
padding: 1rem
color: #991b1b (error) or #9a3412 (warning)
border: 1px solid #fed7aa (warning only)
fontSize: 0.85rem
```

### Notes/Callouts
```
background: #fef9c3
borderRadius: 4px
padding: 4px 8px
color: #92400e
fontSize: 0.8rem
```

---

## Layout Patterns

### App Shell
- Desktop: fixed sidebar (240px) + scrollable main content
- Mobile: no sidebar, bottom tab bar (60px fixed), main content scrolls with bottom padding

### Page Layout
```
padding: 1.5rem
maxWidth: 900px (dashboard) or 1100px (city pages)
```

### Grid Layouts
```
// Two-column dashboard grid
display: grid
gridTemplateColumns: 1fr 1fr
gap: 1rem

// POI card grid (responsive auto-fill)
display: grid
gridTemplateColumns: repeat(auto-fill, minmax(240px, 1fr))
gap: 0.75rem

// Desktop split (50/50), mobile stacked
grid-template-columns: 1fr 1fr  (desktop)
grid-template-columns: 1fr      (mobile, via @media)
```

### Spacing Scale
| Size | Usage |
|------|-------|
| `0.25rem` | Tight inner gaps |
| `0.375-0.5rem` | Between related items |
| `0.75rem` | Standard gap between cards/sections |
| `1rem` | Card padding, grid gaps |
| `1.25rem` | Generous card padding |
| `1.5rem` | Page padding, section margins |
| `2rem` | Hero padding |

---

## Sidebar / Navigation

### Sidebar (Desktop)
- Background: `var(--city-primary)` with smooth 0.4s transition
- Logo: kanji character at 1.4rem weight 800
- Nav items: flex row, 0.875rem, active state = white + `rgba(255,255,255,0.12)` bg + right border accent
- Section labels: 0.65rem uppercase tracking-wide, very low opacity

### Mobile Tab Bar
- Fixed bottom, 60px height, `var(--city-primary)` background
- Icons at 1.25rem, labels at 0.6rem
- Active: white, inactive: `rgba(255,255,255,0.5)`
- Horizontally scrollable for many items

---

## Visual Quality Principles

1. **City identity matters** -- every page should feel like it belongs to the current city through theme colors
2. **Data-forward** -- users are walking in Japan; scannable tiles with icon + value + label, not paragraphs
3. **Touch-friendly** -- generous tap targets (min 44px), comfortable spacing
4. **Depth through gradients** -- use `linear-gradient` and `color-mix` for status cards and heroes, not flat solid fills
5. **Whitespace as structure** -- let content breathe; separate sections with margins, not heavy borders
6. **Japanese aesthetic influence** -- clean lines, intentional empty space, muted colors with selective bold accents
7. **Subtle transitions** -- 0.15-0.2s on interactive elements, 0.4s on theme color transitions
8. **Emoji as icons** -- the current codebase uses emoji consistently for navigation and data labels; maintain this pattern
9. **Maps and images full-bleed** -- when displaying maps, use full available width
10. **Progressive disclosure** -- show summaries by default, details on tap/click (drawers, expanded views)

---

## Anti-Patterns to Avoid

- **Generic Bootstrap/Material look** -- Shogun has a distinct identity per city
- **Walls of text** -- break into scannable tiles and badges
- **Inconsistent spacing** -- use the spacing scale above
- **Over-use of borders/dividers** -- prefer whitespace and background color shifts
- **Default unstyled forms** -- all inputs should match the design language
- **Tiny touch targets** -- minimum 44px for anything tappable
- **Jarring color transitions** -- use the 0.4s ease transition on theme changes
- **Spinners for loading** -- use inline text messages ("Loading weather...") matching the card layout
- **Hard-coded colors where theme vars exist** -- always use `var(--city-*)` for city-contextual elements
- **Mixing Tailwind classes and inline styles arbitrarily** -- the current codebase primarily uses inline styles; be consistent within a component (either all inline or all Tailwind, not a random mix)

---

## Detailed Reference

For code examples, component snippets, and the full icon/color reference, see:
`references/design-system.md`
