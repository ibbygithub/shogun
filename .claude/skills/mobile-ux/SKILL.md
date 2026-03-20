---
name: mobile-ux
description: >
  Mobile-first design patterns for Shogun — responsive breakpoints, touch targets,
  viewport handling, and phone-in-Japan usage patterns. Use this skill when building
  or reviewing UI components that must work well on phones during the Japan trip.
user-invocable: true
---

# Mobile UX Patterns for Shogun

## Overview

Shogun is used by 3 family members walking through Tokyo, Osaka, Nara, and Kyoto. The primary interface during the trip is a phone held in one hand while navigating streets, subway stations, and restaurants. Every UI decision must prioritize:

1. **One-hand usability** -- thumb reach zones, bottom-anchored actions
2. **Glanceability** -- information scannable in 2 seconds, not readable in 20
3. **Connectivity resilience** -- Japan subway dead zones, patchy building WiFi
4. **Readability outdoors** -- high contrast, adequate font sizes, not washed out in sunlight

**Tech stack:** Next.js 14 (App Router, standalone output), React 18, Tailwind CSS 3.4, inline styles (existing codebase pattern), Lucide icons, Radix UI primitives.

**Key files:**
- App shell layout: `src/app/(app)/layout.tsx`
- Root layout (viewport meta): `src/app/layout.tsx`
- Global styles + breakpoints: `src/app/globals.css`
- Mobile tab bar: `src/components/layout/MobileTabBar.tsx`
- Desktop sidebar: `src/components/layout/Sidebar.tsx`
- Tailwind config: `tailwind.config.js`

---

## Responsive Breakpoints

### Current Codebase Breakpoints

The Shogun codebase uses **two breakpoints** defined in `globals.css` media queries (not in Tailwind config -- the Tailwind config has no custom screens):

| Breakpoint | CSS | Purpose |
|------------|-----|---------|
| **Mobile** | `max-width: 768px` | Hide sidebar, show bottom tab bar, single-column layouts |
| **Desktop** | `min-width: 769px` | Show sidebar (240px), hide bottom tab bar, multi-column grids |
| **Chat mobile** | `max-width: 639px` | Chat sidebar toggle visible, chat sidebar overlays full width |

The Tailwind default breakpoints are also available (`sm: 640px`, `md: 768px`, `lg: 1024px`, `xl: 1280px`) but the codebase primarily uses inline media queries in `<style>` tags or CSS class-based breakpoints in `globals.css`.

### Recommended Breakpoint Mental Model

| Range | Device class | Layout |
|-------|-------------|--------|
| 0 -- 639px | Phone portrait | Single column, bottom tab bar, full-bleed cards |
| 640 -- 767px | Phone landscape / small tablet | Single column, still bottom tab bar |
| 768px+ | Tablet / desktop | Sidebar + main content, 2-column grids |

### How Breakpoints Are Implemented

The codebase uses three patterns for responsive behavior:

**Pattern 1: CSS classes in globals.css (layout shell)**
```css
/* globals.css -- the app shell breakpoint */
@media (max-width: 768px) {
  .sidebar { display: none; }
  .main-content { padding-bottom: 60px; }
  .mobile-tab-bar { display: flex; }
}
@media (min-width: 769px) {
  .mobile-tab-bar { display: none; }
}
```

**Pattern 2: Inline `<style>` tags in components**
```tsx
// ChatPanel.tsx -- chat sidebar toggle breakpoint
<style>{`
  @media (max-width: 639px) {
    .sidebar-toggle { display: block !important; }
  }
`}</style>
```

```tsx
// PoisPage -- map grid stacking on mobile
<style>{`
  @media (max-width: 767px) {
    .pois-map-grid { grid-template-columns: 1fr !important; }
  }
`}</style>
```

**Pattern 3: JavaScript window width checks**
```tsx
// ChatPanel.tsx -- runtime mobile detection
const isMobile = () => typeof window !== "undefined" && window.innerWidth < 640;

// Used to overlay sidebar full-width on mobile:
if (isMobile()) setSidebarOpen(false);
```

### When Adding New Breakpoints

- Prefer the existing 768px breakpoint for sidebar/tab bar layout switches
- Use 640px for component-level mobile adjustments (chat, detail panels)
- Use `auto-fill` / `minmax()` grids that naturally respond to width rather than adding new breakpoints:

```tsx
// This naturally goes from 1 column to many, no breakpoint needed:
gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))"
```

---

## Touch Target Sizing

### Minimum Sizes

All interactive elements must meet minimum touch target sizes for comfortable thumb tapping:

