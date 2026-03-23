# Execution Brief 5 — Text Handler + LLM + Tools + RAG Instrumentation

**Agent:** Coding agent on ibbytech-laptop (Windows 11)
**Target:** shogun-core source code
**Dependencies:** Exec Brief 4 must be complete (conversation_logger.py exists)
**Plan ref:** outputs/planning/conversation-logging-plan.md (Approved)

---

## Task

Instrument the primary text conversation path so every Telegram text message
produces a complete JSONL audit record with: user message, full system prompt,
LLM request/response payloads, tool calls with full args/results, RAG routing
decisions, and timing.

---

## File 1: MODIFY — `app-services/shogun-core/app/handlers/text.py`

### Change 1: Add import (after existing imports)

After line 14 (`from app.valkey_client import ...`), add:

```python
from app.services.conversation_logger import log_field, log_section
```

### Change 2: Log user message and system prompt

In the `handle()` function, after line 64 (`system_prompt = build_system_prompt(user, prefs, weather_str=weather_str)`),
add these lines:

```python
    # Audit: capture user message and system prompt
    log_field("user_message", text)
    log_field("system_prompt", system_prompt)
    log_field("conversation_history_length", len(history))
    log_field("conversation_history", history[-6:])  # Last 3 turns for context
    log_field("city_context", city)
    log_field("translate_mode", bool(get_translate_mode(telegram_user_id)))
```

### Change 3: Log /research path

In the `/research` block, after line 87 (`reply = await forced_research(...)`), add:

```python
        log_field("route", "forced_research")
        log_field("research_query", query)
```

### Change 4: Log main chat_with_tools path

After line 97 (`reply = await chat_with_tools(...)`), add:

```python
    log_field("route", "chat_with_tools")
```

---

## File 2: MODIFY — `app-services/shogun-core/app/services/llm.py`

### Change 1: Add import

After line 8 (`from app.config import settings`), add:

```python
from app.services.conversation_logger import log_field, log_section
```

### Change 2: Instrument the `chat()` function

Replace the `chat()` function (lines 125-162) with:

```python
async def chat(
    messages: list[dict],
    system_prompt: str,
    max_tokens: int = 600,
) -> str:
    """
    Send a chat request to the LLM gateway.
    messages: list of {role, content} — conversation history + current message.
    Returns the assistant reply text, or an error string.
    """
    payload = {
        "provider": "google",
        "model": "gemini-2.0-flash",
        "messages": [{"role": "system", "content": system_prompt}] + messages,
        "max_output_tokens": max_tokens,
    }

    # Audit: log the full LLM request
    log_section("llm_gateway_request", {
        "provider": "google",
        "model": "gemini-2.0-flash",
        "message_count": len(payload["messages"]),
        "system_prompt_length": len(system_prompt),
        "max_output_tokens": max_tokens,
        "messages": payload["messages"],
    })

    import time as _time
    _t = _time.time()

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            resp = await client.post(
                f"{settings.llm_gateway_url}/v1/chat",
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            # LLM gateway returns {"output_text": "...", "provider": ..., "model": ..., "usage": ...}
            text = data["output_text"].strip()
            # Strip any role prefix Gemini occasionally prepends
            if text.upper().startswith("ASSISTANT:"):
                text = text[10:].lstrip()

            # Audit: log the full LLM response
            log_section("llm_gateway_response", {
                "output_text": text,
                "usage": data.get("usage"),
                "latency_ms": round((_time.time() - _t) * 1000),
            })

            return text

    except httpx.TimeoutException:
        logger.error("LLM gateway timeout after %.0fs", TIMEOUT)
        log_section("llm_gateway_response", {
            "error": "timeout",
            "latency_ms": round((_time.time() - _t) * 1000),
        })
        return "Sorry, I'm taking too long to respond. Please try again."
    except Exception as exc:
        logger.error("LLM gateway error: %s", exc)
        log_section("llm_gateway_response", {
            "error": str(exc),
            "latency_ms": round((_time.time() - _t) * 1000),
        })
        return "Sorry, I couldn't reach my thinking engine right now. Please try again in a moment."
```

---

## File 3: MODIFY — `app-services/shogun-core/app/services/tools.py`

### Change 1: Add import

After line 21 (`import httpx`), add:

```python
from app.services.conversation_logger import log_field, log_section
```

### Change 2: Instrument `chat_with_tools()` — Gemini Round 1

In the `chat_with_tools()` function, after the line that builds `payload` (after line 778,
`payload["systemInstruction"] = ...`), before the Round 1 try block, add:

