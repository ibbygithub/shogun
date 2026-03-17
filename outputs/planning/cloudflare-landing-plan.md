# Plan: Landing Page + Cloudflare Tunnel + Access
Date: 2026-03-16
Status: Approved

## Objective

Replace the immediate redirect-to-dashboard with a branded landing page using
the Shogun Concierge hero image. Wire up the Cloudflare Tunnel so `shogun.ibbytech.com`
is publicly reachable from Japan, with Google authentication enforced on all
interior routes. The landing page (`/`) is public — everything else is protected.

## Scope

**In scope:**
- Next.js route group refactor to isolate the landing page from the app shell layout
- Full-bleed landing page with hero image, Enter button (top-center), Login link (bottom-right)
- Image asset added to Next.js `public/` directory
- `cloudflared` Docker container added to platform infra compose
- `TUNNEL_TOKEN` env var wired to platform infra `.env`
- Cloudflare Access configuration instructions for Todd (browser work — not code)

**Out of scope:**
- Cloudflare Access configuration itself (Todd does this in the dashboard)
- Brenda and Madeline user seeding (blocked — no emails/Telegram IDs yet)
- Any change to the auth logic inside the app (SHOGUN_BYPASS_AUTH stays true)

## Current State

- `shogun-web-ui` root route (`/`) immediately redirects to `/dashboard`
- Root `layout.tsx` wraps ALL pages with Sidebar + MobileTabBar — landing page cannot live here
- `start-shogun.ps1` already has a Cloudflare Tunnel step (lines 26–28) calling
  `docker-compose.infra.yml up -d cloudflared` — container definition is missing
- Platform infra compose at `C:\git\work\platform\infra\compose\docker-compose.infra.yml`

## Architecture — Layout Refactor

Current structure forces sidebar on every page. Fix with Next.js App Router route groups:

```
src/app/
├── layout.tsx              ← MODIFIED: bare HTML shell only (no sidebar, no tab bar)
├── page.tsx                ← REPLACED: landing page (full-bleed, no shell)
└── (app)/
    ├── layout.tsx          ← NEW: current layout content (Sidebar + MobileTabBar)
    ├── dashboard/
    │   └── page.tsx        (moved — no URL change)
    ├── chat/
    ├── calendar/
    ├── city/[slug]/
    ├── itinerary/
    ├── planning/
    ├── phrases/
    ├── transit/
    ├── checklist/
    ├── budget/
    ├── wishlist/
    ├── pois/
    │   └── [id]/
    ├── admin/
    └── settings/
```

Route group directories (`(app)`) do not appear in URLs. All existing
page routes remain identical — no redirects needed, no links to update.

## Architecture — Cloudflare Access Policy

```
Public (no auth):  /
Protected (auth):  /dashboard, /chat, /calendar, /city/*, /planning,
                   /phrases, /transit, /checklist, /budget, /wishlist,
                   /pois, /pois/*, /itinerary, /admin, /settings
                   (and /api/*)
```

Cloudflare Access session duration: **30 days**
Rationale: 17-day trip + pre-trip dev window. One login, stays valid.

## Architecture — cloudflared Container

```yaml
cloudflared:
  image: cloudflare/cloudflared:latest
  container_name: platform-cloudflared
  restart: unless-stopped
  command: tunnel --no-autoupdate run
  environment:
    - TUNNEL_TOKEN=${TUNNEL_TOKEN}
  networks:
    - platform_net
```

Target service in Cloudflare dashboard: `http://shogun-web-ui:3000`
(container name — resolves via platform_net)

## Landing Page Design

- Full viewport (100vw × 100vh), no scroll
- Background: hero image (`/shogun-landing.png`) — `object-cover`, centered
- Enter button: top-center, semi-transparent dark pill — "Enter →" → navigates to `/dashboard`
- Login link: bottom-right corner, small white text — "Login →" → navigates to `/dashboard`
  (Cloudflare Access intercepts and triggers Google auth if no valid session)
- No sidebar, no tab bar, no app shell of any kind
- Mobile: image crops to fill — pavilion and blossoms are centered, crop is acceptable

## Phases

### Phase 1 — Next.js Route Group Refactor + Landing Page
Goal: Landing page live at localhost:3010, all existing routes unaffected
Entry criteria: None — can start immediately
Deliverables:
  - `(app)/` directory created with all existing pages moved in
  - `(app)/layout.tsx` — current sidebar layout
  - Root `layout.tsx` — bare HTML shell
  - Root `page.tsx` — landing page component
  - `public/shogun-landing.png` — image asset in place
Exit criteria: `localhost:3010` shows landing page; clicking Enter reaches dashboard;
  all existing routes load correctly with sidebar intact
Complexity: Low
Dependencies: None

### Phase 2 — cloudflared Container
Goal: `shogun.ibbytech.com` routes through the tunnel to shogun-web-ui
Entry criteria: TUNNEL_TOKEN in hand (confirmed ✅)
Deliverables:
  - cloudflared service added to `C:\git\work\platform\infra\compose\docker-compose.infra.yml`
  - `TUNNEL_TOKEN` added to platform infra `.env`
  - `.env.example` updated with `TUNNEL_TOKEN=` placeholder
Exit criteria: `docker compose up -d cloudflared` starts clean; container shows
  "Registered tunnel connection" in logs; shogun.ibbytech.com resolves
Complexity: Low
Dependencies: Phase 1 complete (landing page should be live before tunnel goes up)

### Phase 3 — Cloudflare Access Configuration (Todd — browser work)
Goal: Google auth required for all paths except `/`
Entry criteria: Phase 2 complete and tunnel verified
Deliverables (all in Cloudflare Zero Trust dashboard):
  - Access Application policy configured:
    - Protect: all paths (`*`)
    - Bypass: `/` (exact path only)
  - Session duration: 30 days
  - Identity provider: Google
  - Allowed emails: todd@[domain], [brenda email when available], [madeline email when available]
Exit criteria: `shogun.ibbytech.com` shows landing page without auth;
  clicking Enter triggers Google login; authenticated user reaches dashboard
Complexity: Low (browser UI work only)
Dependencies: Phase 2 complete

## Dependencies

- `TUNNEL_TOKEN` — confirmed in hand
- Cloudflare Zero Trust enabled on account — confirmed ✅
- `platform_net` Docker network — already exists
- `shogun-web-ui` container name on `platform_net` — already in use

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Route group refactor breaks an existing page | Low | Medium | Build + test all routes before proceeding to Phase 2 |
| cloudflared container fails to register | Low | High | Check logs immediately; TUNNEL_TOKEN mismatch is most likely cause |
| Cloudflare Access blocks the landing page unexpectedly | Low | Low | Test from incognito before declaring done; easy to fix in dashboard |
| 30-day session expires mid-trip (departs Mar 23, returns Apr 9) | None | High | 30 days from first login covers the full window |

## Open Items

- Brenda and Madeline Google email addresses — needed to complete Access policy
- Test from phone (incognito) before departure — confirm full auth flow end-to-end
