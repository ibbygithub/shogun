# Plan: Conversation Audit Logging — shogun-core (Telegram)
Date: 2026-03-22
Status: Approved

## Objective

Instrument shogun-core with full conversation audit logging so that every
Telegram interaction captures the complete data path: user message → system
prompt → LLM request → tool selection → tool execution → tool result →
LLM synthesis → reply. Logs persist to disk with daily rotation.

**Why:** Todd cannot verify whether the AI chatbot is routing to the correct
resources (knowledge DB, Tavily, Places, etc.) without seeing the full
request/response chain. He will be in Japan for 17 days relying on this
system. This is the observability floor for that to work.

## Scope

**In scope:**
- shogun-core Telegram conversation audit log (JSONL)
- Full LLM request/response payloads at shogun-core call sites
- Full tool call arguments and results
- Full system prompt text
- Daily file rotation, 30-day retention
- Docker volume mount for persistent storage on brainnode-01

**Out of scope:**
- shogun-web-api chat endpoint (Telegram is priority)
- Gateway-side logging (telegram-gateway, llm-gateway, etc.)
- Centralized log aggregation (Loki/ELK — post-trip)
- Log alerting or dashboards

## Current State

- shogun-core logs to stdout only (Docker captures, no persistence)
- LLM request/response payloads: NOT logged
- Tool execution results: NOT logged
- User message content: NOT logged
- System prompt: NOT logged
- Reply text: NOT logged
- No file-based logging, no rotation, no volume mounts

## Proposed Approach

### Architecture: Context-Scoped Conversation Log

Use Python `contextvars` to create a per-request log accumulator. Each handler
and service call appends structured data to the accumulator as it executes.
At the end of the request, the accumulated record is written as a single JSONL
line to a daily log file.

This minimizes code changes — each service adds 1-3 lines to emit data into
the context variable. No function signatures change. No return types change.

### Log Record Structure (one JSONL line per conversation turn)

```json
{
  "timestamp": "2026-03-23T10:15:32.456Z",
  "receipt_id": "abc-123",
  "telegram_user_id": 123456789,
  "user_display_name": "Todd",
  "chat_id": 123456789,
  "message_kind": "text",
  "user_message": "Where should we eat near our Airbnb tonight?",
  "system_prompt": "You are Shogun, an AI travel concierge... [full text]",
  "conversation_history": [
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."}
  ],
  "llm_request_1": {
    "provider": "google",
    "model": "gemini-2.0-flash",
    "message_count": 5,
    "system_prompt_length": 4200,
    "max_output_tokens": 2048
  },
  "llm_response_1": {
    "has_tool_call": true,
    "tool_name": "search_trip_knowledge",
    "tool_args": {"city": "osaka", "query": "restaurant near airbnb", "anchor": "osaka-airbnb"},
    "output_text": null,
    "latency_ms": 1850
  },
  "tool_execution": {
    "tool_name": "search_trip_knowledge",
    "args": {"city": "osaka", "query": "restaurant near airbnb", "anchor": "osaka-airbnb"},
    "result_summary": "5 knowledge items returned",
    "result_full": "[{\"topic\": \"Tenjinbashi ramen\", ...}]",
    "latency_ms": 45
  },
  "llm_request_2": {
    "message_count": 7,
    "includes_tool_result": true,
    "max_output_tokens": 2048
  },
  "llm_response_2": {
    "output_text": "Great question! For dinner near your Tenjinbashi Airbnb...",
    "latency_ms": 2100
  },
  "rag_path": {
    "query_type": "food_place",
    "knowledge_db_hits": 5,
    "tavily_called": false,
    "tavily_results": 0
  },
  "reply_text": "Great question! For dinner near your Tenjinbashi Airbnb...",
  "total_elapsed_ms": 4150,
  "error": null
}
```

### Log File Location and Rotation

| Setting | Value |
|---------|-------|
| Host path | `/opt/logs/shogun/conversations/` |
| Container path | `/var/log/shogun/conversations/` |
| File pattern | `conversation-YYYY-MM-DD.jsonl` |
| Rotation | Daily at midnight UTC (TimedRotatingFileHandler) |
| Retention | 30 days |
| Format | JSONL (one JSON object per line) |

### Additional Log Streams (same volume, separate files)

| File | Purpose | Contents |
|------|---------|----------|
| `conversation-YYYY-MM-DD.jsonl` | Full conversation audit | Complete round-trip per turn |
| `voice-YYYY-MM-DD.jsonl` | Voice message log | Transcription input/output, latency |
| `photo-YYYY-MM-DD.jsonl` | Photo analysis log | Analysis prompt, result, latency |
| `location-YYYY-MM-DD.jsonl` | Location trigger log | GPS, delta, nearby places result |
| `brief-YYYY-MM-DD.jsonl` | Morning brief log | Generated brief content per user |

All five handlers get their own audit trail. Same rotation policy.

## Phases

### Phase 1: Conversation Logger Module + Volume Mount
**Goal:** New `conversation_logger.py` module exists, Docker volume is mounted,
daily rotation works, and a test log line can be written on container startup.