| Element | Minimum size | Current implementation |
|---------|-------------|----------------------|
| Tab bar items | 48x48px hit area | `padding: "4px 8px"`, icon 1.25rem + label 0.6rem. Relies on flex spacing. |
| Filter pills | 44px height | `padding: "4px 12px"`, 0.8rem text. Needs verification. |
| Buttons (primary CTA) | 48px height | `padding: "0.75rem 2rem"`, 0.95rem text. Meets target. |
| Card tappable area | Full card | Cards use full-area Link wrapper. Good. |
| Close buttons | 48x48px hit area | DayDrawer close: `fontSize: "1.25rem"`. Needs larger hit area. |
| Input fields | 48px height | Chat input: `padding: "0.5rem 0.875rem"`. Borderline. |

### Fixing Undersized Touch Targets

When a visual element is smaller than 48px, expand the touch target without expanding the visual:

```tsx
// BAD: Visual and touch target both too small
<button style={{ padding: "4px 8px", fontSize: "0.75rem" }}>
  Delete
</button>

// GOOD: Visual is compact, touch target is generous
<button style={{
  padding: "12px 16px",  // At least 48px total height
  fontSize: "0.75rem",
  margin: "-8px -8px",   // Negative margin to maintain visual position
}}>
  Delete
</button>

// ALSO GOOD: Use a wrapper for invisible hit area expansion
<div style={{ padding: "8px", margin: "-8px" }}>
  <button style={{ padding: "4px 8px", fontSize: "0.75rem" }}>
    Delete
  </button>
</div>
```

### Spacing Between Touch Targets

Adjacent tappable elements need at least 8px gap to prevent mis-taps. The codebase already uses `gap: "0.375rem"` (6px) for filter pills -- this is tight. Prefer `gap: "0.5rem"` (8px) minimum for adjacent interactive elements.

```tsx
// Current filter bar -- slightly tight
<div style={{ display: "flex", gap: "0.375rem", flexWrap: "wrap" }}>

// Better for mobile fingers
<div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
```

---

## Thumb Zone Awareness

### The Reach Problem

When holding a phone one-handed (the Japan walking use case), the thumb has three reach zones:

- **Easy zone (bottom 40%)** -- natural arc, no stretch
- **Stretch zone (middle 30%)** -- reachable but requires grip adjustment
- **Hard zone (top 30%)** -- requires hand repositioning or second hand

### Current Shogun Layout Analysis

**Bottom tab bar (good):** Fixed at bottom, 60px height, in the easy zone. The 8 tabs are horizontally scrollable, keeping primary navigation in the thumb's natural arc.

**Page titles (acceptable):** Top of scrollable content. Users scroll down, so titles move into the easy zone quickly. Not a concern.

**Action buttons (needs attention):** Any CTA or primary action should be placed at the bottom of its context, not the top.

### Design Rules for Thumb-Friendly Layout

1. **Primary actions at the bottom** -- "Send" button in chat is correctly at the bottom. Filter/sort actions should also be bottom-anchored on mobile.

2. **Destructive actions in the hard zone** -- "Delete" and "Clear" buttons should be at the top or behind a confirmation, preventing accidental thumb taps.

3. **Scrollable content fills the middle** -- Lists, cards, and feeds go in the middle zone where scrolling is natural.

4. **Bottom sheets for detail views** -- The DayDrawer already uses this pattern correctly:

```tsx
// DayDrawer.tsx -- bottom sheet pattern (EXISTING)
<div style={{
  position: "fixed", inset: 0, zIndex: 100,
  display: "flex", alignItems: "flex-end",  // Anchors to bottom
}}>
  <div style={{ position: "absolute", inset: 0, background: "rgba(0,0,0,0.4)" }}
    onClick={onClose} />
  <div style={{
    position: "relative",
    width: "100%",
    maxHeight: "80vh",
    background: "white",
    borderRadius: "16px 16px 0 0",  // Top corners rounded
    padding: "1.25rem",
    overflowY: "auto",
  }}>
    {/* Content */}
  </div>
</div>
```

5. **Swipe affordances** -- Bottom sheets should include a visual drag handle:

```tsx
// Add a drag handle at the top of bottom sheets
<div style={{
  width: "36px",
  height: "4px",
  background: "#d1d5db",
  borderRadius: "2px",
  margin: "0 auto 0.75rem",
}} />
```

---

## Bottom Sheet Pattern

Bottom sheets are the mobile-native way to show detail views, confirmations, and secondary actions. The DayDrawer is the existing reference implementation.

### Anatomy of a Bottom Sheet

