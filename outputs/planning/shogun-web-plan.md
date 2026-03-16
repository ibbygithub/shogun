# Plan: Shogun Web — Trip Dashboard and Planning Interface
Date: 2026-03-13
Status: Approved

## Objective

Build a web-based trip planning and status interface for the Ibbotson Japan trip.
Gives Brenda a first-class editing surface for the itinerary, provides all three
travelers a unified view of the trip, and embeds Shogun AI as a web chat panel.
Accessible from home and from Japan via phone. Public exposure via Cloudflare.

This is a parallel track to shogun-core (Telegram bot). The bot and the web app
are independent — the web app failing does not affect Telegram bot operation.

---

## Scope

### IN SCOPE

- Web application: calendar, itinerary editor, dashboard, POI explorer, AI chat, wishlist
- Public access via `shogun.ibbytech.com` (Cloudflare Tunnel)
- Google account authentication via Cloudflare Access + Google IdP
- Role-based access: Todd + Brenda (admin/edit), Madeline (read + wishlist)
- Dedicated web API service (`shogun-web-api`) on svcnode-01
- Next.js frontend with CSS custom properties for swappable theming
- AI chat with separate web context (same intelligence as Telegram, different thread)
- Weather widget via Open-Meteo (no API key, free, cached)
- Madeline wishlist pipeline (Telegram or web input → research → approval → itinerary)

### OUT OF SCOPE

- Live location map (deferred — not needed for v1)
- Dark mode (deferred — adds implementation time for 3-person app)
- Native mobile app (web is mobile-first, that is sufficient)
- JR train status, flight alerts (confirmed out of scope for Shogun v1)
- Multi-language UI (Shogun responds in English; UI is English only)

---

## Approved Decisions

| Decision | Choice | Rationale |
|:---------|:-------|:----------|
| Web API backend | `shogun-web-api` FastAPI Docker on svcnode-01 | Clean separation from shogun-core; consistent with platform pattern |
| Frontend framework | Next.js (React SSR) | SSR = fast on mobile; NextAuth.js makes Google OAuth trivial |
| Authentication | Cloudflare Access + Google IdP | Auth at the edge; app never handles credentials; defense in depth |
| Public exposure | Cloudflare Tunnel (cloudflared Docker on svcnode-01) | No inbound ports; works with dynamic home IP; zero router config |
| Domain | `shogun.ibbytech.com` | Already in Cloudflare zone |
| AI chat context | Separate web context per user (Valkey key: `shogun:web:{user_id}`) | Telegram = in-the-moment; web = trip planning mode. Different use cases. |
| Weather provider | Open-Meteo | Free, no API key, no rate limits, accurate |
| CSS architecture | CSS custom properties in `globals.css`, Tailwind references variables | Theme swap = 8 variable changes, no component edits |

---

## Architecture

```
[Browser — Brenda/Todd/Madeline]
        |
        | HTTPS — shogun.ibbytech.com
        ▼
[Cloudflare Edge]
  • Cloudflare Access: Google IdP auth gate
  • Signed CF-Authorization JWT passed on every request
  • Cloudflare Tunnel: outbound from svcnode-01 (no open ports on home network)
        |
        | cloudflared tunnel
        ▼
[svcnode-01 — 192.168.71.220]
  ┌──────────────────────┐    ┌──────────────────────┐
  │  cloudflared (Docker)│    │  shogun-web-ui       │
  │  Manages tunnel      │───▶│  Next.js :3000       │
  └──────────────────────┘    │  Docker, Traefik     │
                              └──────────┬───────────┘
                                         │ REST
                              ┌──────────▼───────────┐
                              │  shogun-web-api       │
                              │  FastAPI :8090        │
                              │  Docker, Traefik     │
                              └──────────┬───────────┘
                                         │ psycopg2
                                         ▼
[dbnode-01 — 192.168.71.221]
  PostgreSQL 17 — shogun_v1
  (trip_itinerary, trip_pois, users, user_preferences, wishlist_items)

[brainnode-01 — 192.168.71.222]
  shogun-core (unchanged Telegram processor)
  + Madeline wishlist intent detection (Phase F5 addition)
```

---

## Design System

### Theme: Shogun Minimal — Japan-inspired

CSS custom properties in `globals.css` — the single file to edit for a full visual swap:

