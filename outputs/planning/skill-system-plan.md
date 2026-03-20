# Plan: IbbyTech Skill System — 11 Skills Across 3 Repos
Date: 2026-03-19
Status: Approved

## Objective

Build a minimum viable skill system that stabilizes Platform + Project Shogun
before the Japan trip (departure Mar 23). Standardize file structure across
all three repos, create 11 Claude Code skills using proper SKILL.md format
with frontmatter, and produce supporting reference documentation.

## Scope

**Included:**
- Phase 0: Structural cleanup across shogun, platform, ibbytech-foundation
- 11 Claude Code skills (proper SKILL.md format with YAML frontmatter)
- Supporting reference documents where skills need external knowledge
- Skills inventory manifest for team-orchestrator

**Excluded:**
- Runtime Python code (the "muscles" — trip-event-normalization, lodging-context-builder, etc.)
- Place taxonomy schema changes (separate planning session)
- Data loading (follows after skills + taxonomy are decided)
- shogun-core AI pipeline changes (informed by concierge-brain skill, built separately)

## Current State

### Structural Problems
- Shogun has `.agent/` AND `.claude/` — two competing config trees
- Foundation skills in `skills/` not `.claude/skills/` — won't auto-discover
- Platform duplicates all 5 foundation rule files — drift risk
- No existing skills use Claude Code SKILL.md format with frontmatter

### What Works
- 5 foundation rules (01-05) in correct `.claude/rules/` path
- 1 working agent (platform: deployment-gatekeeper)
- 1 working command (platform: register-service)
- Planning state, evidence records, and governance layer are strong

## Phase 0: Structural Cleanup

### Task 0.1 — Migrate Shogun .agent/ → .claude/

| Source | Destination |
|--------|-------------|
| `.agent/rules/00_global_safety.md` | `.claude/rules/00-global-safety.md` |
| `.agent/rules/01-system-context.md` | `.claude/rules/01-system-context.md` |
| `.agent/rules/02-integrity-gatekeeper.md` | `.claude/rules/02-integrity-gatekeeper.md` |
| `.agent/SKILLS/github-access/` | `.claude/skills/github-access/SKILL.md` + `references/` |
| `.agent/SKILLS/gateway-explorer/` | `.claude/skills/gateway-explorer/SKILL.md` |
| `.agent/assets/` | `.claude/assets/` |

After migration: delete `.agent/` directory entirely.
Add frontmatter to migrated SKILL.md files.

### Task 0.2 — Foundation Skills to .claude/skills/

| Source | Destination |
|--------|-------------|
| `skills/ciso-security.md` | `.claude/skills/ciso-security/SKILL.md` |
| `skills/dbnode-01-skill.md` | `.claude/skills/dbnode-01/SKILL.md` |

Add frontmatter to both. Keep original `skills/` directory until confirmed working.

### Task 0.3 — Platform Deduplication

Remove from platform repo:
- `.claude/rules/01-infrastructure.md` through `05-database.md`
- `.claude/skills/ciso-security.md`
- `.claude/skills/dbnode-01-skill.md`
- `.claude/templates/service-doc-template.md`

Update platform CLAUDE.md to reference foundation:
```
## Foundation Reference
Engineering standards: ../ibbytech-foundation
Launch command: claude --add-dir ../ibbytech-foundation
```

### Task 0.4 — Rename Shogun Rules (Avoid Conflicts)

Foundation rules use 01-05 numbering. Shogun's migrated rules must not collide.
Rename to project-prefixed numbers:

| File | New Name |
|------|----------|
| 00-global-safety.md | 10-shogun-global-safety.md |
| 01-system-context.md | 11-shogun-system-context.md |
| 02-integrity-gatekeeper.md | 12-shogun-integrity-gatekeeper.md |

## The 11 Skills

### Skill 1: team-orchestrator (foundation)
**Purpose:** Decompose goals into discrete agent tasks, manage parallel execution, coordinate handoffs, and assign the right skill to the right agent.
**Repo:** ibbytech-foundation
**Path:** `.claude/skills/team-orchestrator/SKILL.md`
**User-invocable:** true
**Supporting docs:** skills-inventory.md (manifest of all 11 skills with scope boundaries)
**Key knowledge areas:**
- Task decomposition patterns (when to parallelize vs sequence)
- Agent scoping (one agent per concern, no overlap)
- Dependency management between concurrent agents
- Validation checkpoints between phases
- Failure handling without cascading
- Full skills inventory with ownership boundaries
- Handoff format between agents

