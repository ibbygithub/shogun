---
name: ai-chatbot-builder
description: >
  Architecture patterns for building AI chatbot interfaces that produce high-quality
  output with structured data — place cards, links, tables, source badges, and formatted
  lists. Use this skill when designing tool result rendering, adding new data types to
  chat responses, structuring API response shapes, building frontend message components,
  or solving the problem of LLMs reformatting pre-built content. Covers the LLM bypass
  pattern, structured side-channel responses, source transparency, and the boundary
  between LLM text generation and frontend rendering responsibility.
user-invocable: true
---

# AI Chatbot Builder — Output Architecture

## The Core Problem

AI chatbots are great at generating natural language. They are bad at producing specific, structured output — especially URLs, tables, and formatted cards — reliably and verbatim.

Gemini 2.0 Flash (and most LLMs) will reformat any tool result text into their own prose. You cannot override this with system prompt instructions. "Copy this exactly," "use this verbatim," and "do not reformat" all fail in practice. The LLM is doing what it was trained to do: synthesize and summarize.

This creates a problem when tool results contain load-bearing structured content:
- Exact URLs (Google Maps direction links that only work with correct coordinates)
- Numbered place cards with distances and walking times
- Tabular data that loses meaning when converted to prose
- Source attribution that must be precise

The solution is architecture, not prompting.

---

## Three Response Architecture Patterns

### Pattern 1: Pure LLM Text

**When to use:** The tool result is data that benefits from LLM synthesis. Search results, knowledge base snippets, recommendations from a DB — all cases where the LLM should contextualize and summarize.

**How it works:** Tool returns plain text → Gemini synthesizes a response → frontend renders markdown.

**Example:**
- `search_trip_knowledge` returns 3 knowledge base entries about ramen in Tokyo
- Gemini reads them and writes "Based on what we've saved, Fuunji in Shinjuku is worth the queue — 45-minute wait on weekdays, 90 on weekends, their tsukemen is the standout..."
- Good outcome — LLM adds value by contextualizing

### Pattern 2: Formatted Block Bypass

**When to use:** The tool result contains pre-built content that must appear verbatim — exact URLs, pre-formatted place cards, tables. You want LLM prose introduction but exact tool output for the structured part.

**How it works:** Tool returns two sections separated by sentinel markers. The backend extracts the structured section before passing to the LLM, then appends it after the LLM response.

**Implementation in Shogun (`_run_chat_with_tools` in `chat.py`):**

```python
_BLOCK_START = "##FORMATTED_BLOCK_START##"
_BLOCK_END   = "##FORMATTED_BLOCK_END##"

# In tool executor:
def _exec_find_nearby_places(args):
    # ... build results ...
    gemini_context = "Found 3 pharmacies near Osaka Airbnb..."  # LLM sees this
    formatted_block = """
1. **Matsumoto Kiyoshi Namba** (ドラッグストア)
   📍 1.2 km • ⏱ ~15 min walk
   [Walk from Osaka Airbnb →](https://www.google.com/maps/dir/...)
   [Navigate from here →](https://www.google.com/maps/dir/...)
"""
    return f"{gemini_context}\n{_BLOCK_START}\n{formatted_block}\n{_BLOCK_END}"

# In _run_chat_with_tools:
formatted_blocks = []
if _BLOCK_START in result_text and _BLOCK_END in result_text:
    bs = result_text.index(_BLOCK_START)
    be = result_text.index(_BLOCK_END)
    block_content = result_text[bs + len(_BLOCK_START):be].strip()
    formatted_blocks.append(block_content)
    gemini_text = result_text[:bs].strip()  # LLM only sees this

# After LLM responds:
if formatted_blocks:
    reply = reply.rstrip() + "\n\n" + "\n\n".join(formatted_blocks)
```

**Result:** LLM writes a natural intro ("Here are the pharmacies I found near your Airbnb:"), then the exact pre-built place cards with working direction links are appended.

**Trade-offs:**
- Pro: Works reliably without depending on LLM behavior
- Pro: URLs are always correct because the tool builds them from real coordinates
- Con: LLM's intro and the structured block may feel slightly disconnected
- Con: LLM cannot reference specific places in its intro (it never saw the formatted block)

### Pattern 3: Structured Side-Channel

**When to use:** You need maximum control over rendering — place cards with custom UI, interactive elements, maps embeds, or data that needs to be updated/filtered by the user.

**How it works:** The `/chat` API response includes a separate structured field alongside `content`. The frontend renders the structured data independently of the LLM text.