```css
:root {
  --color-primary:   #1e2d4a;   /* deep navy — navigation, headers */
  --color-accent:    #c0392b;   /* torii red — CTAs, active states */
  --color-highlight: #c9a84c;   /* warm gold — confirmed/success */
  --color-surface:   #faf9f7;   /* warm white — page background */
  --color-card:      #ffffff;   /* card backgrounds */
  --color-text:      #1a1a1a;   /* primary text */
  --color-muted:     #64748b;   /* secondary text, labels */
  --color-border:    #e2e8f0;   /* dividers, card borders */
}
```

### Calendar leg-type colors (also in CSS variables)
```css
  --leg-flight:         var(--color-highlight);  /* gold */
  --leg-accommodation:  var(--color-primary);    /* navy */
  --leg-activity:       var(--color-accent);     /* torii red */
  --leg-transit:        var(--color-muted);      /* gray */
```

### Typography
- UI text: Inter (Google Font, fallback system-ui)
- Monospace: JetBrains Mono — confirmation numbers, booking codes, addresses
- Japanese characters render via system CJK fonts — no special loading required

### Layout
- Desktop: fixed left sidebar (navy), content area (warm white), max-width 1280px
- Mobile: bottom tab bar (5 primary tabs), full-width content, no sidebar
- Cards: white, 8px radius, subtle box-shadow — no heavy borders

---

## Pages and Routes

```
/                       Redirect to /dashboard

/city/[slug]            Per-city themed entry page (tokyo, nara, osaka, kyoto)
                        Each city: unique color palette, CSS landmark overlay, city kanji
                        Sections: hero, trip context, blossom status, weather strip,
                        day itinerary teaser, top POI cards, "Ask Shogun" CTA
                        See: outputs/planning/shogun-web-city-themes.md for full spec

/dashboard              Trip status card (city, day N of 17, today's plan)
                        Weather widget (current city, 3-day strip via Open-Meteo)
                        Day-specific reminders panel (passports, cash, train tickets, etc.)
                        Shogun health (bot online, last activity)
                        Wishlist alert badge (pending approvals, Todd/Brenda only)
                        Blossom tracker strip (current city bloom status)
                        AI chat panel (collapsible on mobile, pinned on desktop)

/calendar               17-day grid Mar 23–Apr 9
                        Color-coded by leg type
                        Click any day → detail drawer (address, notes, confirmation numbers,
                        day-specific reminders for that date)
                        Edit mode (Todd/Brenda): click leg to edit, + to add, trash to delete

/itinerary              Sortable table of all legs
                        Inline edit for Todd/Brenda
                        Japanese address shown below English (tap to copy)
                        TBD dates highlighted for completion

/pois                   City tabs: Tokyo / Nara / Osaka / Kyoto / Sakai / Kanazawa
                        POI cards with tag chips
                        Filter bar: temple / food / anime / cameras / activity
                        Each card: name (EN + JA), crowd notes, best time, map link
                        Click card → /pois/[id]/knowledge (deep dive)

/pois/[id]/knowledge    POI educational deep dive page
                        Summary, practical info (best time, duration, transit)
                        YouTube search CTA (formatted query for this POI)
                        Inline "Ask Shogun about [POI]" chat entry
                        Suggested Google searches

/chat                   Full-page AI chat with Shogun
                        Separate web context per user (not shared with Telegram thread)
                        Same system prompt, same intelligence as Telegram bot
                        Web system prompt: trip concierge + educational guide mode
                        Message history persisted in Valkey (shogun:web:{user_id}, 24h TTL)

/wishlist               Madeline view: submit form (city + what she wants + notes)
                        Todd/Brenda view: approval queue
                        Each card: request text, Shogun research summary, city tag,
                        Approve / Reject / Add to itinerary buttons

/settings               Own dietary preferences, display name, notification state
                        Todd/Brenda: all users management panel
                        Telegram ID field (for linking web identity to Telegram context)

/admin                  (Todd + Brenda only)
                        shogun-core: service status, uptime, last 10 events
                        Platform services: LLM gateway, Valkey, Telegram gateway health
                        Each service: last check timestamp, response time, status badge
```

---

## New DB Schema