```tsx
function BottomSheet({ open, onClose, title, children }) {
  if (!open) return null;

  return (
    <div style={{
      position: "fixed",
      inset: 0,
      zIndex: 100,
      display: "flex",
      alignItems: "flex-end",
    }}>
      {/* Scrim / backdrop */}
      <div
        style={{ position: "absolute", inset: 0, background: "rgba(0,0,0,0.4)" }}
        onClick={onClose}
      />

      {/* Sheet */}
      <div style={{
        position: "relative",
        width: "100%",
        maxHeight: "85vh",
        background: "white",
        borderRadius: "16px 16px 0 0",
        padding: "1rem 1.25rem 1.5rem",
        overflowY: "auto",
        // Safe area padding for home indicator
        paddingBottom: "calc(1.5rem + env(safe-area-inset-bottom, 0px))",
      }}>
        {/* Drag handle */}
        <div style={{
          width: "36px",
          height: "4px",
          background: "#d1d5db",
          borderRadius: "2px",
          margin: "0 auto 0.75rem",
        }} />

        {/* Header with close button */}
        <div style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "1rem",
        }}>
          <h2 style={{ fontWeight: 800, fontSize: "1.1rem" }}>{title}</h2>
          <button
            onClick={onClose}
            style={{
              background: "none",
              border: "none",
              fontSize: "1.25rem",
              cursor: "pointer",
              padding: "8px",       // Generous touch target
              margin: "-8px",       // Pull back visual space
            }}
          >
            x
          </button>
        </div>

        {children}
      </div>
    </div>
  );
}
```

### When to Use Bottom Sheets

| Scenario | Pattern |
|----------|---------|
| Day detail in calendar | Bottom sheet (existing: DayDrawer) |
| POI detail on mobile | Bottom sheet or full-page push |
| Filter/sort options | Bottom sheet with pill grid |
| Confirmation dialogs | Small bottom sheet (maxHeight: 40vh) |
| Chat conversation list (mobile) | Full-overlay bottom sheet (existing: ChatPanel sidebar) |

### When NOT to Use Bottom Sheets

- Full editing forms -- use a pushed page instead
- Primary content views -- these should be full pages
- Information that needs landscape viewing (maps) -- use full-bleed

---

## Viewport Handling and Safe Areas

### Viewport Meta Tag

The root layout (`src/app/layout.tsx`) currently does NOT include a viewport meta tag. Next.js 14 adds a default one, but for mobile-optimized apps, the metadata export should explicitly configure it:

```tsx
// src/app/layout.tsx -- recommended metadata
export const metadata: Metadata = {
  title: "Shogun -- Japan Trip",
  description: "AI travel concierge for the Ibbotson Japan trip 2026",
  viewport: {
    width: "device-width",
    initialScale: 1,
    maximumScale: 1,         // Prevents unwanted zoom on input focus
    userScalable: false,     // App-like behavior
    viewportFit: "cover",    // Required for safe-area-inset-* to work
  },
};
```

Note: In Next.js 14, viewport configuration should use the `viewport` export rather than being nested in `metadata`:

```tsx
import type { Metadata, Viewport } from "next";

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
  viewportFit: "cover",
};

export const metadata: Metadata = {
  title: "Shogun -- Japan Trip",
  description: "AI travel concierge for the Ibbotson Japan trip 2026",
};
```

### Safe Area Insets

Modern phones have notches (iPhone), punch-hole cameras, and home indicators that overlap content. CSS `env()` variables provide safe inset values:

```css
/* Safe area variables (available when viewport-fit: cover) */
env(safe-area-inset-top)     /* Notch / status bar */
env(safe-area-inset-bottom)  /* Home indicator */
env(safe-area-inset-left)    /* Landscape rotation */
env(safe-area-inset-right)   /* Landscape rotation */
```

### Where Safe Areas Apply in Shogun

**Bottom tab bar** -- must clear the home indicator:
```css
.mobile-tab-bar {
  height: 60px;
  /* Add safe area padding at bottom */
  padding-bottom: env(safe-area-inset-bottom, 0px);
  height: calc(60px + env(safe-area-inset-bottom, 0px));
}
```

**Main content bottom padding** -- must clear tab bar + home indicator:
```css
@media (max-width: 768px) {
  .main-content {
    padding-bottom: calc(60px + env(safe-area-inset-bottom, 0px));
  }
}
```

**Bottom sheets** -- content must not be hidden by the home indicator:
```tsx
paddingBottom: "calc(1.5rem + env(safe-area-inset-bottom, 0px))"
```

**Fixed input bars** (chat input) -- same treatment as tab bar:
```tsx
<div style={{
  padding: "0.75rem 1rem",
  paddingBottom: "calc(0.75rem + env(safe-area-inset-bottom, 0px))",
  borderTop: "1px solid #e5e7eb",
  background: "white",
}}>
```

### The 100vh Problem

`100vh` on mobile Safari does not account for the browser chrome (URL bar). The app shell uses `height: 100vh` which can cause content to be hidden behind the URL bar on first load.

**Fix options:**