### Skill 2: google-places-expert (platform)
**Purpose:** Expert knowledge of all Google Places API services, field masks, pricing, category mapping, and use-case routing.
**Repo:** platform
**Path:** `.claude/skills/google-places-expert/SKILL.md`
**User-invocable:** true
**Supporting docs needed:** `references/api-catalogue.md` — full catalogue of all ~30 API services with pricing and field masks
**Key knowledge areas:**
- Place Search (Text Search, Nearby Search) — when to use which
- Place Details — field masks and cost optimization
- Place Photos — usage and attribution
- Autocomplete — session tokens for cost control
- Place Types taxonomy (~100 types) — mapping to Shogun categories
- New Places API (v1) vs legacy — which endpoints to use
- Pricing tiers and field mask cost control
- Integration with platform google-places gateway

### Skill 3: tavily-search-expert (platform)
**Purpose:** Expert knowledge of Tavily search strategies, multi-language query construction, domain-restricted search, and Japan-specific search patterns.
**Repo:** platform
**Path:** `.claude/skills/tavily-search-expert/SKILL.md`
**User-invocable:** true
**Supporting docs needed:** `references/japan-search-guide.md` — kanji/romanji term mappings, domain targets, category-specific search strategies
**Key knowledge areas:**
- Search strategies for Japan (kanji vs romanji vs English terms)
- Domain-restricted search (Tabelog, Reddit, Google Maps, TripAdvisor)
- Multi-language query construction (メガネ vs eyeglasses vs 眼鏡店)
- Relevance scoring interpretation and threshold tuning
- When to use Tavily vs Places vs Reddit vs Scraper
- Cost control (calls per search, result limits)
- Integration with platform tavily gateway
- Tabelog-specific patterns (domain search + Firecrawl extraction)

### Skill 4: frontend-design (shogun)
**Purpose:** Design system knowledge for Shogun web UI — colors, typography, component patterns, Tailwind conventions, and visual quality standards.
**Repo:** shogun
**Path:** `.claude/skills/frontend-design/SKILL.md`
**User-invocable:** true
**Supporting docs needed:** `references/design-system.md` — color palette, typography scale, component library, spacing rules
**Key knowledge areas:**
- Shogun color palette (Osaka amber, Kanazawa green, Tokyo blue, travel grey)
- Typography scale and font choices
- Component patterns (cards, tiles, panels, drawers, modals)
- Tailwind CSS conventions and utility patterns
- Dark mode handling
- Animation and transition patterns
- Image handling and lazy loading
- What "good" looks like for a travel app (reference examples)
- Accessibility basics (contrast, focus states)

### Skill 5: mobile-ux (shogun)
**Purpose:** Mobile-first design patterns for Shogun — responsive breakpoints, touch targets, viewport handling, and phone-in-Japan usage patterns.
**Repo:** shogun
**Path:** `.claude/skills/mobile-ux/SKILL.md`
**User-invocable:** true
**Supporting docs needed:** `references/mobile-viewport.md` — breakpoints, touch zones, device targets
**Key knowledge areas:**
- Responsive breakpoints (phone/tablet/desktop)
- Touch target sizing (48px minimum)
- Thumb-zone awareness for bottom navigation
- Bottom-sheet patterns for mobile detail views
- Viewport handling and safe areas
- Offline/slow-network handling for Japan transit (subway dead zones)
- Next.js responsive SSR patterns
- PWA considerations (add to home screen)
- Performance budgets for mobile (bundle size, LCP)
- Japan-specific: small screen + transit use = scannable, not scrollable