```sql
-- One new table required. All other tables already exist.

CREATE TABLE wishlist_items (
    id              SERIAL PRIMARY KEY,
    requested_by    INTEGER NOT NULL REFERENCES users(id),
    city            TEXT,
    description     TEXT NOT NULL,      -- what Madeline asked for
    ai_research     TEXT,               -- what Shogun found (populated by shogun-core)
    status          TEXT NOT NULL DEFAULT 'pending'
                    CHECK (status IN ('pending', 'approved', 'rejected')),
    reviewed_by     INTEGER REFERENCES users(id),
    reviewed_at     TIMESTAMPTZ,
    itinerary_note  TEXT,               -- free text added if approved
    created_utc     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_wishlist_status ON wishlist_items(status);
CREATE INDEX idx_wishlist_requested_by ON wishlist_items(requested_by);
```

---

## shogun-web-api Endpoints

```
Auth (all routes):  Read CF-Authorization JWT → map email → user + role

GET  /dashboard/status      Trip day, current city, Shogun health, pending wishlist count
GET  /weather               Current city weather + 3-day forecast (Open-Meteo, Valkey-cached 30min)
GET  /calendar              All itinerary legs, formatted for calendar component
GET  /itinerary             All legs, sortable
POST /itinerary             Add new leg (Todd/Brenda only)
PUT  /itinerary/:id         Update leg (Todd/Brenda only)
DELETE /itinerary/:id       Delete leg (Todd/Brenda only)
GET  /pois                  POIs by city + tag filter
GET  /wishlist              All wishlist items (Todd/Brenda: all; Madeline: own only)
POST /wishlist              Submit new wishlist item (any role)
PUT  /wishlist/:id/approve  Approve item (Todd/Brenda only)
PUT  /wishlist/:id/reject   Reject item (Todd/Brenda only)
POST /chat                  Send message, get response (Shogun web context)
GET  /chat/history          Load chat history for current user
GET  /admin/health          Service health for all platform components (Todd/Brenda only)
```

---

## Deployment Strategy — Internal First

Cloudflare and Google OAuth are Todd's external items. They are NOT blockers for
coding. The application is built and tested on the internal network, then
Cloudflare is wired in when ready.

**Internal target:** `http://shogun.ibbytech.com` via Pi-hole DNS → svcnode-01
**Auth bypass:** `SHOGUN_BYPASS_AUTH=true` env var → auto-login as Todd (admin)
**Production cutover:** Remove bypass, implement CF JWT parsing — all code paths
already handle auth, only the entry point changes.

---

## Phased Build Plan

### Phase F1 — Identity + Public Access
**Target: March 15**
**Goal:** `shogun.ibbytech.com` live, Google login working

Entry criteria: Cloudflare zone for ibbytech.com confirmed active
Deliverables:
- `cloudflared` Docker container on svcnode-01 (Traefik-managed)
- Cloudflare Zero Trust: tunnel created, pointing to svcnode-01
- Cloudflare Access: Google IdP configured, application policy created
- Todd's Google account confirmed through the gate
- Placeholder 200 response at `shogun.ibbytech.com` (nginx or inline FastAPI)
Exit criteria: Todd opens `shogun.ibbytech.com` on phone, sees Google login, authenticates, gets a page

---

### Phase F2 — shogun-web-api Service
**Target: March 16**
**Goal:** All backend endpoints live and returning real data

Entry criteria: Phase F1 complete, wishlist_items schema deployed to dbnode-01
Deliverables:
- `shogun-web-api` FastAPI Docker on svcnode-01
- CF-Authorization JWT parsing → user identity + role
- All itinerary, POI, dashboard, weather, and chat endpoints
- Open-Meteo weather integration with Valkey cache
- `/chat` endpoint talking to LLM gateway (Gemini 2.0 Flash)
Exit criteria: `curl` with a valid CF JWT returns itinerary JSON and a chat response

---

### Phase F3 — Next.js Shell + Calendar + Itinerary
**Target: March 19**
**Goal:** Brenda can view and edit the full trip plan on her phone

Entry criteria: Phase F2 complete
Deliverables:
- Next.js Docker on svcnode-01
- CSS custom properties design system (globals.css)
- shadcn/ui + Tailwind configured with CSS variable tokens
- `/calendar` — 17-day view, color-coded, click-to-detail, edit mode
- `/itinerary` — list view with inline edit, Japanese address display
- Mobile-responsive layout (bottom tab bar on mobile, sidebar on desktop)
Exit criteria: Brenda edits a TBD itinerary date on her phone and saves it to the DB

---

### Phase F4 — Dashboard + Weather + Chat
**Target: March 21**
**Goal:** Full dashboard operational before departure

