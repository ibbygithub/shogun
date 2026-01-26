# Shogun — AI Services Rails (Docker + MCP) To‑Do (v1)

**Goal:** Stand up reusable, home‑lab hosted AI services (MCP + APIs) that Shogun (and other agents) can call from your laptop dev environment.

**Scope for this doc:**
- ✅ OpenAI MCP server (LLM + embeddings)
- ✅ Google Gemini MCP server (LLM + embeddings)
- ✅ Google Places FastAPI wrapper (non‑MCP)
- ✅ Unstructured parsing service (Docker)
- ✅ Firecrawl web scraper (Docker)
- ⏭️ Redis queue + Postgres/pgvector later (explicitly deferred)

---

## 0) Locked Inputs (confirmed)
- **Docker host OS:** Debian 12 (Bookworm)
- **Docker host resources:** 8GB RAM, 4 CPU cores
- **Laptop ↔ lab access:** LAN-only for MVP (internal services), no public exposure
- **Ingress (future):** Cloudflare/HTTPS will front **apps** later; services may remain internal
- **Reverse proxy for MVP:** **Separate ports** (no Traefik/Nginx yet)
- **Secrets:** **Docker secrets** (keys live on the Docker host, not the laptop)
- **Shogun runtime (initial):** Runs on laptop; calls lab-hosted services via endpoints

---

## 0.1) Decision Log (authoritative)
> This log captures *explicit decisions* made during design. If something here changes, update this section first.

**2026-01-25 — Architecture & Deployment**
- Chose **Docker-first, service-oriented architecture** for all reusable AI capabilities.
- Chose **MCP only for LLMs and embeddings** (OpenAI, Gemini); avoided MCP for scraping, parsing, and Places APIs.
- Chose **separate ports per service** for MVP instead of Traefik/Nginx to reduce complexity.
- Chose **Docker secrets** over `.env` files to eliminate key sprawl and keep secrets off the laptop.
- Chose **LAN-only exposure** for all services during MVP; no public ingress.
- Deferred **Redis queue and Postgres/pgvector** until after API rails are stable.

**2026-01-25 — Runtime Model**
- Shogun runs on the **laptop first**; all heavy lifting (LLMs, embeddings, scraping, parsing, Places) lives in the home lab.
- Laptop code may only call **service endpoints**, never vendor APIs directly.

---

## 1) Repo / Folder Layout (rails first)
Create this in your Shogun repo (or a dedicated `infra/ai-services` repo):

```
shogun/
  infra/
    ai-services/
      compose/
        docker-compose.yml
      env/
        .env.example
        .env.secrets   # NOT committed
      docs/
        SERVICE_MAP.md
        RUNBOOK.md
```

### 1.1 `.env.example` (checked in)
Include names only (no secrets):
- `OPENAI_API_KEY=`
- `GEMINI_API_KEY=` (or whatever Google uses in your chosen approach)
- `GOOGLE_PLACES_API_KEY=`

### 1.2 `.env.secrets` (NOT committed)
Real keys live here on the Docker host.

---

## 2) Networking Standard (so everything is consistent)
**Decision:** one shared Docker network for all AI services.
- Network name: `ai_net`
- Everything attaches to it
- Services discover each other via container DNS name

---

## 3) OpenAI MCP Server (Docker)
### 3.1 Chosen implementation (pinned)
- Repo: **akiojin/openai-mcp-server** (Node)
- Transport: **streamable-http** (so your laptop can call it over LAN)
- Why: simple, focused (chat + list models), easy to Dockerize.

### 3.2 Deliverable
- Container exposes MCP over HTTP on `:7011` (internal/LAN only)

### 3.3 Install steps (Debian 12)
1. Create working directory:
   - `mkdir -p infra/ai-services && cd infra/ai-services`
2. Create Docker secrets (on the Docker host):
   - `printf "%s" "YOUR_OPENAI_KEY" | docker secret create openai_api_key -`
