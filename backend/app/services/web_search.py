# -*- coding: utf-8 -*-
"""Web search service for LLM-assisted book classification."""

try:
    import httpx
except ImportError:
    httpx = None


# Search engine endpoints (free, no API key required)
SEARCH_ENGINES = {
    "duckduckgo": {
        "url": "https://html.duckduckgo.com/html/",
        "method": "POST",
        "params_field": "q",
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        },
    },
}


async def web_search(query: str, engine: str = "duckduckgo", max_results: int = 5) -> str:
    """Search the web and return a summary of results.

    Args:
        query: Search query string.
        engine: Search engine to use (default: duckduckgo).
        max_results: Maximum number of results to return.

    Returns:
        Formatted search results as a string.
    """
    if not httpx:
        return "[Error] httpx is not installed. Run: pip install httpx"

    if not query or not query.strip():
        return "[Error] Empty search query."

    config = SEARCH_ENGINES.get(engine)
    if not config:
        return f"[Error] Unknown search engine: {engine}. Available: {list(SEARCH_ENGINES.keys())}"

    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            if config["method"] == "POST":
                resp = await client.post(
                    config["url"],
                    data={config["params_field"]: query},
                    headers=config["headers"],
                )
            else:
                resp = await client.get(
                    config["url"],
                    params={config["params_field"]: query},
                    headers=config["headers"],
                )

            if resp.status_code != 200:
                return f"[Error] Search failed with status {resp.status_code}."

            text = resp.text
            results = _parse_ddg_results(text, max_results)

            if not results:
                return f"[No results found for '{query}'.]"

            lines = [f"Search results for '{query}':"]
            for i, r in enumerate(results, 1):
                lines.append(f"  {i}. {r['title']}")
                lines.append(f"     URL: {r['url']}")
                if r.get("snippet"):
                    lines.append(f"     {r['snippet']}")
            return "\n".join(lines)

    except httpx.TimeoutException:
        return f"[Error] Search timed out for '{query}'."
    except Exception as e:
        return f"[Error] Search failed: {e}"


def _parse_ddg_results(html: str, max_results: int) -> list:
    """Parse DuckDuckGo HTML results without BeautifulSoup."""
    results = []

    # Extract result blocks - DDG uses div.result__body or similar patterns
    # Simple regex-based extraction
    import re

    # Find all result links with titles
    # DDG HTML format: <a rel="nofollow" class="result__a" href="...">Title</a>
    link_pattern = re.compile(
        r'<a[^>]*class="result__a"[^>]*href="([^"]*)"[^>]*>(.*?)</a>',
        re.DOTALL
    )

    # Find snippets: <a class="result__snippet" ...>text</a>
    snippet_pattern = re.compile(
        r'<a[^>]*class="result__snippet"[^>]*>(.*?)</a>',
        re.DOTALL
    )

    links = link_pattern.findall(html)
    snippets = snippet_pattern.findall(html)

    for i, (url, title_html) in enumerate(links[:max_results]):
        # Clean title HTML
        title = re.sub(r'<[^>]+>', '', title_html).strip()
        if not title:
            continue

        # Clean URL - DDG uses redirect URLs
        clean_url = url
        if "uddg=" in url:
            from urllib.parse import unquote, parse_qs, urlparse
            parsed = urlparse(url)
            params = parse_qs(parsed.query)
            if "uddg" in params:
                clean_url = unquote(params["uddg"][0])

        snippet = ""
        if i < len(snippets):
            snippet = re.sub(r'<[^>]+>', '', snippets[i]).strip()

        results.append({
            "title": title,
            "url": clean_url,
            "snippet": snippet,
        })

    return results


async def search_book_info(title: str, authors: str = "") -> str:
    """Search for book information to help with classification.

    Args:
        title: Book title.
        authors: Book authors (optional).

    Returns:
        Formatted book information from web search.
    """
    query = f"{title} {authors} book category genre".strip() if authors else f"{title} book category genre"
    return await web_search(query, max_results=5)
