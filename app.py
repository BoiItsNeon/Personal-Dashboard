import os
import re
from datetime import datetime
from email.header import decode_header, make_header
from html import unescape
from html.parser import HTMLParser

import feedparser
import pandas as pd
import requests
import streamlit as st
from dotenv import load_dotenv


load_dotenv()

# Default data sources used when no local .env overrides are present.
DEFAULT_INQUIRER_FEED = "https://newsinfo.inquirer.net/feed"
DEFAULT_STOCK_MARKET_FEED = (
    "https://feeds.finance.yahoo.com/rss/2.0/headline?"
    "s=%5EGSPC,%5EDJI,%5EIXIC&region=US&lang=en-US"
)
DEFAULT_WATCH_SYMBOL = "DDD"


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
    """Decode RSS/email-style headers that may contain encoded characters."""

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


@st.cache_data(ttl=120, show_spinner=False)
def fetch_stock_history(symbol: str) -> tuple[dict[str, str | float], pd.DataFrame]:
    """Load recent Yahoo Finance chart data for the watched stock."""

    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
    response = requests.get(
        url,
        params={"range": "6mo", "interval": "1d"},
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=15,
    )
    response.raise_for_status()

    result = response.json()["chart"]["result"][0]
    meta = result["meta"]
    quote = result["indicators"]["quote"][0]

    prices = pd.DataFrame(
        {
            "Date": pd.to_datetime(result["timestamp"], unit="s"),
            "Close": quote["close"],
        }
    ).dropna()

    prices["MA20"] = prices["Close"].rolling(20).mean()
    prices["MA50"] = prices["Close"].rolling(50).mean()

    # The UI uses metadata for the metric card and the DataFrame for the chart.
    return (
        {
            "symbol": meta.get("symbol", symbol),
            "name": meta.get("shortName", symbol),
            "currency": meta.get("currency", "USD"),
            "price": float(meta.get("regularMarketPrice") or prices["Close"].iloc[-1]),
            "previous_close": float(meta.get("previousClose") or prices["Close"].iloc[-2]),
            "exchange": meta.get("exchangeName", ""),
            "market_state": meta.get("marketState", ""),
        },
        prices,
    )


def stock_signal(prices: pd.DataFrame) -> tuple[str, str]:
    """Create a simple educational trend signal from moving averages."""

    latest = prices.iloc[-1]
    close = float(latest["Close"])
    ma20 = float(latest["MA20"]) if pd.notna(latest["MA20"]) else close
    ma50 = float(latest["MA50"]) if pd.notna(latest["MA50"]) else close

    if close > ma20 > ma50:
        return (
            "Bullish watch",
            "Price is above both the 20-day and 50-day moving averages. That suggests positive momentum, but it is not a standalone reason to buy.",
        )

    if close < ma20 < ma50:
        return (
            "Bearish watch",
            "Price is below both the 20-day and 50-day moving averages. That suggests weak momentum, so caution may be warranted.",
        )

    return (
        "Neutral watch",
        "The moving averages are mixed. That usually points to an unclear trend, so waiting for a cleaner setup may be more prudent.",
    )


def render_stock_panel(symbol: str) -> None:
    """Render the stock price, trend signal, and six-month chart."""

    st.subheader(f"{symbol.upper()} Stock Watch")

    try:
        stock, prices = fetch_stock_history(symbol.upper())
    except Exception as exc:
        st.error(f"Could not load stock data: {exc}")
        return

    price = float(stock["price"])
    previous_close = float(stock["previous_close"])
    change = price - previous_close
    change_pct = (change / previous_close) * 100 if previous_close else 0
    currency = stock["currency"]
    signal, signal_reason = stock_signal(prices)

    metric_col, signal_col = st.columns([0.35, 0.65], vertical_alignment="top")
    with metric_col:
        st.metric(
            label=f"{stock['name']} ({stock['symbol']})",
            value=f"{currency} {price:,.2f}",
            delta=f"{change:+.2f} ({change_pct:+.2f}%)",
        )
        if stock["market_state"]:
            st.caption(f"{stock['exchange']} · {stock['market_state']}")

    with signal_col:
        st.markdown(f"**Signal: {signal}**")
        st.write(signal_reason)
        st.caption("Educational signal only, not personalized financial advice.")

    chart_data = prices.set_index("Date")[["Close", "MA20", "MA50"]]
    st.line_chart(chart_data, height=260)


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


def render_feed_panel(title: str, feed_url: str, limit: int) -> None:
    """Render one news column with thumbnails, headlines, and short summaries."""

    st.subheader(title)

    try:
        articles = fetch_feed_news(feed_url, limit)
    except Exception as exc:
        st.error(f"Could not load this news feed: {exc}")
        return

    if not articles:
        st.info("No articles found in the configured feed.")
        return

    for article in articles:
        title_text = article["title"]
        link = article["link"]
        published = article["published"]
        image = article["image"]

        image_col, text_col = st.columns([0.32, 0.68], vertical_alignment="top")

        with image_col:
            if image:
                st.image(image, use_container_width=True)
            else:
                st.markdown('<div class="story-placeholder">No image</div>', unsafe_allow_html=True)

        with text_col:
            if link:
                st.markdown(f"**[{title_text}]({link})**")
            else:
                st.markdown(f"**{title_text}**")

            if published:
                st.caption(published)

            if article["summary"]:
                st.write(shorten(article["summary"]))

        st.divider()


def main() -> None:
    """Configure the page layout and assemble the dashboard panels."""

    st.set_page_config(
        page_title="News and Market Dashboard",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    st.markdown(
        """
        <style>
        .block-container {
            padding-top: 2rem;
        }

        [data-testid="stMarkdownContainer"] p {
            line-height: 1.45;
        }

        .story-placeholder {
            align-items: center;
            aspect-ratio: 16 / 10;
            background: #f3f5f7;
            border: 1px solid #e4e8ed;
            border-radius: 6px;
            color: #8a94a3;
            display: flex;
            font-size: 0.8rem;
            justify-content: center;
            width: 100%;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.title("News and Market Dashboard")
    st.caption("Latest Inquirer headlines plus US stock-market news.")

    with st.sidebar:
        # Keep everyday controls visible and source URLs tucked away by default.
        st.header("Dashboard")
        st.caption("Tune how much appears on the main view.")
        inquirer_limit = st.slider("Inquirer items", min_value=3, max_value=20, value=8)
        market_limit = st.slider("Market items", min_value=3, max_value=20, value=8)

        if st.button("Refresh", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

        with st.expander("Feed sources"):
            inquirer_feed_url = st.text_input(
                "Inquirer",
                value=os.getenv("INQUIRER_FEED_URL", DEFAULT_INQUIRER_FEED),
                label_visibility="collapsed",
                placeholder="Inquirer feed URL",
            )
        market_feed_url = st.text_input(
            "US stock market",
            value=os.getenv("STOCK_MARKET_FEED_URL", DEFAULT_STOCK_MARKET_FEED),
            label_visibility="collapsed",
            placeholder="US stock market feed URL",
        )
        watch_symbol = st.text_input(
            "Stock symbol",
            value=os.getenv("WATCH_SYMBOL", DEFAULT_WATCH_SYMBOL),
            label_visibility="collapsed",
            placeholder="Stock symbol",
        )

    render_stock_panel(watch_symbol)
    st.divider()

    news_col, market_col = st.columns([1.1, 1])

    with news_col:
        render_feed_panel("News from the Inquirer", inquirer_feed_url, inquirer_limit)

    with market_col:
        render_feed_panel("US Stock Market News", market_feed_url, market_limit)


if __name__ == "__main__":
    main()
