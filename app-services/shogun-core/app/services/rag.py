"""
RAG pipeline: knowledge_items DB search → Tavily fallback → LLM synthesis.

For food/place queries: checks the pre-ingested knowledge_items table first.
If the DB returns relevant results, injects them as context. Only calls Tavily
if the DB returns nothing — saving API cost and latency.

For event/sakura queries: Tavily directly (no knowledge base for live events).
Falls through to plain LLM if all sources return nothing.
"""
import logging
from app.services import tavily as tavily_svc
from app.services.llm import chat
from app import db as _db
from app.services.conversation_logger import log_field, log_section

logger = logging.getLogger(__name__)

# Keywords that suggest a food/restaurant query — use Tabelog domain restriction
_FOOD_KEYWORDS = {
    "restaurant", "ramen", "sushi", "izakaya", "tonkatsu", "yakiniku",
    "tempura", "udon", "soba", "katsu", "tabelog", "eat", "food",
    "lunch", "dinner", "breakfast", "cafe", "coffee", "dessert",
    "where to", "recommend", "best place", "good place", "nearby",
    "yakitori", "kushikatsu", "gyoza", "takoyaki",
}

# Keywords that trigger RAG but are NOT restaurant queries — use open Tavily search
_EVENT_KEYWORDS = {
    "sakura", "cherry blossom", "hanami", "bloom", "blooming", "blossoms",
    "season", "spring flowers", "weather", "forecast", "what's on",
    "events", "happening", "weekend",
}

_TABELOG_DOMAINS = ["tabelog.com"]


def _is_food_query(text: str) -> bool:
    lower = text.lower()
    return any(kw in lower for kw in _FOOD_KEYWORDS)


def _is_event_query(text: str) -> bool:
    lower = text.lower()
    return any(kw in lower for kw in _EVENT_KEYWORDS)


async def respond(
    user_query: str,
    history: list[dict],
    system_prompt: str,
    city_context: str | None = None,
    max_tokens: int = 600,
) -> str:
    """
    Generate a reply, augmenting with Tavily search if the query is food/place-related.
    history: conversation history WITHOUT the current user_query appended yet.
    Returns the assistant reply text.
    """
    is_food   = _is_food_query(user_query)
    is_event  = _is_event_query(user_query)

    log_section("rag_routing", {
        "is_food_query": is_food,
        "is_event_query": is_event,
        "city_context": city_context,
        "query": user_query,
    })

    if not is_food and not is_event:
        messages = history + [{"role": "user", "content": user_query}]
        return await chat(messages, system_prompt, max_tokens=max_tokens)

    if is_event and not is_food:
        # Sakura / events / weather queries — open Tavily search, no domain restriction
        # Include city and year in the query to get current 2026 data
        city_part = f" {city_context}" if city_context else ""
        # For sakura/bloom queries, build a targeted forecast query
        lower_q = user_query.lower()
        if any(kw in lower_q for kw in {"sakura", "cherry blossom", "hanami", "bloom",
                                         "blooming", "blossoms", "spring flowers"}):
            search_q = f"cherry blossom forecast{city_part} 2026 bloom status"
        else:
            search_q = f"{user_query}{city_part} Japan 2026"
        logger.info("RAG: event/sakura query — open Tavily search: %r", search_q[:80])
        log_field("rag_search_query", search_q)

        snippets = await tavily_svc.search(search_q, domains=None, max_results=4)

        if not snippets:
            logger.info("RAG: Tavily empty for event query — falling back to plain LLM")
            messages = history + [{"role": "user", "content": user_query}]
            return await chat(messages, system_prompt, max_tokens=max_tokens)

        context_block = "\n".join(f"- {s}" for s in snippets)
        augmented = (
            f"{user_query}\n\n"
            f"[Web search results — current 2026 data:]\n{context_block}\n\n"
            f"Use these search results to give accurate, up-to-date information. "
            f"Reference specific dates and status where visible."
        )
        messages = history + [{"role": "user", "content": augmented}]
        return await chat(messages, system_prompt, max_tokens=max_tokens)

    # Food/place query — check knowledge_items DB first, Tavily as fallback
    logger.info("RAG: food/place query — searching knowledge DB first: %r", user_query[:80])
    try:
        kb_rows = _db.search_trip_knowledge(user_query, city=city_context)
    except Exception as _exc:
        logger.warning("RAG: knowledge DB search failed: %s", _exc)
        kb_rows = []

    if kb_rows:
        logger.info("RAG: knowledge DB returned %d result(s) — skipping Tavily", len(kb_rows))
        log_section("rag_knowledge_db", {
            "hit_count": len(kb_rows),
            "results": [{"city": r["city"], "category": r["category"],
                          "topic": r["topic"], "summary": (r["content_summary"] or "")[:200]}
                         for r in kb_rows[:10]],
        })
        context_lines = []
        for row in kb_rows:
            city_label = (row["city"] or "").title() or "General"
            cat = row["category"] or ""
            topic = row["topic"] or ""
            summary = row["content_summary"] or ""
            context_lines.append(f"- [{city_label} / {cat}] {topic}: {summary}")
        context_block = "\n".join(context_lines)
        augmented = (
            f"{user_query}\n\n"
            f"[Knowledge base — pre-researched trip intelligence:]\n{context_block}\n\n"
            f"Use these results to give specific, accurate recommendations. "
            f"Cite notable details and note the area/district where visible."
        )
        messages = history + [{"role": "user", "content": augmented}]
        return await chat(messages, system_prompt, max_tokens=max_tokens)

    # Knowledge base empty — fall back to Tavily with Tabelog domain restriction
    search_q = f"{user_query} Japan" if not city_context else f"{user_query} {city_context} Japan"
    logger.info("RAG: knowledge DB empty — searching Tavily (Tabelog): %r", search_q[:80])
    log_field("rag_tavily_fallback", True)
    log_field("rag_tavily_query", search_q)

    snippets = await tavily_svc.search(search_q, domains=_TABELOG_DOMAINS, max_results=4)

    if not snippets:
        logger.info("RAG: Tavily empty — falling back to plain LLM")
        messages = history + [{"role": "user", "content": user_query}]
        return await chat(messages, system_prompt, max_tokens=max_tokens)

    context_block = "\n".join(f"- {s}" for s in snippets)
    augmented = (
        f"{user_query}\n\n"
        f"[Web search results — Tabelog/local sources:]\n{context_block}\n\n"
        f"Use these search results to give specific, accurate recommendations. "
        f"Cite notable details (ratings, prices, signature dishes) where visible."
    )

    messages = history + [{"role": "user", "content": augmented}]
    return await chat(messages, system_prompt, max_tokens=max_tokens)