**Entry criteria:** None — can start immediately.

**Deliverables:**
- `app/services/conversation_logger.py` — ConversationLog context var, JSONL writer, TimedRotatingFileHandler
- `app/main.py` — initialize logger on startup
- Docker compose update — volume mount `/opt/logs/shogun/conversations/`
- Startup health check writes a test entry

**Exit criteria:** Container starts, `/opt/logs/shogun/conversations/conversation-2026-03-22.jsonl` exists on brainnode-01 host with startup test entry.

**Complexity:** Low

### Phase 2: Text Handler + LLM Instrumentation
**Goal:** Every Telegram text message produces a complete JSONL audit record
with full system prompt, LLM payloads, and reply.

**Entry criteria:** Phase 1 complete.

**Deliverables:**
- `app/handlers/text.py` — capture user message, init context log, flush at end
- `app/services/llm.py` — log full request payload and response to context
- `app/services/rag.py` — log RAG routing decisions and results to context

**Exit criteria:** Send a Telegram message, verify the JSONL entry contains:
user message, full system prompt, LLM request/response, reply text, timing.

**Complexity:** Medium — most code changes are here.

### Phase 3: Tool Calling Instrumentation
**Goal:** Every tool invocation (search_trip_knowledge, find_nearby_places,
web_search, get_itinerary, get_trip_pois) logs full args and full results.

**Entry criteria:** Phase 2 complete.

**Deliverables:**
- `app/services/tools.py` — log each tool's full arguments, full result, and latency to context

**Exit criteria:** Ask a question that triggers a tool call. Verify the JSONL
entry contains tool_name, full args, full result JSON, and latency.

**Complexity:** Medium — tools.py has many executor functions.

### Phase 4: Voice, Photo, Location, Brief Handlers
**Goal:** Non-text handlers also produce audit records.

**Entry criteria:** Phase 2 complete (logger module working).

**Deliverables:**
- `app/handlers/voice.py` — transcription input/output log
- `app/handlers/photo.py` — analysis prompt/result log
- `app/handlers/location.py` — GPS, delta, nearby places log
- `app/services/brief.py` — generated brief content log

**Exit criteria:** Each handler type produces a JSONL entry in its respective
log file when triggered.

**Complexity:** Low — pattern established in Phase 2, repeat for each handler.

### Phase 5: Deploy + Verify from Telegram
**Goal:** All logging live on brainnode-01. Verified end-to-end from a real
Telegram conversation.

**Entry criteria:** Phases 1-4 complete.

**Deliverables:**
- Git push to develop
- SSH to brainnode-01, git pull, docker compose build + up
- Create `/opt/logs/shogun/conversations/` on brainnode-01 host
- Send 3 test messages covering: plain text, tool-triggering question, voice/photo
- Verify all JSONL files populated with correct data

**Exit criteria:** Todd can SSH to brainnode-01 and run:
```bash
cat /opt/logs/shogun/conversations/conversation-2026-03-22.jsonl | jq .
```
and see complete conversation audit records.

**Complexity:** Low — deployment is standard git pull + compose rebuild.

## Dependencies

- brainnode-01 must have `/opt/logs/shogun/conversations/` created (devops-agent)
- Docker compose must be updated with volume mount before deploy
- No new Python dependencies — uses stdlib `logging` + `contextvars` + `json`

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Full system prompt in logs = large files | Medium | Low | JSONL compresses well; 30-day retention; daily rotation keeps individual files manageable |
| Logging adds latency to request path | Low | Low | File I/O is one write at end of request, not per-step. JSONL append is fast. |
| Disk fills on brainnode-01 | Low | Medium | 30-day retention cap. Monitor with df during trip. Estimate: ~50MB/day worst case = 1.5GB total. |
| Logging breaks request handler on error | Medium | High | Wrap all log writes in try/except — logging failure must never break the conversation. |
| Sensitive data in logs (user messages) | Low | Low | Single-user family system on private network. Logs on brainnode-01 only, not exposed. |

## Files Modified

| File | Change |
|------|--------|
| `app/services/conversation_logger.py` | **NEW** — ConversationLog context var, JSONL writer, rotation config |
| `app/main.py` | Initialize conversation logger on startup |
| `app/handlers/text.py` | Capture user message, init log context, flush at end |
| `app/handlers/voice.py` | Log transcription round-trip |
| `app/handlers/photo.py` | Log photo analysis round-trip |
| `app/handlers/location.py` | Log location trigger + nearby results |
| `app/services/llm.py` | Log full request payload and response |
| `app/services/tools.py` | Log tool args, results, latency per executor |
| `app/services/rag.py` | Log RAG routing decisions |
| `app/services/brief.py` | Log generated brief content |
| Docker compose (brainnode-01) | Add volume mount for `/opt/logs/shogun/conversations/` |

## Execution Notes

- All changes are in shogun-core only (single container rebuild)
- No database changes required
- No gateway changes required
- No new Python packages — stdlib only
- Logging failures must be wrapped in try/except — never break a conversation
- The conversation_logger module should be designed so adding a new field
  is a one-line change (dict append), not a refactor