**Example API response shape:**
```json
{
  "content": "Here are the pharmacies near your Airbnb:",
  "tool_actions": [...],
  "places": [
    {
      "name": "Matsumoto Kiyoshi Namba",
      "name_ja": "マツモトキヨシ難波店",
      "distance_m": 1200,
      "walk_min": 15,
      "address": "...",
      "maps_url": "https://...",
      "dir_from_anchor": "https://www.google.com/maps/dir/?...",
      "dir_from_here": "https://www.google.com/maps/dir/?..."
    }
  ]
}
```

Frontend renders `places[]` as place cards with buttons — completely independent of what the LLM said.

**Trade-offs:**
- Pro: Full control over rendering — can add maps, thumbnails, tap-to-call, etc.
- Pro: LLM text and structured data are cleanly separated
- Pro: Frontend can filter/sort results without re-querying
- Con: Requires frontend changes (new component, new API field handling)
- Con: More complex to implement end-to-end
- Con: Place data must be extracted from tool result and added to API response shape

**This is the right long-term architecture for Shogun's place results.** Pattern 2 is the pragmatic current approach.

---

## Source Transparency: The `tool_actions` Pattern

Users need to know how the AI got its answer. Did it search the web? Did it use local knowledge? Did it just make something up from training data?

Shogun answers this with `tool_actions` badges in the chat UI.

### Pipeline

1. **Tool loop** (`_run_chat_with_tools`): Each successful tool call appends to `tool_actions`:
   ```python
   tool_actions.append({
       "tool": tool_name,
       "summary": _tool_action_summary(tool_name, args, result)
   })
   ```

2. **API response**: `tool_actions` is returned with every chat response (even `[]` for no-tool answers)

3. **Valkey storage**: `tool_actions` is stored with the assistant message:
   ```python
   assistant_entry = {
       "role": "assistant",
       "content": response_text,
       "timestamp": time.time(),
       "tool_actions": tool_actions,  # always store — even empty list
   }
   ```
   **Critical:** Use `"tool_actions": tool_actions` not `if tool_actions: ...` — empty list `[]` is a meaningful signal.

4. **History endpoint**: Return `tool_actions` whenever the key exists:
   ```python
   if "tool_actions" in h:   # NOT: if h.get("tool_actions"):
       entry["tool_actions"] = h["tool_actions"]
   ```
   The `get()` pattern is falsy for `[]` — it silently drops the "no tools called" signal.

5. **Frontend rendering** (`ChatMessage.tsx`):
   ```typescript
   const toolActions = (!isUser && message.tool_actions?.length > 0) ? message.tool_actions : null;
   const noToolsCalled = !isUser && Array.isArray(message.tool_actions) && message.tool_actions.length === 0;
   // Green badges for each tool called
   // Gray badge "No tools called — answered from conversation context" when []
   // No badge when undefined (old messages before this feature)
   ```

### Writing Good `_tool_action_summary` Strings

The summary is what users read in the badge. It should tell them:
- What resource was used
- What was searched/found
- How many results (if applicable)

```python
def _tool_action_summary(tool_name, args, result):
    if tool_name == "web_search":
        query = args.get("query", "?")
        domains = args.get("include_domains", [])
        domain_str = f" [{', '.join(domains)}]" if domains else ""
        return f"Web search{domain_str}: '{query}'"

    if tool_name == "find_nearby_places":
        query = args.get("query", "?")
        anchor = args.get("anchor") or "current accommodation"
        radius_m = args.get("radius_m") or 800
        # Count results by looking for numbered entries "1. ", "2. ", etc.
        import re
        result_count = len(re.findall(r"^\d+\. ", result or "", re.MULTILINE))
        return f"Google Places: '{query}' near {anchor} ({radius_m}m) → {result_count} results"

    if tool_name == "search_trip_knowledge":
        query = args.get("query", "?")
        return f"Knowledge base: '{query}'"
```

---

## Frontend Markdown Rendering

The web UI renders AI message content as HTML, not raw markdown. This requires a `formatContent()` function that handles markdown-to-HTML conversion safely.

### Key requirements

1. **HTML escape first, then format** — Never apply markdown patterns to unescaped text (XSS risk)
2. **Extract links before escaping** — Markdown links `[text](url)` contain URLs that would be destroyed by HTML escaping
3. **Render `<a>` tags for links** — Users must be able to click direction links without copy-paste

### Pattern from Shogun's `ChatMessage.tsx`