### Skill 6: concierge-brain (shogun)
**Purpose:** Define how Shogun's AI concierge should behave — system prompt architecture, context assembly, recommendation patterns, personality, and data coverage strategy.
**Repo:** shogun
**Path:** `.claude/skills/concierge-brain/SKILL.md`
**User-invocable:** true
**Key knowledge areas:**
- System prompt architecture (what to inject and when)
- Context assembly strategy (trip data + weather + time + location + knowledge)
- Response personality and tone (helpful family concierge, not generic chatbot)
- Recommendation scoring logic (proximity + relevance + time-of-day)
- Time-awareness patterns (morning vs evening recommendations differ)
- Location-awareness patterns (near-hotel vs exploring vs transit)
- Full inventory of data sources the AI should consult
- Conversation memory patterns (Valkey context, what to remember across turns)
- Function calling tool design principles
- Fallback behavior when data is sparse
- Multi-user awareness (Todd vs Brenda vs Madeline may want different things)

### Skill 7: telegram-admin (platform)
**Purpose:** Expert knowledge of Telegram Bot API capabilities, ingress patterns, message formatting, and the shogun-core integration.
**Repo:** platform
**Path:** `.claude/skills/telegram-admin/SKILL.md`
**User-invocable:** true
**Key knowledge areas:**
- Bot API capabilities (messages, inline keyboards, location, photos, voice)
- Polling vs webhook trade-offs
- Message formatting (MarkdownV2 quirks and escaping rules)
- Command registration and handling
- Location sharing payload structure
- Photo/voice message handling pipeline
- Rate limits and retry patterns
- Ingress-to-shogun-core data flow
- Error handling and user-facing error messages
- Bot menu and command list management

### Skill 8: llm-gateway-admin (platform)
**Purpose:** Expert knowledge of the LLM gateway, Gemini 2.0 Flash capabilities, function calling patterns, and prompt engineering for the Shogun use case.
**Repo:** platform
**Path:** `.claude/skills/llm-gateway-admin/SKILL.md`
**User-invocable:** true
**Key knowledge areas:**
- Gemini 2.0 Flash capabilities and limits
- Function calling declaration patterns
- System prompt engineering best practices
- Token budget management (input/output limits)
- Multimodal handling (images, voice transcription)
- Structured output (JSON mode)
- Temperature and sampling parameters
- How the LLM gateway wraps the Gemini API
- Error handling (rate limits, token overflow, malformed responses)
- Cost tracking and optimization

### Skill 9: shogun-dba (shogun)
**Purpose:** Schema knowledge for shogun_v1, migration patterns, grant management, and the place/activity category taxonomy.
**Repo:** shogun
**Path:** `.claude/skills/shogun-dba/SKILL.md`
**User-invocable:** true
**Key knowledge areas:**
- Full shogun_v1 schema reference (all tables, columns, types, constraints)
- Migration file conventions and execution patterns
- Grant management (shogun_app role, what it can access)
- Category taxonomy for places, food, shopping, activities, temples
- Query optimization patterns for trip data
- pgvector usage for embeddings
- pgcrypto usage for PII
- Backup and restore patterns
- Data validation queries (expected counts, null checks, FK integrity)
- Connection patterns (app → dbnode-01 via TCP)

### Skill 10: git-lifecycle (foundation)
**Purpose:** Branch promotion logic, merge discipline, changelog generation, README update triggers, and stale branch cleanup.
**Repo:** ibbytech-foundation
**Path:** `.claude/skills/git-lifecycle/SKILL.md`
**User-invocable:** true
**Key knowledge areas:**
- Branch promotion criteria (what must be true before develop → main)
- Changelog generation patterns
- README update triggers (when code changes require doc updates)
- PR description quality standards
- Commit message intelligence beyond format spec
- Stale branch detection and cleanup workflow
- Release tagging conventions
- Post-merge validation (did the merge break anything?)
- GitHub integration (PR templates, labels, milestones)

### Skill 11: documentation-standard (foundation)
**Purpose:** When and how to update documentation — README files, PR descriptions, changelog, API docs, and evidence-to-documentation flow.
**Repo:** ibbytech-foundation
**Path:** `.claude/skills/documentation-standard/SKILL.md`
**User-invocable:** true
**Key knowledge areas:**
- README update rules (what triggers an update, what sections are required)
- PR description format and quality standards
- Changelog format (Keep a Changelog convention)
- API documentation patterns (when to update OpenAPI specs)
- Evidence-to-documentation flow (validation reports → release notes)
- Code comment standards (why not what)
- Architecture decision records (ADR) format
- Service documentation lifecycle (create → update → deprecate → decommission)

