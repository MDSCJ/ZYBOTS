"""Field-update tools for Muse's forward-looking creative work.

"Creativity" for this agent includes speculative thinking: what might
happen next in AI, or in some other field. To keep that speculation
grounded rather than made up, get_field_updates pulls real recent
developments from NewsAPI before Muse extrapolates. Muse should always
present the extrapolation as its own creative speculation, clearly
separated from the sourced facts.
"""

from .news import _request

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
    return _request(
        "everything",
        {"q": query, "language": "en", "sortBy": "publishedAt"},
    )