```css
/* Option 1: Use dvh (dynamic viewport height) -- supported iOS 15.4+ */
.app-shell {
  height: 100dvh;
}

/* Option 2: Fallback chain */
.app-shell {
  height: 100vh;                     /* Fallback */
  height: 100dvh;                    /* Modern browsers */
  height: -webkit-fill-available;    /* Safari fallback */
}

/* Option 3: CSS variable updated by JS */
.app-shell {
  height: calc(var(--vh, 1vh) * 100);
}
```

If using the JS approach:
```tsx
useEffect(() => {
  function setVh() {
    document.documentElement.style.setProperty("--vh", `${window.innerHeight * 0.01}px`);
  }
  setVh();
  window.addEventListener("resize", setVh);
  return () => window.removeEventListener("resize", setVh);
}, []);
```

---

## Offline and Slow-Network Handling

### Japan Network Reality

| Location | Connectivity |
|----------|-------------|
| Street level (cities) | Good -- pocket WiFi or eSIM 4G/5G |
| Subway (in motion) | Dead zone -- no signal between stations |
| Subway (at station) | Brief connectivity window (30-90 seconds) |
| Department store basements | Weak or absent signal |
| Rural areas (Nara park, temple trails) | Patchy 4G |
| Hotel WiFi | Usually good but sometimes slow |

### Strategies for Shogun

**1. Optimistic UI for chat messages**
The ChatPanel already adds user messages to state before the API responds. This is correct. Extend this to show a "sending" state that survives brief disconnections:

```tsx
// Current (good): message appears immediately
const userMsg = { role: "user", content: text, timestamp: Date.now() / 1000 };
setMessages((prev) => [...prev, userMsg]);
```

**2. Cache ambient dashboard data**
The AmbientDashboard refreshes every 10 minutes. When offline, show the last-fetched data with a stale indicator:

```tsx
// Show stale data age when offline
const staleMinutes = data?.generated_at
  ? Math.round((Date.now() - new Date(data.generated_at).getTime()) / 60000)
  : null;

{staleMinutes && staleMinutes > 15 && (
  <span style={{ fontSize: "0.7rem", color: "#d97706" }}>
    {staleMinutes}min ago (offline?)
  </span>
)}
```

**3. Service Worker for static assets**
Next.js standalone output does not include a service worker. For PWA-grade offline support, add `next-pwa` or a manual service worker that caches:
- The app shell (HTML, CSS, JS bundles)
- City theme CSS variables
- Last-known ambient data (weather, exchange rate)
- Phrase book data (critical for offline use in Japan)

**4. Loading states that do not block**
Never show a spinner that blocks the entire page. Show content progressively:

```tsx
// BAD: Blocking spinner
if (loading) return <Spinner />;

// GOOD: Skeleton with last-known data visible
<div style={{ opacity: loading ? 0.6 : 1, transition: "opacity 0.2s" }}>
  {data ? <RealContent data={data} /> : <SkeletonCards count={3} />}
</div>
```

**5. Retry with exponential backoff**
API calls should retry on network failure, not immediately give up:

```tsx
async function fetchWithRetry(fn: () => Promise<any>, maxRetries = 3): Promise<any> {
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      return await fn();
    } catch (e) {
      if (attempt === maxRetries - 1) throw e;
      await new Promise((r) => setTimeout(r, 1000 * Math.pow(2, attempt)));
    }
  }
}
```

---

## Next.js Responsive SSR Patterns

### Server Components vs. Client Components for Mobile

Server components (`page.tsx` files without `"use client"`) cannot use `window.innerWidth` or `matchMedia`. Responsive behavior in server components must use:

1. **CSS-only approaches** (media queries, `auto-fill` grids)
2. **Tailwind responsive classes** (`md:grid-cols-2`, `sm:hidden`)

Client components (`"use client"`) can use runtime width detection but should avoid it for initial render to prevent hydration mismatches:

```tsx
// BAD: Causes hydration mismatch (server renders desktop, client renders mobile)
const [isMobile, setIsMobile] = useState(window.innerWidth < 768);

// GOOD: Default to mobile, then check on mount
const [isMobile, setIsMobile] = useState(true); // SSR-safe default
useEffect(() => {
  setIsMobile(window.innerWidth < 768);
  const handler = () => setIsMobile(window.innerWidth < 768);
  window.addEventListener("resize", handler);
  return () => window.removeEventListener("resize", handler);
}, []);
```

### The Existing Pattern

The codebase uses `typeof window !== "undefined"` guards for SSR safety:

```tsx
// ChatPanel.tsx -- existing pattern
const isMobile = () => typeof window !== "undefined" && window.innerWidth < 640;
```

This works as a function call (evaluated at event time, not render time) and avoids hydration issues. Follow this pattern for new components.

### Layout Approach for Mobile-First

Since the app is primarily used on phones, build mobile layout first, then add desktop enhancements:

