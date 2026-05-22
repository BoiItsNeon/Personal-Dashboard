"""Helpers for cleaning RSS HTML and extracting thumbnail images."""

import re
from email.header import decode_header, make_header
from html import unescape
from html.parser import HTMLParser

import feedparser


class FirstImageParser(HTMLParser):
    """Extract the first image URL from an HTML summary block."""

    def __init__(self) -> None:
        super().__init__()
        self.image_url = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if self.image_url or tag.lower() != "img":
            return

        attr_map = {name.lower(): value for name, value in attrs if value}
        self.image_url = attr_map.get("src", "")


def clean_header(value: str | None) -> str:
    """Decode RSS-style headers that may contain encoded characters."""

    if not value:
        return ""
    try:
        return str(make_header(decode_header(value)))
    except Exception:
        return value


def strip_html(value: str) -> str:
    """Convert feed summaries from HTML into compact plain text."""

    text = re.sub(r"<[^>]+>", " ", value)
    text = re.sub(r"\s+", " ", unescape(text))
    return text.strip()


def shorten(value: str, max_chars: int = 180) -> str:
    """Keep summaries short so the dashboard stays scannable."""

    text = strip_html(value)
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 1].rsplit(" ", 1)[0] + "..."


def first_image_from_html(value: str) -> str:
    """Find a fallback thumbnail when a feed embeds images inside summaries."""

    parser = FirstImageParser()
    try:
        parser.feed(value)
    except Exception:
        return ""
    return parser.image_url


def get_entry_image(entry: feedparser.util.FeedParserDict) -> str:
    """Look for a thumbnail across common RSS media fields."""

    for media_item in getattr(entry, "media_thumbnail", []):
        image_url = media_item.get("url", "")
        if image_url:
            return image_url

    for media_item in getattr(entry, "media_content", []):
        image_url = media_item.get("url", "")
        medium = media_item.get("medium", "")
        media_type = media_item.get("type", "")
        if image_url and (medium == "image" or media_type.startswith("image/")):
            return image_url

    for enclosure in getattr(entry, "enclosures", []):
        image_url = enclosure.get("href", "")
        media_type = enclosure.get("type", "")
        if image_url and media_type.startswith("image/"):
            return image_url

    return first_image_from_html(getattr(entry, "summary", ""))
