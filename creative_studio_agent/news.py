"""News tools for Muse, backed by public RSS feeds."""

import requests
import xml.etree.ElementTree as ET

def fetch_rss(url: str, source_name: str) -> dict:
    try:
        # Use headers to mimic a browser, some RSS feeds block standard python-requests UA
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        resp = requests.get(url, headers=headers, timeout=10)
        root = ET.fromstring(resp.content)
        articles = []
        for item in root.findall('.//item')[:15]:
            articles.append({
                "title": item.findtext('title'),
                "source": source_name,
                "published_at": item.findtext('pubDate'),
                "description": item.findtext('description'),
                "url": item.findtext('link'),
            })
        return {"status": "success", "count": len(articles), "articles": articles}
    except Exception as e:
        return {"status": "error", "message": f"RSS fetch failed: {e}"}

def get_local_news(query: str = "") -> dict:
    """Fetch recent local news for Sri Lanka / Colombo.

    Args:
        query: A topic to narrow the search. (Ignored for direct RSS fetch)

    Returns:
        A dict with status and a list of recent articles.
    """
    return fetch_rss("https://www.ada.lk/rss/latest_news/1", "Ada.lk (Sri Lanka News)")

def get_international_news(query: str = "") -> dict:
    """Fetch recent international / world news headlines.

    Args:
        query: Optional topic to narrow the search. (Ignored for direct RSS fetch)

    Returns:
        A dict with status and a list of recent articles.
    """
    return fetch_rss("https://www.dailymirror.lk/rss/breaking_news/108", "Daily Mirror (Global News)")

def get_sports_news(query: str = "") -> dict:
    """Fetch recent sports news headlines.

    Args:
        query: Optional topic to narrow the search. (Ignored for direct RSS fetch)

    Returns:
        A dict with status and a list of recent articles.
    """
    # Falling back to breaking news for sports as no specific sports RSS was provided
    return fetch_rss("https://www.dailymirror.lk/rss/breaking_news/108", "Daily Mirror (Sports/Breaking)")
