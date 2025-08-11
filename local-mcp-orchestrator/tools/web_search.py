from __future__ import annotations

from typing import List, Dict, Any


def _ddg_search(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """Return raw search rows from DuckDuckGo.

    Uses `duckduckgo-search` when available. On failure (e.g., network blocked
    or package missing), returns a single diagnostic row instead of raising.
    """
    try:
        from duckduckgo_search import DDGS  # type: ignore
    except Exception as e:  # pragma: no cover - optional dependency at runtime
        return [
            {
                "title": "duckduckgo-search not available",
                "href": "",
                "body": f"Install duckduckgo-search or enable network. Error: {e}",
            }
        ]

    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
        return results
    except Exception as e:
        return [
            {
                "title": "Search failed",
                "href": "",
                "body": f"{type(e).__name__}: {e}",
            }
        ]


def run(query: str, max_results: int = 5) -> str:
    """Search the web using DuckDuckGo and return a concise summary string.

    Designed for use as a Tool (MCP/LangChain). Gracefully handles offline
    environments and returns a readable, bounded-length output.
    """
    query = (query or "").strip()
    if not query:
        return "[web_search] empty query"

    results = _ddg_search(query, max_results=max_results)
    if not results:
        return "[web_search] no results"

    lines: List[str] = [f"[web_search] Query: {query}"]
    for i, r in enumerate(results, 1):
        title = r.get("title") or r.get("source") or "(no title)"
        url = r.get("href") or r.get("url") or ""
        snippet = r.get("body") or r.get("text") or r.get("snippet") or ""
        snippet = snippet.replace("\n", " ").strip()
        if len(snippet) > 240:
            snippet = snippet[:240] + "…"
        lines.append(f"{i}. {title} | {url}\n   {snippet}")
    return "\n".join(lines)


if __name__ == "__main__":
    import sys
    q = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "langchain llama_cpp example"
    print(run(q))

