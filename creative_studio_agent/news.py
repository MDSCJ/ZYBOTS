"""News tools for Muse, backed by public RSS feeds."""

import requests
import xml.etree.ElementTree as ET

def fetch_google_news(base_query: str, user_query: str = "") -> dict:
    try:
        import urllib.parse
        combined_query = f"{user_query} {base_query}".strip()
        q = urllib.parse.quote_plus(combined_query)
        url = f"https://news.google.com/rss/search?q={q}&hl=en-US&gl=US&ceid=US:en"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/rss+xml, application/xml, text/xml;q=0.9, */*;q=0.8'
        }
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        
        root = ET.fromstring(resp.content)
        articles = []
        for item in root.findall('.//item')[:15]:
            articles.append({
                "title": item.findtext('title'),
                "source": "Google News",
                "published_at": item.findtext('pubDate'),
                "description": item.findtext('description'),
                "url": item.findtext('link'),
            })
        return {"status": "success", "count": len(articles), "articles": articles}
        
    except requests.exceptions.HTTPError as http_err:
        return {"status": "error", "message": f"HTTP error occurred: {http_err}"}
    except ET.ParseError as parse_err:
        return {"status": "error", "message": f"Failed to parse RSS XML. Error: {parse_err}"}
    except Exception as e:
        return {"status": "error", "message": f"RSS fetch failed: {e}"}

def get_local_news(query: str = "") -> dict:
    """Fetch recent local news for Sri Lanka / Colombo.

    Args:
        query: A topic to narrow the search.

    Returns:
        A dict with status and a list of recent articles.
    """
    return fetch_google_news("Sri Lanka", query)

def get_international_news(query: str = "") -> dict:
    """Fetch recent international / world news headlines.

    Args:
        query: Optional topic to narrow the search.

    Returns:
        A dict with status and a list of recent articles.
    """
    return fetch_google_news("World news", query)

def get_sports_news(query: str = "") -> dict:
    """Fetch recent sports news headlines.

    Args:
        query: Optional topic to narrow the search.

    Returns:
        A dict with status and a list of recent articles.
    """
    return fetch_google_news("Sports", query)
