import httpx
import os
import logging

logger = logging.getLogger(__name__)

# Tavily gateway is the platform-tavily container.
# The endpoint is /v1/search (not /search) — confirmed from OpenAPI spec.
_TAVILY_URL = os.getenv("TAVILY_GATEWAY_URL", "http://platform-tavily:8084")


async def tavily_search(
    query: str,
    max_results: int = 5,
    search_depth: str = "basic",
    include_domains: list[str] | None = None,
) -> list[dict]:
    """Search via the platform Tavily gateway.

    Returns a list of {title, url, content, score} dicts.
    Never raises — returns empty list on any failure so callers
    can degrade gracefully.
    """
    payload: dict = {
        "query": query,
        "max_results": max_results,
        "search_depth": search_depth,
    }
    if include_domains:
        payload["include_domains"] = include_domains

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                f"{_TAVILY_URL}/v1/search",
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("results", [])
    except Exception as e:
        logger.warning("Tavily search failed for query '%s': %s", query, e)
        return []