```tsx
// MOBILE-FIRST: Start with single column
<div style={{
  display: "grid",
  gridTemplateColumns: "1fr",
  gap: "0.75rem",
}}>
  {/* On desktop, CSS or Tailwind adds the second column */}
</div>

// In globals.css or inline <style>:
@media (min-width: 769px) {
  .dashboard-grid { grid-template-columns: 1fr 1fr; }
}
```

---

## PWA Considerations

### Current State

The Shogun web UI is **not** a PWA. There is no `manifest.json`, no service worker, and no `apple-mobile-web-app-capable` meta tag. The Next.js config uses `output: "standalone"` for Docker deployment.

### Minimum PWA Setup for Trip Use

For the Japan trip, a full PWA is not required, but "Add to Home Screen" improves the mobile experience significantly:

**1. Web App Manifest**

Create `public/manifest.json`:
```json
{
  "name": "Shogun -- Japan Trip",
  "short_name": "Shogun",
  "description": "AI travel concierge for Japan",
  "start_url": "/dashboard",
  "display": "standalone",
  "background_color": "#1a1a2e",
  "theme_color": "#1a1a2e",
  "icons": [
    { "src": "/icon-192.png", "sizes": "192x192", "type": "image/png" },
    { "src": "/icon-512.png", "sizes": "512x512", "type": "image/png" }
  ]
}
```

**2. Meta tags in root layout**

```tsx
export const metadata: Metadata = {
  title: "Shogun -- Japan Trip",
  manifest: "/manifest.json",
  appleWebApp: {
    capable: true,
    statusBarStyle: "black-translucent",
    title: "Shogun",
  },
  themeColor: "#1a1a2e",
};
```

**3. What "standalone" mode changes**
- No browser URL bar (more screen space)
- Appears as a separate app in the task switcher
- Status bar takes `theme_color`
- Back navigation must be handled in-app (no browser back button)

---

## Performance Budgets for Mobile

### Bundle Size Targets

| Metric | Target | Why |
|--------|--------|-----|
| First Load JS | < 150 KB gzipped | 3G Japan pocket WiFi: ~1.5s parse time |
| Per-page JS | < 50 KB gzipped | Each navigation should be fast |
| Total CSS | < 30 KB gzipped | Tailwind purges unused styles |
| Largest image | < 100 KB | Hero images, map tiles handled by CDN |

### Core Web Vitals Targets

| Metric | Target | Notes |
|--------|--------|-------|
| LCP (Largest Contentful Paint) | < 2.5s | Dashboard hero card or weather widget |
| FID (First Input Delay) | < 100ms | Tab bar and filter pills must respond instantly |
| CLS (Cumulative Layout Shift) | < 0.1 | No layout jumps when ambient data loads |
| INP (Interaction to Next Paint) | < 200ms | Card taps, drawer opens |

### How to Prevent Layout Shift

The dashboard loads ambient data asynchronously. Cards that change height when data arrives cause CLS:

```tsx
// BAD: Card has no min-height, jumps when data loads
<WeatherCard data={data?.weather ?? null} loading={loading} />

// GOOD: Card reserves space with min-height (EXISTING pattern)
<div style={{
  minHeight: "140px",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
}}>
  {loading ? "Loading weather..." : <WeatherContent />}
</div>
```

The existing `WeatherCard` already does this correctly with `minHeight: "140px"`.

### Image Optimization

The codebase does not currently serve user-uploaded images, but embedded maps (Windy, Leaflet) and potential future POI photos should be optimized:

```tsx
// Next.js Image component with responsive sizing
import Image from "next/image";

<Image
  src={poi.photo_url}
  alt={poi.name_en}
  width={400}
  height={300}
  sizes="(max-width: 768px) 100vw, 50vw"  // Full width on mobile, half on desktop
  loading="lazy"
  style={{ borderRadius: "10px", objectFit: "cover" }}
/>
```

For inline images, use `loading="lazy"` and explicit `width`/`height` to prevent CLS:

```tsx
// Always specify dimensions to prevent layout shift
<img
  src={url}
  alt={alt}
  width={400}
  height={300}
  loading="lazy"
  decoding="async"
  style={{ width: "100%", height: "auto", borderRadius: "10px" }}
/>
```

---

## Japan-Specific Mobile Patterns

### Scannable, Not Scrollable

Users are standing at train stations, walking through shopping streets, or sitting in restaurants. They glance at the phone for 2-3 seconds, not 30. Design for scanning:

**Data tiles instead of paragraphs:**
```tsx
// BAD: Text block
<p>The weather today in Osaka is 18 degrees celsius with
   partly cloudy skies and a 20% chance of rain.</p>

// GOOD: Scannable tile (EXISTING WeatherCard pattern)
<div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
  <span style={{ fontSize: "2.25rem" }}>sun_emoji</span>
  <div>
    <div style={{ fontSize: "1.75rem", fontWeight: 700 }}>64 F</div>
    <div style={{ fontSize: "0.75rem", color: "#6b7280" }}>Partly cloudy</div>
  </div>
</div>
```