Entry criteria: Phase F3 complete
Deliverables:
- `/dashboard` with all 4 card types (trip status, weather, Shogun health, wishlist badge)
- Weather widget (current city + 3-day strip, Open-Meteo, 30-min Valkey cache)
- AI chat panel on dashboard (collapsible on mobile)
- `/chat` full-page view
Exit criteria: Weather shows for Osaka. Chat responds with Japan trip context. Dashboard shows correct trip day.

---

### Phase F5 — POIs + Wishlist Pipeline (post-departure acceptable)
Entry criteria: Phases F1–F4 complete; Madeline has Telegram installed
Deliverables:
- `/pois` city tabs with tag filtering
- `/wishlist` submission and approval UI
- shogun-core: Madeline wishlist intent detection + LLM research + Todd/Brenda notification
Exit criteria: Madeline submits a wishlist item via web, Shogun researches it, Todd sees it in approval queue

---

### Phase F6 — Settings + Admin + Polish (post-departure)
Deliverables:
- `/settings` user management
- `/admin` service health panel
- Brenda + Madeline added to Cloudflare Access policy
- Full end-to-end test all three users
Exit criteria: All three users authenticated, correct roles enforced, Madeline cannot reach /admin

---

## Pre-F1 Checklist — Needed Before Build Starts

| Item | Owner | Status |
|:-----|:------|:-------|
| Confirm ibbytech.com DNS zone is in Cloudflare | Todd | TBD |
| Enable Cloudflare Zero Trust (free tier) | Todd | TBD |
| Create Google Cloud project, enable Identity API, get OAuth client ID + secret | Todd | TBD |
| Confirm svcnode-01 has outbound port 443 access for cloudflared | Todd | TBD |
| Brenda and Madeline Google email addresses | Todd | TBD |

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|:-----|:-----------|:-------|:-----------|
| Cloudflare Access JWT format differs from NextAuth expectations | Low | Medium | shogun-web-api handles JWT parsing; Next.js app reads role from API, not JWT directly |
| Open-Meteo API changes or goes offline | Low | Low | Weather widget fails gracefully — shows "--" not an error page |
| Next.js Docker image size slows svcnode-01 | Low | Low | Multi-stage Dockerfile; Next.js standalone output mode reduces image significantly |
| Timeline: F3 not ready by March 23 | Medium | Medium | F1+F2 alone give Brenda API access; printable itinerary (Phase 6) is the paper backup |
| Madeline wishlist (F5) not ready before departure | High | Low | F5 is explicitly post-departure acceptable; Madeline can text requests to Todd/Brenda directly |

---

## Dependencies on Other Phases

- Phase 6 (printable itinerary): can be built from the same `trip_itinerary` data; independent of web app
- Phase 7 (hardening): web app health becomes part of the hardening checklist once F3 is live
- Brenda/Madeline Telegram IDs: needed for Phase F6 (Telegram ↔ web identity linking) but NOT for F1–F4

---

## Expanded Feature Scope (Added 2026-03-13)

The following features were added during planning session. See
`outputs/planning/shogun-web-agent-brief.md` for full implementation spec.

| Feature | Phase | Priority |
|---------|-------|----------|
| Per-city themed entry pages (tokyo, nara, osaka, kyoto) | F3 expansion | P1 — visual centerpiece |
| Day-specific trip reminders (passports, cash, train tickets) | F4 expansion | P1 — practical value |
| Blossom tracker with live status per city | F4 expansion | P1 — timely for March |
| Blossom webcam links (YouTube search, not hardcoded) | F4 expansion | P2 |
| POI knowledge base deep dive pages | F5 expansion | P1 |
| YouTube search links per POI (not hardcoded embeds) | F5 expansion | P2 |
| Inline "Ask Shogun" on POI knowledge pages | F5 expansion | P1 |
| Educational chat mode (concierge + guide) | F4 expansion | P1 — system prompt update |
| Email newsletter with photo uploads | Aspirational | Deferred — needs SMTP + storage |
| Booking from chat session | Aspirational | Deferred — needs partner APIs |

---

## Out of Scope — Confirmed

- Live location map
- Dark mode
- Native mobile app
- JR train status, flight alerts
- Multi-language UI
- Shared Telegram + web chat context (separate contexts, same intelligence)
- Email newsletter (deferred — needs SMTP service and file storage)
- TikTok video embeds (platform restrictions)
- Direct booking integration (needs partner APIs)
- Hardcoded YouTube video IDs (use search links — live stream IDs change)
