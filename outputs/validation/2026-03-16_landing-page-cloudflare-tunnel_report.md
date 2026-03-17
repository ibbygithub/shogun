# Validation Report — Landing Page + Cloudflare Tunnel
**Date:** 2026-03-16
**Task:** Landing page (full-bleed hero), Next.js route group refactor, cloudflared container

---

## Summary

Replaced the immediate `/dashboard` redirect with a branded landing page.
Refactored the Next.js layout hierarchy using route groups. Wired up the
Cloudflare Tunnel container and confirmed tunnel registration.

---

## Files Changed

### shogun repo (develop)

| File | Change |
|------|--------|
| `src/app/layout.tsx` | Stripped to bare HTML shell — no sidebar |
| `src/app/page.tsx` | Landing page — full-bleed hero image, Enter + Login buttons |
| `src/app/(app)/layout.tsx` | New — owns Sidebar + MobileTabBar for all app routes |
| `src/app/(app)/*/page.tsx` | 14 page files moved — no URL changes |
| `public/shogun-landing.png` | Hero image asset |
| `outputs/planning/cloudflare-landing-plan.md` | Plan document |

### platform repo (feature/20260315-cloudflared-reddit-laptop-mode)

| File | Change |
|------|--------|
| `infra/compose/.env.example` | Added TUNNEL_TOKEN documentation |

---

## Build Result

- **Build:** PASS — `✓ Compiled successfully`, 17/17 pages generated
- **Type check:** PASS — no TypeScript errors
- **Route manifest verified:**
  - `○ /` — 172B (landing page, static, no app shell)
  - All 16 app routes intact under `(app)/` group

---

## HTTP Verification

| URL | Expected | Result |
|-----|----------|--------|
| `http://localhost:3010/` | 200 | ✅ 200 |
| `http://localhost:3010/dashboard` | 200 | ✅ 200 |

---

## Cloudflare Tunnel

| Check | Result |
|-------|--------|
| `platform-cloudflared` container status | ✅ Running |
| Tunnel token valid | ✅ Confirmed |
| Registered connections | ✅ 4 connections (sjc10, sjc08, sjc01 + 1) |
| Target service | `http://shogun-web-ui:3000` via platform_net |

Tunnel logs confirmed:
```
Registered tunnel connection connIndex=0 location=sjc10
Registered tunnel connection connIndex=1 location=sjc10
Registered tunnel connection connIndex=2 location=sjc08
Registered tunnel connection connIndex=3 location=sjc01
```

---

## Remaining — Phase 3 (Todd, browser work)

| Item | Location | Action |
|------|----------|--------|
| Cloudflare Access policy | Zero Trust → Access → Applications | Bypass `/`, protect `*`, 30-day session |
| Allowed emails | Access policy | Add todd@[domain]; add Brenda + Madeline when available |
| End-to-end test | From phone (incognito) | Confirm Google auth → dashboard flow |
