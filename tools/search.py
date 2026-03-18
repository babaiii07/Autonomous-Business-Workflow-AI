from __future__ import annotations

from typing import Any

from config import get_settings
from utils import get_logger


log = get_logger(component="search")


def tavily_search(query: str, *, max_results: int = 5) -> list[dict[str, Any]]:
    """
    Tavily search integration.

    Uses LangChain community tool if available; otherwise returns empty list if not configured.
    """

    settings = get_settings()
    if not settings.tavily_api_key:
        return []

    try:
        # Lazy import to keep optional dependency surface small.
        from langchain_community.tools.tavily_search import TavilySearchResults  # type: ignore

        tool = TavilySearchResults(api_key=settings.tavily_api_key, max_results=max_results)
        res = tool.invoke({"query": query})
        if isinstance(res, list):
            return res
        return [{"result": res}]
    except Exception as exc:
        log.warning("tavily_search_failed", error=str(exc))
        return []

