# SHOGUN_PATHS.md — Canonical Path Contract (Windows ↔ Linux)

**Status:** Authoritative  
**Scope:** All Shogun development, automation, AI agents, and deployments  
**Goal:** Eliminate path guessing and prevent structural drift

This document defines the ONLY approved directory roots and relative paths for the Shogun project. Any human, script, or AI agent that writes files must follow this contract.

---

## 1. Canonical Roots (Absolute Paths)

### Windows (Development)
- **Git root:** `C:\git\`
- **Shogun root:** `C:\git\work\shogun\`

### Linux (Deployment)
- **Git root:** `/opt/git/`
- **Shogun root:** `/opt/git/work/shogun/`

**Rule:** Never write outside the Shogun root on either OS.

---

## 2. Canonical Relative Tree (Authoritative)

All paths below are relative to `work/shogun/`.

```
docs/
  architecture/
  decisions/
  notes/

infra/
  SHOGUN_PATHS.md
  compose/        # optional: top-level compositions (future)
  deploy/         # optional: deployment scripts/runbooks (future)
  ops/            # optional: operational docs (future)

platform-services/
  telegram-ingress-service/
  google-places-service/
  web-scrape-service/

repo/
  shogun-core/
  shogun-web/
```

**Naming rule:** The correct directory name is **`telegram-ingress-service`**.

---

## 3. Allowed Write Zones

Automation and humans MAY write only within:

- `docs/**`
- `infra/**`
- `platform-services/**`
- `repo/**`

Automation MUST NOT:

- write to `C:\git\archive\` or `C:\git\vendor\`
- create new top-level directories under `C:\git\`
- invent alternate roots such as:
  - `C:\Shogun\`
  - `/srv/shogun/`
  - `/root/shogun/`

---

## 4. Path Usage Rules (No Guessing)

- Use absolute paths only to locate the canonical root.
- After the root is known, use **relative paths only**.
- If a required directory does not exist, it must be created inside the canonical tree.

---

## 5. Cross-Platform Invariance Rule

The following must remain identical on Windows and Linux:

- directory names
- relative tree structure
- file naming conventions

Only the root prefix differs:

- Windows: `C:\git\`
- Linux: `/opt/git/`

---

## 6. Primary Architecture References

- Telegram Gateway MVP1 specification:
  - `docs/architecture/telegram_gateway_mvp_1_platform_specification.md`

If any future document conflicts with this file, this file wins unless explicitly superseded by a newer version of **SHOGUN_PATHS.md**.

---

## 7. Change Control

Any change to canonical paths requires:

1. Updating this file first
2. Updating affected architecture documents
3. Applying the same change on Windows and Linux
4. Recording the change below

---

## Change Log

- 2026-01-25 — Initial canonical cross-platform path contract created

