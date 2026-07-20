"""Field-update tools for Muse's forward-looking creative work.

"Creativity" for this agent includes speculative thinking: what might
happen next in AI, or in some other field. To keep that speculation
grounded rather than made up, get_field_updates pulls real recent
developments from NewsAPI before Muse extrapolates. Muse should always
present the extrapolation as its own creative speculation, clearly
separated from the sourced facts.
"""

import requests
import xml.etree.ElementTree as ET

def fetch_rss_query(query: str) -> dict:
    try:
        import urllib.parse
        q = urllib.parse.quote_plus(query)
        url = f"https://news.google.com/rss/search?q={q}&hl=en-US&gl=US&ceid=US:en"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        resp = requests.get(url, headers=headers, timeout=10)
        root = ET.fromstring(resp.content)
        articles = []
        for item in root.findall('.//item')[:10]:
            articles.append({
                "title": item.findtext('title'),
                "source": "Google News",
                "published_at": item.findtext('pubDate'),
                "description": item.findtext('description'),
                "url": item.findtext('link'),
            })
        return {"status": "success", "count": len(articles), "articles": articles}
    except Exception as e:
        return {"status": "error", "message": f"RSS fetch failed: {e}"}

# A few common fields mapped to search terms that surface substantive
# coverage rather than noise. Any other field is searched as-is.
_FIELD_QUERIES = {
    "ai": "artificial intelligence OR machine learning OR LLM",
    "technology": "technology breakthrough OR startup OR big tech",
    "science": "scientific discovery OR research breakthrough",
    "space": "space exploration OR NASA OR spacecraft",
    "climate": "climate change OR renewable energy",
    "health": "medical breakthrough OR healthcare technology",
    "finance": "markets OR economy OR fintech",
    "gaming": "video game industry OR game development",
}


def get_field_updates(field: str = "ai") -> dict:
    """Fetch recent real-world developments in a field, to ground
    future-facing creative speculation in what's actually happening now.

    Args:
        field: A field name, e.g. "ai", "technology", "science", "space",
            "climate", "health", "finance", "gaming", or any other topic —
            unrecognized fields are searched as free text.

    Returns:
        A dict with status and a list of recent articles (title, source,
        published_at, description, url). Use these as factual grounding,
        then build your own clearly-labeled speculation on top — don't
        present speculation as if it were reported news.
    """
    key = field.strip().lower()
    query = _FIELD_QUERIES.get(key, field)
    return fetch_rss_query(query)