**Key information first:**
- Weather: temperature + icon, not a description
- Transit: status badge (normal/disruption), not a paragraph
- POIs: name + category badge + distance, not a full review
- Calendar: time + title + city badge, not notes

**Truncation with progressive disclosure:**
```tsx
// POI description -- 2-line clamp (EXISTING PoiCard pattern)
<p style={{
  display: "-webkit-box",
  WebkitLineClamp: 2,
  WebkitBoxOrient: "vertical",
  overflow: "hidden",
  fontSize: "0.8rem",
}}>
  {poi.description}
</p>
```

### Transit-Friendly Layouts

Subway trips in Japan are 5-30 minutes. Users check Shogun at the station, then lose signal. Design for pre-loading:

1. **Dashboard should load in one request** -- the ambient summary endpoint bundles weather, transit, exchange, calendar into one call. This is correct.

2. **Phrase book must work offline** -- phrases are the most critical offline feature. They should be cached aggressively or included in the service worker cache.

3. **No infinite scroll** -- paginated lists load predictably. A user at a station knows they have 3 pages of POIs, not an infinite stream that might fail mid-scroll.

4. **Time-sensitive information is prominent** -- train times, restaurant hours, and event schedules should use larger text and high contrast.

### Small Screen + Japanese Text

Japanese characters (kanji, hiragana, katakana) are visually denser than Latin text. When displaying bilingual content:

```tsx
// Name pair: English primary, Japanese secondary
<div>
  <div style={{ fontWeight: 700, fontSize: "0.95rem", color: "#111827" }}>
    {poi.name_en}
  </div>
  {poi.name_ja && (
    <div style={{ fontSize: "0.8rem", color: "#6b7280" }}>
      {poi.name_ja}
    </div>
  )}
</div>
```

- English name always first (primary user language)
- Japanese name slightly smaller, muted color
- Do NOT use smaller than `0.75rem` for Japanese text (characters become illegible)
- Kanji decorative elements (sidebar logo, hero) can be larger since they are ornamental

---

## Scroll Behavior and Overflow Handling

### App Shell Scroll Architecture

The Shogun app shell uses a fixed sidebar + scrollable main area:

```css
/* globals.css */
.app-shell {
  display: flex;
  height: 100vh;
  overflow: hidden;    /* Shell does not scroll */
}
.main-content {
  flex: 1;
  overflow-y: auto;   /* Main area scrolls */
}
```

On mobile, the sidebar is hidden and the main content fills the viewport. The bottom tab bar is fixed, and `padding-bottom: 60px` prevents content from being hidden behind it.

### Scroll Containment

When a bottom sheet or modal is open, the main content behind it should not scroll:

```tsx
// When opening a bottom sheet, lock body scroll
useEffect(() => {
  if (open) {
    document.body.style.overflow = "hidden";
    return () => { document.body.style.overflow = ""; };
  }
}, [open]);
```

### Horizontal Scroll Patterns

The mobile tab bar and city tabs use horizontal scroll:

```tsx
// MobileTabBar -- horizontal scroll with hidden scrollbar
<nav className="mobile-tab-bar" style={{ overflowX: "auto" }}>
  {/* Items with flexShrink: 0 */}
</nav>
```

For horizontal scrolling lists, hide the scrollbar on mobile:

```css
.horizontal-scroll {
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  scrollbar-width: none;           /* Firefox */
}
.horizontal-scroll::-webkit-scrollbar {
  display: none;                   /* Chrome, Safari */
}
```

### Overscroll Behavior

Prevent the "bounce" effect from interfering with bottom sheet drag gestures:

```css
.bottom-sheet {
  overscroll-behavior: contain;
}
```

### Scroll Snap for Carousels

If adding a horizontal card carousel (e.g., "Nearby POIs"):

```tsx
<div style={{
  display: "flex",
  gap: "0.75rem",
  overflowX: "auto",
  scrollSnapType: "x mandatory",
  WebkitOverflowScrolling: "touch",
  padding: "0 1rem",
}}>
  {items.map((item) => (
    <div key={item.id} style={{
      scrollSnapAlign: "start",
      minWidth: "280px",
      flexShrink: 0,
    }}>
      <Card item={item} />
    </div>
  ))}
</div>
```

---

## Font Sizing for Readability

### Size Reference from Codebase

