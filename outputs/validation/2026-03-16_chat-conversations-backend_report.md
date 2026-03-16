# Validation Report — Multi-Conversation Chat Backend
**Date:** 2026-03-16
**Feature:** Multi-conversation support for shogun-web-api chat router
**File modified:** `app-services/shogun-web/shogun-web-api/routers/chat.py`

---

## Summary

Added per-conversation storage to the Shogun web chat API. Users can now maintain
multiple named conversations and switch between them. Legacy single-key history is
migrated automatically on first access.

---

## Changes Made

### New Valkey key scheme

| Key | Content | TTL |
|-----|---------|-----|
| `shogun:web:{user_id}:conversations` | JSON list of conversation metadata | 30 days |
| `shogun:web:{user_id}:chat:{conv_id}` | JSON list of messages for that conversation | 24h rolling |
| `shogun:web:{user_id}:current_conv` | Active conversation ID string | 30 days |
| `shogun:web:{user_id}:chat` | Legacy key — migrated on first access, then deleted | — |

### New helper functions

- `_conv_list_key`, `_conv_msg_key`, `_current_conv_key` — key builders
- `_load_conv_list` / `_save_conv_list` — read/write conversation metadata list
- `_get_or_create_current_conv` — resolves current conv ID; handles legacy migration
- `_load_history` / `_save_history` — updated to operate on per-conversation keys

### Migration logic

On first call to `_get_or_create_current_conv` (no `current_conv` key in Valkey):
1. Checks for legacy `shogun:web:{user_id}:chat` key
2. If found: migrates messages to new key, titles conversation "Previous conversation", deletes legacy key
3. If not found: creates a new empty conversation titled "New conversation"

### New API endpoints

| Method | Path | Behaviour |
|--------|------|-----------|
| `GET` | `/chat/conversations` | Returns conversation list + current_id |
| `POST` | `/chat/conversations` | Creates new conversation, sets as current |
| `DELETE` | `/chat/conversations/{id}` | Deletes conversation and messages; switches current if needed |
| `POST` | `/chat/conversations/{id}/activate` | Switches active conversation; returns its messages |
| `DELETE` | `/chat/history` | Clears messages in current conversation; resets title |

Existing endpoints unchanged in signature:
- `POST /chat` — sends message in current conversation
- `GET /chat/history` — returns current conversation messages

---

## Build Verification

```
docker compose build --no-cache  → SUCCESS (image built clean)
docker compose up -d             → Container started
```

---

## Functional Verification

All checks run against `http://localhost:8090` (no auth configured on test instance).

| Check | Command | Result |
|-------|---------|--------|
| GET /chat/conversations (empty) | `curl -s http://localhost:8090/chat/conversations` | `{"conversations":[],"current_id":null}` — PASS |
| POST /chat/conversations | `curl -s -X POST ...` | Returns conv object with uuid4 id — PASS |
| List shows new conversation | `curl -s http://localhost:8090/chat/conversations` | `current_id` matches created id — PASS |
| Create 2nd conversation | `curl -s -X POST ...` | New uuid, inserted at front of list — PASS |
| List shows 2+ conversations | Verified list length growing correctly — PASS |
| Activate conv1 | `curl -s -X POST .../activate` | Returns `{id, messages:[]}` — PASS |
| current_id switches | List after activate shows conv1 as current — PASS |
| Delete conv2 | `curl -s -X DELETE .../conv2` | `{"ok":true}`, conv2 removed from list — PASS |
| current_id unaffected on non-current delete | Confirmed — PASS |
| DELETE /chat/history | `curl -s -X DELETE http://localhost:8090/chat/history` | `{"ok":true}` — PASS |
| GET /chat/history after clear | Returns `[]` — PASS |
| Activate unknown conv_id | Returns `{"detail":"Conversation not found"}` (HTTP 404) — PASS |

---

## API Contract (for frontend implementation)

```
GET  /chat/conversations              → {conversations: [{id,title,created_at,last_at,message_count}], current_id}
POST /chat/conversations              → creates new, returns conv object
DELETE /chat/conversations/{id}       → deletes conversation + messages
POST /chat/conversations/{id}/activate → switches active conv, returns {id, messages:[{role,content,timestamp}]}
DELETE /chat/history                  → clears current conv messages
GET  /chat/history                    → returns current conv messages (unchanged)
POST /chat                            → send message in current conv (unchanged)
```

---

## Status

PASS — All 11 verification checks passed. Ready to commit.