3. Add compose service (see **RUNBOOK.md** steps section below).
4. Bring up:
   - `docker compose up -d openai-mcp`

### 3.4 Validation
- `curl -s http://<DOCKER_HOST_IP>:7011/health || true`
- Run a minimal MCP client call (we’ll wire a small Python test script from laptop).

---

## 4) Google Gemini MCP Server (Docker)
### 4.1 Chosen implementation (pinned)
- Repo: **philschmid/gemini-mcp-server**
- Transport: **streamable-http**
- Why: clear env-based auth; supports both STDIO and HTTP modes.

### 4.2 Deliverable
- Container exposes MCP over HTTP on `:7012` (internal/LAN only)

### 4.3 Install steps
1. Create Docker secret:
   - `printf "%s" "YOUR_GEMINI_KEY" | docker secret create gemini_api_key -`
2. Bring up:
   - `docker compose up -d gemini-mcp`

### 4.4 Validation
- `curl -s http://<DOCKER_HOST_IP>:7012/health || true`
- Minimal prompt + embeddings test via a laptop-side script.

---

## 5) Google Places API Wrapper (FastAPI, Docker)
### 5.1 Deliverable
- A tiny internal REST API that normalizes Places responses
- Port `:7021`

### 5.2 Install steps
1. Create Docker secret:
   - `printf "%s" "YOUR_GOOGLE_PLACES_KEY" | docker secret create google_places_api_key -`
2. Add service `places-api` in compose.
3. Build + run:
   - `docker compose up -d --build places-api`

### 5.3 Validation
- `curl http://<DOCKER_HOST_IP>:7021/health`
- `curl "http://<DOCKER_HOST_IP>:7021/places/nearby?lat=...&lng=...&radius_m=500&q=coffee"`

---

## 6) Unstructured Parsing (Docker)
### 6.1 Chosen implementation
- **Unstructured API** (official repo: Unstructured-IO/unstructured-api)
- Run as a service on port `:7031`

### 6.2 Notes
- The image can be **large** and memory hungry. Start with conservative concurrency.
- Your host has **8GB RAM**—fine for MVP, but don’t hammer it.

### 6.3 Install steps
- `docker compose up -d unstructured-api`

### 6.4 Validation
- `curl http://<DOCKER_HOST_IP>:7031/health` (or service docs endpoint)

---

## 7) Firecrawl Scraper (Docker)
### 7.1 Chosen implementation
- Firecrawl self-host (official docs)
- Port `:7041`

### 7.2 Install steps
- `docker compose up -d firecrawl`

### 7.3 Validation
- `curl http://<DOCKER_HOST_IP>:7041/health`
- `POST /scrape` against a known URL and confirm markdown.

---

## 8) Integration Order (recommended)
**Day 1 rails (tomorrow):**
1. Folder layout + `.env` strategy
2. Shared Docker network
3. Boot empty containers (even if keys aren’t set yet)
4. Add health endpoints + runbooks

**Day 2 connectivity:**
5. OpenAI MCP working end-to-end
6. Gemini MCP working end-to-end

**Day 3 product data:**
7. Places wrapper working end-to-end

**Day 4 content pipeline:**
8. Firecrawl up + validated
9. Unstructured up + validated

**Day 5 glue:**
10. Define service contracts (schemas) + add client stubs in Shogun

---

## 9) Deferred (explicitly not doing first)
- Redis queue
- Postgres + pgvector
- Background worker pattern
- Caching layer

(We’ll revisit once the APIs are up and you’ve seen the request flow.)

---

## 10) Open Questions
✅ **None for MVP** — all prior questions have been answered and locked in (see Section 0).

---

## 11) Next Actions I’ll take once you answer
- Produce a single `docker-compose.yml` skeleton with:
  - shared `ai_net`
  - placeholder services for OpenAI MCP, Gemini MCP, Places API, Firecrawl, Unstructured
- Produce minimal FastAPI skeleton for Places wrapper
- Provide step-by-step bring-up + validation commands
- Provide a “first successful request” checklist