| Element | Size | Weight | Used in |
|---------|------|--------|---------|
| Page title | `1.4-1.5rem` | 900 | Dashboard h1, POIs h1 |
| Section heading | `1rem` | 700 | Ambient section header |
| Card title | `0.95rem` | 700 | PoiCard name, drawer heading |
| Body text | `0.85rem` | 400 | Descriptions, messages |
| Small / secondary | `0.8rem` | 400 | Japanese names, filter labels |
| Meta / label | `0.7-0.75rem` | 400-700 | Timestamps, category badges |
| Tab bar label | `0.6rem` | 400 | Mobile tab bar text |
| Tiny data | `0.65rem` | 400-600 | Forecast details, section labels |

### Minimum Sizes for Mobile Readability

- **Body text:** Never below `0.8rem` (12.8px). The codebase uses `0.85rem` as the floor for readable text. Good.
- **Interactive labels:** Never below `0.75rem` (12px). Filter pills at `0.8rem` are fine.
- **Secondary/meta text:** `0.7rem` (11.2px) is the absolute floor. Used for timestamps and labels. Acceptable for non-essential info.
- **Tab bar labels at `0.6rem`:** This is small (9.6px) but acceptable because the emoji icon above it provides the primary recognition.

### Outdoor Readability

In bright sunlight, contrast matters more than size. Ensure:
- Body text uses `#4b5563` or darker on white backgrounds (ratio > 4.5:1)
- Avoid light gray text on light backgrounds outdoors
- Muted text (`#94a3b8`) is for non-essential meta only, never for actionable labels

---

## Form Input Patterns for Mobile

### Input Types and Keyboard Optimization

The chat input is the primary text entry point. Additional forms may include wishlist entries, checklist items, and settings.

```tsx
// Chat input -- text keyboard (correct)
<input type="text" inputMode="text" />

// Search -- shows search keyboard with "Search" button
<input type="search" inputMode="search" enterKeyHint="search" />

// Phone number (restaurant reservations)
<input type="tel" inputMode="tel" />

// Number entry (budget amounts)
<input type="text" inputMode="decimal" />

// URL entry
<input type="url" inputMode="url" />
```

### Autocomplete Attributes

For any forms that take user info:

```tsx
// Name fields
<input type="text" autoComplete="name" />

// Email
<input type="email" autoComplete="email" inputMode="email" />
```

### Input Focus Behavior on iOS

When an input receives focus on iOS, the page scrolls and zooms to center it. To prevent unwanted zoom:

1. Ensure `font-size >= 16px` on inputs (or `1rem` with a 16px root). The current chat input uses `0.9rem` (14.4px), which **will trigger iOS zoom**. Fix:

```tsx
// Prevent iOS zoom on focus
<input style={{
  fontSize: "16px",   // or "1rem" -- must be >= 16px
  // ... other styles
}} />
```

2. If you want to keep smaller visual font size but prevent zoom, set the viewport `maximum-scale=1` (recommended in the viewport section above).

### Enter Key Behavior

The chat input correctly handles Enter to send:

```tsx
onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && send()}
```

For multi-line inputs, use `enterKeyHint` to label the Enter key:

```tsx
<textarea enterKeyHint="send" />    // Shows "Send" label on Enter key
<input enterKeyHint="search" />     // Shows "Search" label
<input enterKeyHint="go" />         // Shows "Go" label
<input enterKeyHint="next" />       // Shows "Next" label (for multi-step forms)
```

---

## Grid and Layout Patterns for Mobile

### Single-Column Mobile, Multi-Column Desktop

The dashboard uses `gridTemplateColumns: "1fr 1fr"` which does not stack on mobile. This should be addressed:

```tsx
// Current dashboard grid -- does NOT stack on mobile
<div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem" }}>
  <TripStatusCard />
  <ShogunHealthCard />
</div>

// Better: Use auto-fill with a minimum that forces stacking on phones
<div style={{
  display: "grid",
  gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))",
  gap: "1rem",
}}>
  <TripStatusCard />
  <ShogunHealthCard />
</div>

// Or: Add a CSS class with a mobile breakpoint
// .dashboard-grid { grid-template-columns: 1fr 1fr; }
// @media (max-width: 639px) { .dashboard-grid { grid-template-columns: 1fr; } }
```

### Full-Bleed Patterns

Some elements should extend edge-to-edge on mobile (no side padding):

```tsx
// Map -- full bleed on mobile
<div style={{
  margin: "0 -1rem",     // Pull out of parent padding
  borderRadius: 0,        // No rounded corners at edges
}}>
  <PoisMap />
</div>

// Hero image -- full bleed
<div style={{
  margin: "0 -1.5rem",
  width: "calc(100% + 3rem)",
}}>
```

### Calendar Grid on Mobile

The CalendarGrid uses `minmax(160px, 1fr)` which produces 2 columns on most phones. This is good -- each day cell is 160px+ wide and shows 2 leg previews. On very small phones (320px wide), it naturally falls to 1 column.

---

## Performance Patterns

### Lazy Loading Components

Heavy components (maps, charts) should be lazy-loaded:

```tsx
import dynamic from "next/dynamic";

const PoisMap = dynamic(() => import("@/components/pois/PoisMap"), {
  ssr: false,
  loading: () => (
    <div style={{
      height: "300px",
      background: "#f1f5f9",
      borderRadius: "12px",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      color: "#94a3b8",
    }}>
      Loading map...
    </div>
  ),
});
```

### Reducing Re-renders

The ChatPanel re-renders the entire message list on every new message. For long conversations, use `React.memo` on `ChatMessage`:

```tsx
const ChatMessage = React.memo(function ChatMessage({ message }: Props) {
  // ... render
});
```

### Debouncing Resize Handlers

Window resize listeners should be debounced to prevent excessive re-renders during orientation changes:

```tsx
useEffect(() => {
  let timeout: NodeJS.Timeout;
  function handleResize() {
    clearTimeout(timeout);
    timeout = setTimeout(() => {
      setIsMobile(window.innerWidth < 768);
    }, 150);
  }
  window.addEventListener("resize", handleResize);
  return () => {
    clearTimeout(timeout);
    window.removeEventListener("resize", handleResize);
  };
}, []);
```

---

## Orientation Handling

### Portrait-First Design

Shogun is designed for portrait orientation. Most layouts assume a tall, narrow viewport. However, users may rotate to landscape for:
- Viewing maps
- Reading longer content
- Showing the phone to someone else

### Landscape Considerations

When the phone rotates to landscape:
- The bottom tab bar should remain at the bottom (not move to the side)
- Grids may gain an extra column naturally via `auto-fill`
- Bottom sheets should reduce `maxHeight` to `70vh` (landscape has less vertical space)
- Safe area insets shift: `safe-area-inset-left` and `right` become relevant

```css
@media (orientation: landscape) {
  .bottom-sheet-content {
    max-height: 70vh;
  }
  .main-content {
    padding-left: env(safe-area-inset-left, 0px);
    padding-right: env(safe-area-inset-right, 0px);
  }
}
```

---

## Accessibility on Mobile

### Focus Management

When opening bottom sheets or modals, trap focus inside:

```tsx
// Set focus to the sheet's close button when it opens
const closeRef = useRef<HTMLButtonElement>(null);
useEffect(() => {
  if (open) closeRef.current?.focus();
}, [open]);
```

### Reduced Motion

Some users have "Reduce Motion" enabled. Respect it:

```css
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

### Screen Reader Labels

Interactive elements that use only icons need `aria-label`:

```tsx
// Tab bar items with emoji icons
<Link href={tab.href} aria-label={tab.label}>
  <span aria-hidden="true">{tab.icon}</span>
  {tab.label}
</Link>

// Close buttons
<button onClick={onClose} aria-label="Close">x</button>
```

---

## Anti-Patterns to Avoid

### Mobile Anti-Patterns

1. **Hover-only interactions** -- The PoiCard has `transition: "transform 0.15s"` but no visible hover state on mobile. This is fine (transitions apply to active/focus too). But never make information accessible only on hover.

2. **Tiny close buttons** -- The DayDrawer close button is `fontSize: "1.25rem"` with no explicit padding. The touch target is likely under 44px. Always add padding.

3. **Fixed 2-column grids on mobile** -- The dashboard `gridTemplateColumns: "1fr 1fr"` forces two narrow columns on a 375px phone (each column ~170px). Cards become cramped.

4. **Blocking loading states** -- Never return `null` or a full-page spinner from a client component. Show the shell with skeleton content.

5. **Input zoom on iOS** -- Any `<input>` or `<textarea>` with `font-size < 16px` triggers iOS Safari zoom on focus. Either use 16px+ or set `maximum-scale=1` on the viewport.

6. **Unsized async content** -- Images, maps, or data tiles that load without reserved height cause layout shift. Always set `minHeight` on containers that load async.

7. **Desktop-first CSS** -- Write mobile styles as the default, then add complexity at wider breakpoints. Do not write desktop styles and then override them with `max-width` media queries.

8. **Horizontal scroll without indication** -- The mobile tab bar scrolls horizontally but has no visual indicator (gradient fade, arrow, or partial item visibility). Users may not discover tabs beyond the visible area.

9. **Text selection on cards** -- Tapping and holding on a card to "peek" at it may accidentally select text. Add `user-select: none` to card containers that are primarily tap targets.

10. **Excessive padding on mobile** -- Page padding of `1.5rem` (24px) on a 375px phone leaves only 327px for content. Consider reducing to `1rem` on mobile:

```css
@media (max-width: 639px) {
  .page-content { padding: 1rem; }
}
```

---

## Detailed Reference

For breakpoint values, device dimensions, safe area CSS, and thumb zone diagrams, see:
`references/mobile-viewport.md`