## Supporting Reference Documents

| Document | Path | Skill it supports | Priority |
|----------|------|-------------------|----------|
| Skills inventory manifest | foundation: `.claude/skills/team-orchestrator/references/skills-inventory.md` | team-orchestrator | Day 1 |
| Google Places API catalogue | platform: `.claude/skills/google-places-expert/references/api-catalogue.md` | google-places-expert | Day 1 |
| Japan search strategy guide | platform: `.claude/skills/tavily-search-expert/references/japan-search-guide.md` | tavily-search-expert | Day 1 |
| Shogun design system spec | shogun: `.claude/skills/frontend-design/references/design-system.md` | frontend-design | Day 1 |
| Mobile viewport reference | shogun: `.claude/skills/mobile-ux/references/mobile-viewport.md` | mobile-ux | Day 2 |
| Gemini function calling patterns | platform: `.claude/skills/llm-gateway-admin/references/function-calling.md` | llm-gateway-admin | Day 2 |

## Separate Planning Sessions Needed

### Place Taxonomy (High Priority — Schedule for Day 3)
Current `knowledge_items.category` is flat. Needs two-level taxonomy covering:
- Shopping subcategories (clothing-traditional, vintage, cosplay, jewelry, cosmetics, eyewear, etc.)
- Food/cuisine types (ramen, sushi, tempura, izakaya, western, convenience, etc.)
- Temple/shrine types (shinto, buddhist, zen, power-spot)
- Activity types (museums, parks, markets, festivals, experiences)

Impacts: database schema, knowledge pipeline search terms, Google Places type mapping, AI recommendation vocabulary, UI filter design.

## Sequencing

### Day 1 — Mar 19: Structure + First 4 Skills
- Phase 0: Structural cleanup (all repos)
- Skill 1: team-orchestrator + skills inventory manifest
- Skill 2: google-places-expert + API catalogue research
- Skill 3: tavily-search-expert + Japan search guide
- Skill 4: frontend-design + design system spec

### Day 2 — Mar 20: Skills 5-8
- Skill 5: mobile-ux + viewport reference
- Skill 6: concierge-brain
- Skill 7: telegram-admin
- Skill 8: llm-gateway-admin + function calling patterns

### Day 3 — Mar 21: Skills 9-11 + Taxonomy Session
- Skill 9: shogun-dba
- Skill 10: git-lifecycle
- Skill 11: documentation-standard
- Planning session: Place taxonomy architecture

### Day 4 — Mar 22: Data Load + Dry Run
- Load trip data using new taxonomy
- Dry-run travel scenarios:
  - "What should I do near the hotel tonight?"
  - "Late-night food near me within 15 minutes"
  - "Where can Brenda get prescription eyeglasses?"
  - "What shopping fits today's district?"
  - "What's the backup plan if rain hits?"
  - "What do I already have booked tomorrow?"
- Gap list and emergency fixes

## Dependencies

- Place taxonomy planning session (Day 3) must complete before Day 4 data load
- Google Places API catalogue research (Day 1) informs shogun-dba taxonomy knowledge
- team-orchestrator needs skills inventory manifest (built alongside it on Day 1)
- All structural cleanup (Phase 0) must complete before any skills are written

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Google Places API research takes longer than 2-3h | Medium | Delays skill quality | Start with top 10 most-used APIs, complete catalogue post-trip |
| Taxonomy session reveals schema changes too large for Day 4 | Medium | Data load quality reduced | Load with current flat categories, migrate to taxonomy post-trip |
| 11 skills in 3 days is too ambitious | Low | Some skills are thin | Priority order ensures highest-impact skills are done first |
| Structural cleanup breaks existing .claude/ behavior | Low | Session startup fails | Test /start-session after cleanup before proceeding |

## Out of Scope

- Runtime Python "muscles" (trip-event-normalization, lodging-context-builder, etc.) — planned separately after skills are in place
- shogun-core AI pipeline code changes — informed by concierge-brain skill, built in execution sessions
- MCP architecture — deferred post-trip
- Proxmox rebuild — post-trip
- Reddit gateway DB setup — post-trip unless time permits
