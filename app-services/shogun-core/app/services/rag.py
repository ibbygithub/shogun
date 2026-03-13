"""
RAG pipeline: Tavily search → LLM synthesis.

Triggered when user asks about restaurants, food, or local places.
Injects Tabelog/web search results into the LLM context before generating a reply.
Falls through to plain LLM if Tavily returns nothing or query doesn't warrant search.
"""
import logging
from app.services import tavily as tavily_svc
from app.services.llm import chat

logger = logging.getLogger(__name__)

# Keywords that suggest a food/place query worth searching
_FOOD_KEYWORDS = {
    "restaurant", "ramen", "sushi", "izakaya", "tonkatsu", "yakiniku",
    "tempura", "udon", "soba", "katsu", "tabelog", "eat", "food",
    "lunch", "dinner", "breakfast", "cafe", "coffee", "dessert",
    "where to", "recommend", "best place", "good place", "nearby",
    "izakaya", "yakitori", "kushikatsu", "gyoza", "takoyaki",
}

_TABELOG_DOMAINS = ["tabelog.com"]


def _is_food_query(text: str) -> bool:
    lower = text.lower()
    return any(kw in lower for kw in _FOOD_KEYWORDS)


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
    if not _is_food_query(user_query):
        messages = history + [{"role": "user", "content": user_query}]
        return await chat(messages, system_prompt, max_tokens=max_tokens)

    # Build Tavily search query
    search_q = f"{user_query} Japan" if not city_context else f"{user_query} {city_context} Japan"
    logger.info("RAG: food/place query — searching Tavily: %r", search_q[:80])

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
        f"Cite notable details (ratings, prices, signatures dishes) where visible."
    )

    messages = history + [{"role": "user", "content": augmented}]
    return await chat(messages, system_prompt, max_tokens=max_tokens)
