"""RSS loading and normalization for dashboard news panels."""

from datetime import datetime

import feedparser
import streamlit as st

from dashboard.html_utils import clean_header, get_entry_image


@st.cache_data(ttl=300, show_spinner=False)
def fetch_feed_news(feed_url: str, limit: int) -> list[dict[str, str]]:
    """Fetch and normalize RSS entries for display in a news panel."""

    feed = feedparser.parse(feed_url)
    if getattr(feed, "bozo", False) and not feed.entries:
        raise RuntimeError(str(getattr(feed, "bozo_exception", "Unable to load feed")))

    items: list[dict[str, str]] = []
    for entry in feed.entries[:limit]:
        published = ""
        if getattr(entry, "published_parsed", None):
            published = datetime(*entry.published_parsed[:6]).strftime("%b %d, %Y %I:%M %p")

        items.append(
            {
                "title": clean_header(getattr(entry, "title", "Untitled")),
                "link": getattr(entry, "link", ""),
                "summary": getattr(entry, "summary", ""),
                "image": get_entry_image(entry),
                "published": published,
            }
        )
    return items
