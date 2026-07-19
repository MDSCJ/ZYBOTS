"""News tools for Muse, backed by NewsAPI.org (https://newsapi.org).

NewsAPI's /v2/top-headlines endpoint only supports a fixed list of country
codes, and Sri Lanka ("lk") is not one of them. So "local" news is fetched
via the /v2/everything endpoint with a Sri Lanka / Colombo query instead of
a country filter, while international and sports news use top-headlines,
which NewsAPI does support broadly.

Requires NEWS_API_KEY in the environment (see .env.example).
"""

import os

import requests

NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")
_BASE_URL = "https://newsapi.org/v2"

# NewsAPI source IDs for well-known international outlets. Used instead of
# a single country code so "international" isn't tied to one nation's lens.
_INTERNATIONAL_SOURCES = "bbc-news,al-jazeera-english,reuters,cnn"


def _request(endpoint: str, params: dict) -> dict:
    if not NEWS_API_KEY:
        return {
            "status": "error",
            "message": (
                "NEWS_API_KEY is not set. Get a free key at newsapi.org and "
                "add it to your .env file."
            ),
        }

    params = {**params, "apiKey": NEWS_API_KEY, "pageSize": params.get("pageSize", 8)}
    try:
        resp = requests.get(f"{_BASE_URL}/{endpoint}", params=params, timeout=10)
        data = resp.json()
    except requests.RequestException as exc:
        return {"status": "error", "message": f"Network error contacting NewsAPI: {exc}"}

    if data.get("status") != "ok":
        return {
            "status": "error",
            "message": data.get("message", "NewsAPI returned an error."),
        }

    articles = [
        {
            "title": a.get("title"),
            "source": (a.get("source") or {}).get("name"),
            "published_at": a.get("publishedAt"),
            "description": a.get("description"),
            "url": a.get("url"),
        }
        for a in data.get("articles", [])
        if a.get("title") and a.get("title") != "[Removed]"
    ]

    return {"status": "success", "count": len(articles), "articles": articles}


def get_local_news(query: str = "Sri Lanka") -> dict:
    """Fetch recent local news for Sri Lanka / Colombo.

    Args:
        query: A topic to narrow the search (e.g. "Colombo traffic",
            "Sri Lanka economy", "Sri Lanka elections"). Defaults to
            general Sri Lanka news.

    Returns:
        A dict with status and a list of recent articles (title, source,
        published_at, description, url).
    """
    search_terms = query if "sri lanka" in query.lower() or "colombo" in query.lower() else f"{query} Sri Lanka"
    return _request(
        "everything",
        {"q": search_terms, "language": "en", "sortBy": "publishedAt"},
    )


def get_international_news(query: str = "") -> dict:
    """Fetch recent international / world news headlines.

    Args:
        query: Optional topic to narrow the search (e.g. "climate summit",
            "elections", "markets"). Leave empty for general world headlines
            from major international outlets (BBC, Al Jazeera, Reuters, CNN).

    Returns:
        A dict with status and a list of recent articles.
    """
    if query:
        return _request(
            "everything",
            {"q": query, "language": "en", "sortBy": "publishedAt"},
        )
    return _request("top-headlines", {"sources": _INTERNATIONAL_SOURCES})


def get_sports_news(query: str = "") -> dict:
    """Fetch recent sports news headlines.

    Args:
        query: Optional topic to narrow the search (e.g. "cricket",
            "Sri Lanka cricket", "Premier League", "Formula 1"). Leave
            empty for general top sports headlines.

    Returns:
        A dict with status and a list of recent articles.
    """
    if query:
        return _request(
            "everything",
            {"q": query, "language": "en", "sortBy": "publishedAt"},
        )
    return _request("top-headlines", {"category": "sports", "language": "en", "country": "us"})
