# Mobile Viewport Reference -- Shogun

This document provides concrete values, measurements, and quick-reference tables for mobile development in Shogun. Use this alongside the main `SKILL.md` for implementation details.

---

## Table of Contents

1. [Breakpoint Values](#breakpoint-values)
2. [Target Devices](#target-devices)
3. [Screen Dimension Reference](#screen-dimension-reference)
4. [Safe Area Inset Patterns](#safe-area-inset-patterns)
5. [Touch Target Measurement Guide](#touch-target-measurement-guide)
6. [Thumb Zone Diagram](#thumb-zone-diagram)
7. [Media Query Quick Reference](#media-query-quick-reference)
8. [Performance Budget Numbers](#performance-budget-numbers)
9. [Viewport Meta Tag Reference](#viewport-meta-tag-reference)
10. [CSS Unit Reference for Mobile](#css-unit-reference-for-mobile)
11. [Shogun Component Dimensions](#shogun-component-dimensions)
12. [Device Pixel Ratio Reference](#device-pixel-ratio-reference)
13. [Japan Network Speed Reference](#japan-network-speed-reference)

---

## Breakpoint Values

### Shogun Codebase Breakpoints (as of 2026-03-19)

These are the actual breakpoints used in the Shogun codebase, extracted from `globals.css` and component `<style>` tags:

| Breakpoint | Value | Direction | Source file | Purpose |
|------------|-------|-----------|-------------|---------|
| Mobile layout | `768px` | `max-width` | `globals.css` | Hide sidebar, show tab bar |
| Desktop layout | `769px` | `min-width` | `globals.css` | Show sidebar, hide tab bar |
| Chat mobile | `639px` | `max-width` | `ChatPanel.tsx` | Chat sidebar toggle |
| POI map stack | `767px` | `max-width` | `PoisPage.tsx` | Stack map below tiles |

### Tailwind Default Breakpoints (available but mostly unused)

| Prefix | Value | Direction |
|--------|-------|-----------|
| `sm:` | `640px` | `min-width` |
| `md:` | `768px` | `min-width` |
| `lg:` | `1024px` | `min-width` |
| `xl:` | `1280px` | `min-width` |
| `2xl:` | `1536px` | `min-width` |

### Tailwind Config Custom Values

The `tailwind.config.js` does **not** define custom breakpoints. It only extends `colors` with CSS variable bridges:

```js
// tailwind.config.js -- NO custom screens defined
module.exports = {
  theme: {
    extend: {
      colors: {
        "city-primary":   "var(--city-primary)",
        "city-accent":    "var(--city-accent)",
        "city-highlight": "var(--city-highlight)",
        "city-surface":   "var(--city-surface)",
      },
    },
  },
};
```

---

## Target Devices

### Primary Devices (Family Trip)

These are the device classes the Shogun UI must work well on. Specific models are representative -- design for the size class, not the exact device.

| Device Class | Representative Model | Viewport (CSS px) | Physical (pt) | DPR | Priority |
|-------------|---------------------|-------------------|---------------|-----|----------|
| **iPhone standard** | iPhone 14 / 15 | 390 x 844 | 390 x 844 | 3x | Highest |
| **iPhone large** | iPhone 14/15 Pro Max | 430 x 932 | 430 x 932 | 3x | High |
| **iPhone compact** | iPhone SE (3rd gen) | 375 x 667 | 375 x 667 | 2x | Medium |
| **Android standard** | Samsung Galaxy S24 | 360 x 780 | 360 x 780 | 3x | High |
| **Android large** | Samsung Galaxy S24 Ultra | 384 x 824 | 384 x 824 | 3x | Medium |
| **Tablet** | iPad (10th gen) | 820 x 1180 | 820 x 1180 | 2x | Low |
| **Desktop** | Laptop browser | 1440 x 900+ | -- | 1-2x | Low (pre-trip) |

### Critical Width Range

The most common phone viewport widths fall between **360px and 430px**. Design and test primarily in this range:

```
|----- 360px ------|  Samsung Galaxy S series, Pixel
|------ 375px ------|  iPhone SE, iPhone 8
|------- 390px -------|  iPhone 14/15/16
|--------- 430px ---------|  iPhone Pro Max
```

---

## Screen Dimension Reference

### Common Phone Viewports (CSS Pixels)

| Device | Width | Height | Safe Top | Safe Bottom | Usable Height |
|--------|-------|--------|----------|-------------|---------------|
| iPhone SE (3rd) | 375 | 667 | 20 | 0 | 647 |
| iPhone 14 | 390 | 844 | 59 | 34 | 751 |
| iPhone 14 Pro | 393 | 852 | 59 | 34 | 759 |
| iPhone 14 Pro Max | 430 | 932 | 59 | 34 | 839 |
| iPhone 15 | 393 | 852 | 59 | 34 | 759 |
| iPhone 15 Pro Max | 430 | 932 | 59 | 34 | 839 |
| iPhone 16 | 393 | 852 | 59 | 34 | 759 |
| Samsung Galaxy S24 | 360 | 780 | 0 | 0 | 780 |
| Samsung Galaxy S24+ | 384 | 824 | 0 | 0 | 824 |
| Samsung Galaxy S24 Ultra | 384 | 824 | 0 | 0 | 824 |
| Pixel 8 | 412 | 915 | 0 | 0 | 915 |
| Pixel 8 Pro | 448 | 998 | 0 | 0 | 998 |

### Usable Content Height Calculation

```
Usable Height = Viewport Height
              - Safe Area Top (notch/status bar)
              - Safe Area Bottom (home indicator)
              - Browser Chrome (URL bar, ~50px on first load, collapses on scroll)
              - App Chrome (Shogun tab bar: 60px)
```

For iPhone 14 (the most common case):
```
844px (viewport)
 -59px (safe area top / Dynamic Island)
 -34px (safe area bottom / home indicator)
 -50px (Safari URL bar, before scroll)
 -60px (Shogun tab bar)
 --------
 641px usable on first load
 691px usable after URL bar collapses
```

### Tablet Viewports

| Device | Width (portrait) | Height (portrait) |
|--------|-----------------|-------------------|
| iPad (10th gen) | 820 | 1180 |
| iPad Air (M2) | 820 | 1180 |
| iPad Pro 11" | 834 | 1194 |
| iPad Pro 12.9" | 1024 | 1366 |
| iPad Mini (6th) | 744 | 1133 |

Note: At 820px, the iPad triggers the desktop layout (sidebar visible, tab bar hidden) since the breakpoint is 769px. This is correct -- iPads have enough space for the sidebar.

---

## Safe Area Inset Patterns

### CSS Custom Properties

These are set by the browser when `viewport-fit: cover` is in the viewport meta tag:

```css
env(safe-area-inset-top)      /* Notch, Dynamic Island, status bar */
env(safe-area-inset-bottom)   /* Home indicator bar */
env(safe-area-inset-left)     /* Landscape: left edge near notch */
env(safe-area-inset-right)    /* Landscape: right edge near notch */
```

### Typical Values by Device

| Device | Top | Bottom | Left (landscape) | Right (landscape) |
|--------|-----|--------|-------------------|---------------------|
| iPhone SE (3rd) | 20px | 0px | 0px | 0px |
| iPhone 14 | 59px | 34px | 59px | 0px |
| iPhone 14 Pro (Dynamic Island) | 59px | 34px | 59px | 0px |
| iPhone 15 Pro Max | 59px | 34px | 59px | 0px |
| Samsung Galaxy S24 | 0px | 0px | 0px | 0px |
| iPad (any) | 24px | 20px | 0px | 0px |

Android devices generally report 0px for all safe area insets (the OS handles it at the system level).

### Application to Shogun Components

**Bottom tab bar:**
```css
.mobile-tab-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: calc(60px + env(safe-area-inset-bottom, 0px));
  padding-bottom: env(safe-area-inset-bottom, 0px);
  background-color: var(--city-primary);
  z-index: 50;
}
```

**Main content padding (mobile):**
```css
@media (max-width: 768px) {
  .main-content {
    padding-bottom: calc(60px + env(safe-area-inset-bottom, 0px));
  }
}
```

**Bottom sheet content:**
```tsx
<div style={{
  paddingBottom: "calc(1.5rem + env(safe-area-inset-bottom, 0px))",
}}>
```

**Fixed chat input bar:**
```tsx
<div style={{
  position: "sticky",
  bottom: 0,
  paddingBottom: "calc(0.75rem + env(safe-area-inset-bottom, 0px))",
}}>
```

### Enabling Safe Area Insets

Safe area inset values are only populated when the viewport meta tag includes `viewport-fit=cover`:

```html
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
```

In Next.js 14:
```tsx
// src/app/layout.tsx
export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
};
```

Without `viewport-fit: cover`, all `env(safe-area-inset-*)` values resolve to `0px`.

---

## Touch Target Measurement Guide

### Minimum Touch Target Sizes

| Standard | Minimum Size | Recommended |
|----------|-------------|-------------|
| WCAG 2.1 AAA | 44 x 44 CSS px | -- |
| Apple HIG | 44 x 44 pt | 48 x 48 pt |
| Material Design 3 | 48 x 48 dp | -- |
| **Shogun standard** | **48 x 48 CSS px** | **48 x 48 CSS px** |

### Measuring Touch Targets

A touch target's effective size is the total clickable/tappable area, including padding:

```
Touch Target Size = Content Size + Padding (all sides)

Example: A button with 12px text and 18px vertical padding
  Content height: ~18px (line height of 12px text)
  + top padding:  18px
  + bottom padding: 18px
  = Total height: ~54px  (GOOD: exceeds 48px)
```

### Common Shogun Element Measurements

| Element | Content | Padding | Total | Meets 48px? |
|---------|---------|---------|-------|-------------|
| Tab bar item | ~28px (icon+label) | 4px top/bottom, 8px sides | ~36px height | NO |
| Filter pill | ~13px text | 4px top/bottom, 12px sides | ~21px height | NO |
| Sidebar nav link | ~14px text | 10px top/bottom, 16px sides | ~34px height | NO |
| Chat send button | ~14px text | 8px top/bottom, 16px sides | ~30px height | NO |
| DayDrawer close | ~20px icon | 0px explicit | ~20px | NO |
| PoiCard (full card) | Variable | 14px all sides | Full card | YES |
| Primary CTA button | ~15px text | 12px top/bottom, 32px sides | ~39px height | BORDERLINE |

### How to Fix Undersized Targets

**Method 1: Increase padding directly**
```tsx
// Before: 21px touch target
<button style={{ padding: "4px 12px" }}>Filter</button>

// After: 50px touch target
<button style={{ padding: "14px 16px" }}>Filter</button>
```

**Method 2: Invisible hit area expansion (when visual size must stay small)**
```tsx
<button style={{
  padding: "4px 12px",        // Visual padding (small)
  position: "relative",
}}>
  Filter
  {/* Invisible expanded hit area */}
  <span style={{
    position: "absolute",
    inset: "-12px -4px",       // Expand hit area by this much
    // No background, no border -- invisible
  }} />
</button>
```

**Method 3: Negative margin to maintain layout spacing**
```tsx
<button style={{
  padding: "14px 16px",       // Big touch target
  margin: "-10px -4px",       // Pull back to maintain visual spacing
  fontSize: "0.8rem",
}}>
  Filter
</button>
```

### Spacing Between Touch Targets

| Scenario | Minimum Gap | Recommended Gap |
|----------|-------------|-----------------|
| Adjacent buttons | 8px | 12px |
| List items | 0px (if each item is full-width) | 4px separator |
| Grid of cards | 8px | 12px (0.75rem) |
| Tab bar items | 0px (flex distributes) | -- |
| Filter pills | 8px | 10px |

---

## Thumb Zone Diagram

### One-Handed Phone Use (Right Hand)

```
+---------------------------+
|         HARD ZONE         |    Top 30% of screen
|   Requires hand shift     |    - Place: page titles, non-interactive headers
|   or second hand          |    - Avoid: primary actions, frequent interactions
|                           |
+---------------------------+
|       STRETCH ZONE        |    Middle 30% of screen
|   Reachable with effort   |    - Place: scrollable content, lists, feeds
|   Thumb extends to reach  |    - Cards, tiles, secondary actions
|                           |
+---------------------------+
|        EASY ZONE          |    Bottom 40% of screen
|   Natural thumb arc       |    - Place: primary actions, navigation
|   Comfortable, no strain  |    - Tab bar, send button, CTAs
|                           |
|   +---+---+---+---+---+  |    <-- Tab bar lives here
+---------------------------+
```

### Thumb Reach Arc (Right Hand)

```
+---------------------------+
|  X  X  X  .  .  .  .  .  |    X = Cannot reach
|  X  X  .  .  .  .  .  .  |    . = Difficult reach
|  X  .  .  .  .  o  o  .  |    o = Comfortable reach
|  .  .  .  o  o  O  O  o  |    O = Natural resting position
|  .  .  o  o  O  O  O  o  |
|  .  o  o  O  O  O  O  o  |    Thumb pivot point: bottom-right
|  o  o  O  O  O  O  O  .  |    (for right-hand use)
|  o  O  O  O  O  O  o  .  |
|  O  O  O  O  O  O  .  .  |
|  +--[Tab][Tab][Tab][Tab]  |    <-- Navigation tabs
+---------------------------+
```

### Left-Handed Thumb Zone (Mirrored)

```
+---------------------------+
|  .  .  .  .  .  X  X  X  |
|  .  .  .  .  .  .  X  X  |
|  .  o  o  .  .  .  .  X  |
|  o  O  O  o  o  .  .  .  |
|  o  O  O  O  o  o  .  .  |
|  o  O  O  O  O  o  o  .  |
|  .  O  O  O  O  O  o  o  |
|  .  o  O  O  O  O  O  o  |
|  .  .  O  O  O  O  O  O  |
|  [Tab][Tab][Tab][Tab]--+  |
+---------------------------+
```

### Thumb Zone Application to Shogun

| Zone | Shogun Elements | Placement |
|------|----------------|-----------|
| **Easy** (bottom 40%) | Tab bar, chat input + send, bottom sheet actions, filter bar | Correct placement |
| **Stretch** (middle 30%) | POI cards, calendar grid, weather tiles, message list | Natural scrolling zone |
| **Hard** (top 30%) | Page titles, section headers, sidebar toggle | Non-interactive or rarely used |

### Design Guidelines from Thumb Zones

1. **Navigation (tab bar):** Bottom of screen. CORRECT in current implementation.
2. **Primary CTA ("Send", "Save"):** Bottom of their container. Chat send is CORRECT.
3. **Destructive actions ("Delete", "Clear"):** Top of container or behind confirmation. Keeps them in the hard zone.
4. **Search/filter bar:** Can be top (hard zone) if it is a set-and-forget filter, or bottom if frequently toggled.
5. **Scroll content:** Middle zone. Cards, lists, feeds. Users naturally scroll with the thumb in this zone.

---

## Media Query Quick Reference

### Breakpoint Patterns Used in Shogun

```css
/* Mobile-only styles */
@media (max-width: 768px) {
  /* Applies to phones and small tablets */
}

/* Desktop-only styles */
@media (min-width: 769px) {
  /* Applies to tablets (landscape) and desktop */
}

/* Small phones only (chat sidebar behavior) */
@media (max-width: 639px) {
  /* Applies to phones in portrait */
}

/* POI map stacking */
@media (max-width: 767px) {
  /* Stack map below tiles */
}
```

### Mobile-First Pattern (Recommended)

Write base styles for mobile, enhance for desktop:

```css
/* Base: mobile (no media query needed) */
.grid { grid-template-columns: 1fr; }

/* Enhancement: desktop */
@media (min-width: 769px) {
  .grid { grid-template-columns: 1fr 1fr; }
}
```

### Orientation Queries

```css
/* Portrait (most common for Shogun) */
@media (orientation: portrait) { }

/* Landscape (maps, media viewing) */
@media (orientation: landscape) { }
```

### Feature Queries

```css
/* Touch device (heuristic) */
@media (hover: none) and (pointer: coarse) {
  /* Increase touch targets, hide hover-only UI */
}

/* Fine pointer (mouse/stylus) */
@media (hover: hover) and (pointer: fine) {
  /* Hover effects, smaller targets OK */
}

/* Reduced motion preference */
@media (prefers-reduced-motion: reduce) {
  * { animation-duration: 0.01ms !important; }
}

/* Dark mode (not currently used in Shogun, city themes control colors) */
@media (prefers-color-scheme: dark) { }

/* High contrast */
@media (prefers-contrast: high) { }
```

### Tailwind Responsive Utilities

If using Tailwind classes instead of inline styles:

```tsx
// Mobile-first: single column, then 2 columns at md (768px)
<div className="grid grid-cols-1 md:grid-cols-2 gap-3">

// Hide on mobile, show on desktop
<div className="hidden md:block">Desktop sidebar</div>

// Show on mobile, hide on desktop
<div className="block md:hidden">Mobile tab bar</div>

// Responsive padding
<div className="p-4 md:p-6">Content</div>

// Responsive text size
<h1 className="text-xl md:text-2xl font-black">Title</h1>
```

### JavaScript Breakpoint Detection

```tsx
// SSR-safe breakpoint hook (use in client components only)
function useIsMobile(breakpoint = 768) {
  const [isMobile, setIsMobile] = useState(true); // Default: mobile (SSR-safe)

  useEffect(() => {
    const mql = window.matchMedia(`(max-width: ${breakpoint}px)`);
    setIsMobile(mql.matches);

    function handler(e: MediaQueryListEvent) {
      setIsMobile(e.matches);
    }
    mql.addEventListener("change", handler);
    return () => mql.removeEventListener("change", handler);
  }, [breakpoint]);

  return isMobile;
}

// Usage
const isMobile = useIsMobile();     // true when <= 768px
const isSmall = useIsMobile(639);   // true when <= 639px
```

### CSS Container Queries (future consideration)

Container queries allow components to respond to their parent's width rather than the viewport. Useful when the same component appears in different layout contexts:

```css
/* Define a container */
.card-grid { container-type: inline-size; }

/* Respond to container width */
@container (min-width: 600px) {
  .poi-card { display: grid; grid-template-columns: 200px 1fr; }
}
```

Not currently used in Shogun but available in all modern browsers (Safari 16+, Chrome 105+).

---

## Performance Budget Numbers

### Bundle Size Budgets

| Asset | Budget (gzipped) | Budget (uncompressed) | Rationale |
|-------|-------------------|-----------------------|-----------|
| **Total First Load JS** | 150 KB | 500 KB | 3G: ~2s download, ~1.5s parse |
| **Per-route JS chunk** | 50 KB | 170 KB | Smooth page transitions |
| **Total CSS** | 30 KB | 100 KB | Tailwind purges unused |
| **Largest single image** | 100 KB | 300 KB | Hero images should be WebP/AVIF |
| **Map tile** (Leaflet) | Managed by CDN | -- | Use vector tiles if possible |
| **Font files** | 0 KB | 0 KB | System font stack, no web fonts |
| **Third-party JS** | 50 KB total | 170 KB | Leaflet is ~42KB gzipped |

### Core Web Vitals Targets

| Metric | Good | Needs Improvement | Poor |
|--------|------|-------------------|------|
| **LCP** (Largest Contentful Paint) | < 2.5s | 2.5s -- 4.0s | > 4.0s |
| **INP** (Interaction to Next Paint) | < 200ms | 200ms -- 500ms | > 500ms |
| **CLS** (Cumulative Layout Shift) | < 0.1 | 0.1 -- 0.25 | > 0.25 |

### Shogun-Specific Performance Targets

| Scenario | Target | Notes |
|----------|--------|-------|
| Dashboard initial load | < 3s (LCP) | Includes ambient API call |
| Tab bar tap to page paint | < 300ms | Route change, no API |
| POI card tap to detail | < 500ms | May include API call |
| Chat message send to visible | < 100ms | Optimistic UI, no wait |
| Chat response complete | < 25s | LLM gateway timeout |
| Bottom sheet open animation | < 200ms | Pure CSS/JS, no data |
| Map tile first paint | < 2s | CDN tile loading |
| Filter pill toggle to list update | < 300ms | Client-side filter or API |

### Network Budget (Japan Pocket WiFi)

Typical pocket WiFi speeds in Japan:

| Condition | Download | Upload | Latency |
|-----------|----------|--------|---------|
| Street level (LTE) | 20-50 Mbps | 5-15 Mbps | 30-80ms |
| Indoor (WiFi) | 10-30 Mbps | 5-10 Mbps | 20-50ms |
| Subway station | 5-15 Mbps | 2-5 Mbps | 50-150ms |
| Crowded area (Shibuya) | 3-10 Mbps | 1-3 Mbps | 80-200ms |
| Rural / temple grounds | 2-8 Mbps | 1-3 Mbps | 80-200ms |
| Subway in motion | 0 Mbps | 0 Mbps | -- (no signal) |

Time to load 150 KB gzipped JS bundle:

| Network Speed | Time |
|--------------|------|
| 50 Mbps | 24ms |
| 10 Mbps | 120ms |
| 3 Mbps | 400ms |
| 1 Mbps | 1.2s |

### Image Size Guidelines

| Use case | Max width | Max file size | Format |
|----------|-----------|---------------|--------|
| POI thumbnail | 400px | 50 KB | WebP |
| POI detail hero | 800px | 100 KB | WebP |
| Map marker icon | 32px | 2 KB | PNG or SVG |
| City hero background | CSS gradient | 0 KB | None (pure CSS) |
| Windy radar embed | iframe | N/A | Loaded by iframe |

---

## Viewport Meta Tag Reference

### Recommended Configuration for Shogun

```html
<meta name="viewport"
  content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no, viewport-fit=cover" />
```

### Next.js 14 Implementation

```tsx
// src/app/layout.tsx
import type { Metadata, Viewport } from "next";

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
  viewportFit: "cover",         // Enables safe-area-inset-* env variables
};
```

### Attribute Reference

| Attribute | Value | Purpose |
|-----------|-------|---------|
| `width` | `device-width` | Match CSS pixels to device width |
| `initial-scale` | `1` | No zoom on load |
| `maximum-scale` | `1` | Prevent zoom (avoids iOS input focus zoom) |
| `user-scalable` | `no` | Disable pinch-to-zoom (app-like behavior) |
| `viewport-fit` | `cover` | Content extends behind notch/home indicator; enables `env(safe-area-inset-*)` |

### When NOT to Disable Zoom

Accessibility guidelines recommend keeping zoom enabled. If Shogun needs to comply with WCAG:
- Remove `maximum-scale=1` and `user-scalable=no`
- Instead, fix iOS zoom by ensuring all `<input>` elements have `font-size >= 16px`

---

## CSS Unit Reference for Mobile

### Unit Comparison

| Unit | Meaning | Use for |
|------|---------|---------|
| `px` | CSS pixel (not physical pixel) | Borders, shadows, fixed dimensions |
| `rem` | Relative to root font size (16px default) | Font sizes, spacing, padding |
| `em` | Relative to parent font size | Letter spacing, relative padding |
| `%` | Relative to parent dimension | Widths, responsive containers |
| `vw` | 1% of viewport width | Full-bleed elements |
| `vh` | 1% of viewport height | **AVOID** on mobile (see below) |
| `dvh` | 1% of dynamic viewport height | **PREFER** over vh on mobile |
| `svh` | 1% of smallest viewport height | URL bar expanded |
| `lvh` | 1% of largest viewport height | URL bar collapsed |
| `vmin` | 1% of smaller viewport dimension | Rarely used |
| `vmax` | 1% of larger viewport dimension | Rarely used |

### The vh Problem on Mobile

| Unit | Behavior on iOS Safari |
|------|----------------------|
| `100vh` | Fixed to largest viewport (URL bar collapsed). Content hidden behind URL bar on initial load. |
| `100dvh` | Dynamically updates as URL bar appears/disappears. **Correct behavior.** |
| `100svh` | Always matches smallest viewport (URL bar visible). Leaves gap when URL bar hides. |
| `100lvh` | Always matches largest viewport (URL bar hidden). Same as `100vh`. |

### Shogun App Shell Height Fix

Current:
```css
.app-shell { height: 100vh; }  /* Can be hidden behind URL bar */
```

Recommended:
```css
.app-shell {
  height: 100vh;                    /* Fallback for older browsers */
  height: 100dvh;                   /* Modern browsers */
}
```

Or with fill-available:
```css
.app-shell {
  height: 100vh;
  height: -webkit-fill-available;   /* Safari */
  height: 100dvh;                   /* Modern browsers override */
}
```

---

## Shogun Component Dimensions

### Fixed Dimensions in the Codebase

| Component | Dimension | Value | Source |
|-----------|-----------|-------|--------|
| Sidebar width | `--sidebar-width` | `240px` | `globals.css` :root |
| Header height | `--header-h` | `64px` | `globals.css` :root |
| Mobile tab bar height | fixed height | `60px` | `globals.css` .mobile-tab-bar |
| City hero height | fixed height | `280px` | `globals.css` .city-hero |
| Bottom sheet max height | inline style | `80vh` | `DayDrawer.tsx` |
| Chat sidebar width | inline style | `260px` | `ChatPanel.tsx` |
| Calendar day cell min height | inline style | `90px` | `CalendarGrid.tsx` |
| Weather card min height | inline style | `140px` | `WeatherCard.tsx` |
| Card border radius | inline style | `12px` | Multiple components |
| POI tile border radius | inline style | `10px` | `PoiCard.tsx` |
| Badge border radius | inline style | `9999px` | Multiple components |
| Bottom sheet corner radius | inline style | `16px 16px 0 0` | `DayDrawer.tsx` |

### Grid Configurations

| Grid | Template | Min item width | Source |
|------|----------|---------------|--------|
| Dashboard status | `1fr 1fr` (hardcoded) | ~170px at 375px viewport | `dashboard/page.tsx` |
| Ambient weather+info | `1fr 1fr` (hardcoded) | ~170px at 375px viewport | `AmbientDashboard.tsx` |
| POI cards (no map) | `auto-fill, minmax(280px, 1fr)` | 280px | `PoisPage.tsx` |
| POI cards (with map) | `1fr 1fr` (hardcoded) | ~170px on mobile | `PoisPage.tsx` |
| Calendar grid | `auto-fill, minmax(160px, 1fr)` | 160px | `CalendarGrid.tsx` |
| Forecast strip | `flex` with `flex: 1` | ~33% of card width | `WeatherCard.tsx` |

### Padding and Spacing

| Context | Value | Source |
|---------|-------|--------|
| Page padding | `1.5rem` (24px) | `dashboard/page.tsx` |
| Card padding | `1rem` (16px) | Multiple |
| Generous card padding | `1.25rem` (20px) | Hero sections |
| Section gap | `0.75rem` (12px) | `AmbientDashboard.tsx` |
| Grid gap | `1rem` (16px) | Dashboard grids |
| Grid gap (cards) | `0.75rem` (12px) | POI cards |
| Tab/filter gap | `0.375rem` (6px) | `FilterBar.tsx` |
| Tab bar bottom space | `60px` | `globals.css` mobile content padding |

---

## Device Pixel Ratio Reference

### Common DPRs

| DPR | Devices | Image sizing |
|-----|---------|-------------|
| 1x | Older desktops | 1 CSS px = 1 physical px |
| 2x | Retina Mac, iPad, iPhone SE | Serve 2x images or use SVG |
| 3x | iPhone 14/15/16, most modern Android | Serve 3x images or use SVG |

### Image Sizing for DPR

For a 200px-wide container on a 3x device, the physical image should be 600px wide for crisp rendering. However, for performance, a 2x image (400px) is usually sufficient:

```tsx
<img
  src="/poi/photo-400w.webp"
  srcSet="/poi/photo-400w.webp 400w, /poi/photo-800w.webp 800w"
  sizes="(max-width: 768px) 100vw, 50vw"
  width={400}
  height={300}
  loading="lazy"
/>
```

### When to Use SVG vs. Raster

| Content | Format | Reason |
|---------|--------|--------|
| Icons (Lucide) | SVG (via component) | Scales to any DPR perfectly |
| Emoji icons | Unicode | Rendered by OS, always crisp |
| Map markers | SVG or PNG at 2x | Small fixed size |
| POI photos | WebP at 2x | Photographic content |
| City hero backgrounds | CSS gradient | No image needed |
| App icon (PWA) | PNG at 192x192 and 512x512 | Required by manifest spec |

---

## Japan Network Speed Reference

### Connectivity by Location Type

| Location | Speed Class | Strategy |
|----------|------------|----------|
| Hotel room (WiFi) | Fast (20-50 Mbps) | Sync/prefetch for the day |
| Street level (pocket WiFi) | Good (10-30 Mbps) | Normal app usage |
| Convenience store (WiFi) | Medium (5-15 Mbps) | API calls work fine |
| Subway station platform | Medium (5-15 Mbps) | Quick glances, not heavy loading |
| Subway in motion | None (0 Mbps) | Must work offline or show cached data |
| Bullet train (Shinkansen) | Slow (1-5 Mbps) | Aggressive caching, minimal payloads |
| Temple/shrine grounds | Variable (2-10 Mbps) | Cache phrases and maps beforehand |
| Department store (basement) | Weak (0-5 Mbps) | Show last-known data |
| Crowded events (festivals) | Congested (0-3 Mbps) | Timeout gracefully |

### Payload Budget per Network Class

| Speed Class | Max acceptable first paint | Max API payload |
|------------|---------------------------|----------------|
| Fast (20+ Mbps) | 1.5s | 500 KB |
| Good (10-20 Mbps) | 2.5s | 200 KB |
| Medium (5-10 Mbps) | 3.5s | 100 KB |
| Slow (1-5 Mbps) | 5s | 50 KB |
| Offline | Instant (cached) | 0 KB (use cached) |

### Caching Priority for Offline Use

| Data | Cache strategy | Priority |
|------|---------------|----------|
| App shell (HTML/CSS/JS) | Service worker precache | Critical |
| Phrase book | Service worker precache | Critical |
| Last ambient summary | localStorage or cache API | High |
| POI list for current city | cache API, stale-while-revalidate | High |
| Itinerary/calendar | cache API | High |
| Chat history | Valkey server-side (not offline) | Low (degrades gracefully) |
| Map tiles for current city | Leaflet tile cache | Medium |
| POI photos | lazy load, no cache | Low |

---

## Quick Reference Card

### The Numbers That Matter Most

```
BREAKPOINTS
  Mobile/Desktop split:     768px
  Chat compact mode:        639px

TOUCH TARGETS
  Minimum tap size:         48 x 48 CSS px
  Minimum gap between:      8px

SAFE AREAS (iPhone 14/15)
  Top (notch):              59px
  Bottom (home indicator):  34px

SHOGUN CHROME
  Sidebar (desktop):        240px
  Tab bar (mobile):         60px
  Header height:            64px

PERFORMANCE
  First Load JS budget:     < 150 KB gzipped
  LCP target:               < 2.5s
  CLS target:               < 0.1
  INP target:               < 200ms

FONT FLOORS
  Body text minimum:        0.8rem (12.8px)
  Meta/label minimum:       0.7rem (11.2px)
  Input text (iOS zoom):    16px minimum

VIEWPORT
  Primary width range:      360px -- 430px
  Primary height range:     667px -- 932px
  Use dvh, not vh:          height: 100dvh
```
