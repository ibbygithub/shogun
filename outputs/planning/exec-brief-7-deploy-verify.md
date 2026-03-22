# Execution Brief 7 — Deploy Conversation Logging + Verify

**Agent:** DevOps Agent on brainnode-01
**Persona:** `devops-agent` via SSH key `~/.ssh/devops-agent_ed25519_clean`
**Target:** brainnode-01 (192.168.71.222) — shogun-core container
**Dependencies:** Exec Briefs 4-6 must be complete and committed to develop branch
**Plan ref:** outputs/planning/conversation-logging-plan.md (Approved)

---

## Task

Deploy the instrumented shogun-core to brainnode-01 and verify that conversation
audit logs are being written correctly.

---

## Pre-flight (on laptop)

Before deploying, ensure all changes from Briefs 4-6 are committed and pushed:

```bash
cd C:\git\work\shogun
git add app-services/shogun-core/app/services/conversation_logger.py
git add app-services/shogun-core/app/main.py
git add app-services/shogun-core/app/handlers/text.py
git add app-services/shogun-core/app/handlers/voice.py
git add app-services/shogun-core/app/handlers/photo.py
git add app-services/shogun-core/app/handlers/location.py
git add app-services/shogun-core/app/services/llm.py
git add app-services/shogun-core/app/services/tools.py
git add app-services/shogun-core/app/services/rag.py
git add app-services/shogun-core/app/services/brief.py
git add app-services/shogun-core/docker-compose.yml
git status
git diff --cached --stat
git commit -m "feat(logging): add conversation audit logging with daily JSONL rotation

Adds full request/response logging for the AI chatbot pipeline:
- conversation_logger.py: contextvars-based JSONL logger with daily rotation
- text handler: user message, system prompt, conversation history
- llm.py: full LLM gateway request/response payloads
- tools.py: Gemini function calling R1/R2, tool args + results
- rag.py: routing decisions, knowledge DB results, Tavily fallback
- voice/photo/location/brief: handler-specific audit fields
- Docker volume mount for /opt/logs/shogun/conversations

Co-Authored-By: Claude <noreply@anthropic.com>"

git push origin develop
```

---

## Step 1: Create log directory on brainnode-01

```bash
ssh -i ~/.ssh/devops-agent_ed25519_clean devops-agent@192.168.71.222
```

Then on brainnode-01:

```bash
sudo mkdir -p /opt/logs/shogun/conversations
sudo chown devops-agent:devops-agent /opt/logs/shogun/conversations
ls -la /opt/logs/shogun/conversations/
```

---

## Step 2: Pull and rebuild shogun-core

On brainnode-01:

```bash
cd /home/devops-agent/git-work/shogun
git pull origin develop
cd app-services/shogun-core
docker compose build
docker compose up -d
docker logs shogun-core --tail 20
```

Verify in the logs that you see:
```
Conversation audit loggers initialized → /var/log/shogun/conversations
```

---

## Step 3: Verify log files exist

On brainnode-01:

```bash
ls -la /opt/logs/shogun/conversations/
```

Expected: `conversation.jsonl` exists (startup marker was written).

```bash
cat /opt/logs/shogun/conversations/conversation.jsonl
```

Expected: One JSON line with `"event": "startup"`.

---

## Step 4: Send a test Telegram message

Send a message to the Shogun bot via Telegram. Example:
"Where should we eat near the Airbnb in Osaka?"

Then verify:

```bash
cat /opt/logs/shogun/conversations/conversation.jsonl | python3 -m json.tool
```

Or for just the latest entry:

```bash
tail -1 /opt/logs/shogun/conversations/conversation.jsonl | python3 -m json.tool
```

Expected fields in the log entry:
- `receipt_id` — present
- `telegram_user_id` — present
- `user_message` — full text of what was sent
- `system_prompt` — full system prompt text (long)
- `tool_name` — e.g., "search_trip_knowledge" or "find_nearby_places"
- `tool_args` — full argument dict
- `tool_execution.result` — full tool output
- `reply_text` — what the bot replied
- `total_elapsed_ms` — round-trip time

---

## Step 5: Verify log rotation naming

Check that the TimedRotatingFileHandler suffix is configured correctly:

```bash
ls -la /opt/logs/shogun/conversations/
```

Files should be named: `conversation.jsonl` (current), and after midnight UTC
rotation: `conversation.jsonl.2026-03-22` (previous day).

---

## Verification Checklist

- [ ] `/opt/logs/shogun/conversations/` exists on brainnode-01 with correct ownership
- [ ] shogun-core container starts with "Conversation audit loggers initialized" in logs
- [ ] `conversation.jsonl` contains startup marker
- [ ] Sending a Telegram text message produces a complete JSONL audit record
- [ ] The audit record contains: user_message, system_prompt, tool details, reply_text
- [ ] Container restart preserves existing log files (volume mount works)
- [ ] No errors in `docker logs shogun-core`

---

## Rollback

If the instrumented build causes errors:

```bash
cd /home/devops-agent/git-work/shogun
git log --oneline -5
# Find the commit before the logging commit
git checkout <previous-commit> -- app-services/shogun-core/
cd app-services/shogun-core
docker compose build && docker compose up -d
```

The logging changes are additive and wrapped in try/except — they should not
affect conversation functionality. If they do, the issue is in the import
chain, not the logging logic itself.

---

## Quick Review Command (use from Japan)

Once deployed, Todd can review conversations from his phone terminal:

```bash
ssh -i ~/.ssh/devops-agent_ed25519_clean devops-agent@192.168.71.222 \
  "tail -1 /opt/logs/shogun/conversations/conversation.jsonl | python3 -m json.tool"
```

Or see all conversations from today:

```bash
ssh -i ~/.ssh/devops-agent_ed25519_clean devops-agent@192.168.71.222 \
  "cat /opt/logs/shogun/conversations/conversation.jsonl | python3 -c \"
import sys, json
for line in sys.stdin:
    d = json.loads(line)
    if 'user_message' in d:
        print(f\\\"[{d.get('timestamp','')}] {d.get('user_display_name','?')}: {d.get('user_message','')[:80]}  → tool={d.get('tool_name','none')}\\\")
\""
```