```typescript
function escapeHtml(text: string): string {
  return text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function formatContent(text: string): string {
  // 1. Extract markdown links BEFORE escaping — URLs contain characters that would be destroyed
  const linkPattern = /\[([^\]]+)\]\((https?:\/\/[^)]+)\)/g;
  const parts: string[] = [];
  let lastIndex = 0;
  let match;

  while ((match = linkPattern.exec(text)) !== null) {
    // HTML-escape and format the non-link text segment
    if (match.index > lastIndex) {
      parts.push(applyInlineFormatting(escapeHtml(text.slice(lastIndex, match.index))));
    }
    // Render the link as an <a> tag — sanitize href by encoding double quotes
    const linkText = escapeHtml(match[1]);
    const href = match[2].replace(/"/g, '%22');
    parts.push(`<a href="${href}" target="_blank" rel="noopener noreferrer" ...>${linkText}</a>`);
    lastIndex = match.index + match[0].length;
  }

  // Handle remaining text after last link
  if (lastIndex < text.length) {
    parts.push(applyInlineFormatting(escapeHtml(text.slice(lastIndex))));
  }

  return parts.join('');
}
```

### Inline formatting patterns

```typescript
function applyInlineFormatting(safe: string): string {
  return safe
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/`(.+?)`/g, '<code ...>$1</code>')
    .replace(/^- /gm, '• ')
    .replace(/¥([\d,]+)/g, '<span style="font-weight:600">¥$1</span>');
}
```

### Bubble CSS requirements for long content

AI responses may contain long URLs and Japanese text. Without proper overflow handling, content breaks out of chat bubbles:

```css
white-space: pre-wrap;      /* preserve line breaks */
word-break: break-word;     /* break long URLs at any character */
overflow-wrap: break-word;  /* fallback for overflow wrapping */
```

Without `word-break: break-word`, a Google Maps URL will overflow the chat bubble horizontally.

---

## Formatting Patterns for Different Content Types

### Place results
```
1. **Place Name** (Japanese Name)
   📍 1.2 km from [anchor] • ⏱ ~15 min walk
   [Walk from Anchor Name →](maps_url)
   [Navigate from here →](navigate_url)
   ★ 4.2 • Open until 22:00
```

### Recommendations list
```
**Afuri Ramen** (阿夫利) — Ebisu
- 15 min by Yamanote from Sugamo
- Yuzu shio ramen, 1,100¥/bowl
- Usually 10-20 min wait
```

### Transit instructions
```
Yamanote Line (green) from Sugamo → Ebisu: 15 min, ~200¥
```

### Search results with sources
```
From Tabelog: Kichisen (吉泉) — 3.8★, lunch from ¥3,500...
[View on Tabelog →](https://tabelog.com/...)
```

---

## Decision Guide: Which Pattern for New Content Types?

| Content type | Recommended pattern | Reason |
|-------------|--------------------|---------|
| Text answers, recommendations | Pattern 1 (LLM text) | LLM synthesis adds value |
| Places with direction links | Pattern 2 (formatted block) | Links must be exact |
| Tabular data (schedules, prices) | Pattern 2 (formatted block) | Tables break in LLM prose |
| Interactive elements (buttons, maps) | Pattern 3 (side-channel) | Requires frontend components |
| Search result summaries | Pattern 1 (LLM text) | LLM should contextualize |
| Checklist items | Pattern 1 (LLM text) | Simple state, prose is fine |
| Knowledge base search results | Pattern 1 (LLM text) | LLM summarizes and prioritizes |

---

## Common Mistakes and Fixes

**Mistake:** Instructing LLM to "copy these links exactly" via system prompt.
**Fix:** Use Pattern 2 — the LLM never sees the links.

**Mistake:** Storing `tool_actions` only when non-empty (`if tool_actions: ...`).
**Fix:** Always store — `[]` is a meaningful signal ("answered from context").

**Mistake:** Returning `tool_actions` from history only when truthy (`if h.get(...)`).
**Fix:** Use `if "tool_actions" in h:` — key presence, not truthiness.

**Mistake:** Building direction URLs with place names instead of coordinates.
**Fix:** Always use `places.location.latitude` and `longitude` from the API response.

**Mistake:** Applying a hard distance filter on top of the Places API radius.
**Fix:** Return all results sorted by haversine distance, label beyond-radius results.

**Mistake:** Rendering AI message content as raw markdown with `innerHTML` without escaping.
**Fix:** HTML-escape first, extract links before escaping, then apply formatting patterns.
