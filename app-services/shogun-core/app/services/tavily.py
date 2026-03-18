"""
Tavily search client — routes through tavily.platform.ibbytech.com.
Used by the RAG pipeline for restaurant and local place lookups.
"""
import logging
import httpx
from app.config import settings

logger = logging.getLogger(__name__)
TIMEOUT = 15.0


async def search(
    query: str,
    domains: list[str] | None = None,
    max_results: int = 5,
) -> list[str]:
    """
    Run a Tavily web search.
    Returns a list of result snippet strings (title + content + url).
    Returns [] on any failure — callers must handle gracefully.
    """
    payload: dict = {
        "query": query,
        "max_results": max_results,
        "search_depth": "basic",
    }
    if domains:
        payload["include_domains"] = domains

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            resp = await client.post(
                f"{settings.tavily_gateway_url}/v1/search",
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()

        results = data.get("results") or []
        snippets = []
        for r in results:
            title = r.get("title", "")
            content = r.get("content", "")
            url = r.get("url", "")
            if content:
                snippet = f"{title}: {content}" if title else content
                if url:
                    snippet += f" ({url})"
                snippets.append(snippet)
        logger.info("Tavily search %r → %d results", query[:60], len(snippets))
        return snippets

    except Exception as exc:
        logger.warning("Tavily search failed for query=%r: %s", query[:60], exc)
        return []
