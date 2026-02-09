# Project Shogun  
## MVP Platform Edge + LLM Gateway Baseline — Handoff Document

**Status:** MVP-1 Closed  
**Next Phase:** MVP-2 (Knowledge & Signal Ingestion)  
**Date:** 2026-02-08  
**Audience:** Human operators, AI coding agents, future platform maintainers

---

## 1. Executive Summary

This MVP establishes a reusable **platform edge** and **LLM access layer** for Project Shogun and future AI-agent-driven applications (travel concierge, research, automation, coding, etc.).

Scope covered in this MVP:
- Traefik-based platform edge
- Custom LLM Gateway Service
- Windows-first → Git → svcnode-01 workflow
- LAN-only HTTP by design (TLS deferred)

---

## 2. Servers & Environments

### 2.1 Nodes

| Name | Role | OS |
|----|----|----|
| Laptop | Primary dev | Windows 11 |
| svcnode-01 | Platform services | Debian Linux |
| brainnode-01 | Referenced only | Linux |

### 2.2 DNS (LAN)

| Hostname | IP | Purpose |
|----|----|----|
| llm.platform.ibbytech.com | 192.168.71.220 | LLM Gateway |
| traefik.platform.ibbytech.com | 192.168.71.220 | Traefik Dashboard |

---

## 3. Repo & Directory Layout

### Windows
```
C:\git\work\shogun
```

### Linux
```
/opt/git/work/shogun
```

All changes originate on Windows and are deployed via Git.

---

## 4. Key Directories

### Infrastructure
```
infra/platform/compose/
├── docker-compose.platform.yml
├── traefik_dynamic_tls.yml
└── certs/
    └── .keep
```

### Platform Services
```
platform-services/
├── llm-gateway-service/
│   ├── Dockerfile
│   ├── app.py
│   ├── requirements.txt
│   └── .env.example
└── telegram-ingress-service/
```

---

## 5. Traefik Platform Edge

**Status:** Running and validated on LAN HTTP  
**Routes Verified:**
- http://llm.platform.ibbytech.com/health
- http://traefik.platform.ibbytech.com/dashboard/

TLS exists but is not required for MVP use.

---

## 6. LLM Gateway Service

- Abstracts OpenAI + Google Gemini
- Health endpoint validates key presence
- Outbound API calls **not yet exercised**

---

## 7. TLS Decision

**Chosen:** LAN-only HTTP until Cloudflare  
**Reason:** Avoid PKI complexity and premature infra

---

## 8. Accomplishments

- Traefik edge operational
- LLM Gateway service running
- Git hygiene enforced
- MVP-1 formally closed

---

## 9. Deferred Items

| Feature | Reason |
|------|------|
| TLS/PKI | Deferred |
| Cloudflare | Deferred |
| Google Places | MVP-2 |
| MCP wrapping | Later |

---

## 10. Hard Requirements

- Full scripts only
- No edit snippets
- Windows-first workflow
- Git before deployment
- No surprise infrastructure

---

## 11. Next Work (MVP-2)

- Google Places integration via LLM Gateway
- Validate outbound OpenAI/Gemini calls
- Wrap fast-path into MCP service

---

**End of Handoff**