```python
    # Audit: log Gemini Round 1 request
    log_section("gemini_r1_request", {
        "model": GEMINI_MODEL,
        "content_count": len(contents),
        "tool_count": len(TELEGRAM_TOOLS),
        "system_prompt_length": len(system_prompt) if system_prompt else 0,
    })
```

After line 785 (`raw1 = resp.json()`), add:

```python
            # Audit: log Gemini Round 1 response
            log_section("gemini_r1_response", {
                "has_function_call": bool(_extract_function_call(raw1)),
                "has_text": bool(_extract_text(raw1)),
                "raw_candidates_count": len(raw1.get("candidates", [])),
            })
```

### Change 3: Instrument tool execution

After the existing line 815 (`logger.info("tools: executing %r args=%s", tool_name, json.dumps(tool_args)[:120])`), add:

```python
    log_field("tool_name", tool_name)
    log_field("tool_args", tool_args)
```

After the tool execution try/except block (after line 831, the last `tool_result = ...` assignment
in the except blocks), add:

```python
    # Audit: log full tool result
    import time as _time_mod
    log_section("tool_execution", {
        "tool_name": tool_name,
        "args": tool_args,
        "result_length": len(tool_result),
        "result": tool_result[:5000],  # Cap at 5KB to avoid huge log lines
    })
```

### Change 4: Instrument Gemini Round 2

After line 886 (`reply = _extract_text(resp2.json())`), add:

```python
            # Audit: log Gemini Round 2 response
            log_section("gemini_r2_response", {
                "output_text": reply[:3000] if reply else None,
                "had_verbatim_block": bool(verbatim_block),
                "had_image_url": bool(image_url),
            })
```

### Change 5: Instrument `forced_research()`

In `forced_research()`, after line 720 (`context = "\n\n---\n\n".join(parts)`), add:

```python
    # Audit: log forced research results
    log_section("forced_research", {
        "query": query,
        "city_context": city_context,
        "kb_results_found": not kb_results.startswith("No knowledge items") if kb_results else False,
        "web_results_found": bool(parts) and len(parts) > (1 if not kb_results.startswith("No knowledge items") else 0),
        "context_length": len(context),
    })
```

### Change 6: Instrument `location_triggered_places()`

In `location_triggered_places()`, after line 646 (`places_lines`... try/except),
after the if/else that builds `prompt`, add:

```python
    # Audit: log location-triggered places
    log_section("location_places", {
        "lat": lat,
        "lng": lng,
        "places_found": len(places_lines),
        "places": places_lines,
    })
```

---

## File 4: MODIFY — `app-services/shogun-core/app/services/rag.py`

### Change 1: Add import

After line 14 (`from app import db as _db`), add:

```python
from app.services.conversation_logger import log_field, log_section
```

### Change 2: Instrument the `respond()` function

After line 60 (`is_event = _is_event_query(user_query)`), add:

```python
    log_section("rag_routing", {
        "is_food_query": is_food,
        "is_event_query": is_event,
        "city_context": city_context,
        "query": user_query,
    })
```

After line 105 (`logger.info("RAG: knowledge DB returned %d result(s)..."`), add:

```python
        log_section("rag_knowledge_db", {
            "hit_count": len(kb_rows),
            "results": [{"city": r["city"], "category": r["category"],
                          "topic": r["topic"], "summary": (r["content_summary"] or "")[:200]}
                         for r in kb_rows[:10]],
        })
```

After line 77 (`logger.info("RAG: event/sakura query..."`), add:

```python
        log_field("rag_search_query", search_q)
```

After line 125 (`logger.info("RAG: knowledge DB empty — searching Tavily..."`), add:

```python
        log_field("rag_tavily_fallback", True)
        log_field("rag_tavily_query", search_q)
```

---

## Verification

After making all changes, run:

```bash
cd C:\git\work\shogun\app-services\shogun-core
python -c "
from app.handlers.text import handle
from app.services.llm import chat
from app.services.tools import chat_with_tools
from app.services.rag import respond
print('All imports OK')
"
```

---

## Done Criteria

- [ ] text.py logs user_message, system_prompt, conversation_history, route
- [ ] llm.py logs full request payload (including messages array) and full response
- [ ] tools.py logs Gemini R1 request/response, tool name/args/result, Gemini R2 response
- [ ] rag.py logs routing decisions, knowledge DB results, Tavily fallback
- [ ] Python import check passes
- [ ] No changes to function signatures or return types
