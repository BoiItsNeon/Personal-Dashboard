"""Reusable Streamlit UI panels for the dashboard."""

import plotly.graph_objects as go
import streamlit as st

from dashboard.html_utils import shorten
from dashboard.news import fetch_feed_news
from dashboard.stocks import fetch_stock_history, signal_description, stock_signal


def render_candlestick_chart(prices) -> None:
    """Render OHLC candles with moving-average overlays."""

    fig = go.Figure()
    fig.add_trace(
        go.Candlestick(
            x=prices["Date"],
            open=prices["Open"],
            high=prices["High"],
            low=prices["Low"],
            close=prices["Close"],
            name="Price",
            increasing_line_color="#16a34a",
            decreasing_line_color="#dc2626",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=prices["Date"],
            y=prices["MA20"],
            mode="lines",
            name="MA20",
            line={"color": "#2563eb", "width": 1.5},
        )
    )
    fig.add_trace(
        go.Scatter(
            x=prices["Date"],
            y=prices["MA50"],
            mode="lines",
            name="MA50",
            line={"color": "#9333ea", "width": 1.5},
        )
    )
    fig.update_layout(
        height=320,
        margin={"l": 10, "r": 10, "t": 10, "b": 10},
        hovermode="x unified",
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "right", "x": 1},
        xaxis_rangeslider_visible=False,
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


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
    tooltip = signal_description(signal)

    metric_col, signal_col = st.columns([0.35, 0.65], vertical_alignment="top")
    with metric_col:
        st.metric(
            label=f"{stock['name']} ({stock['symbol']})",
            value=f"{currency} {price:,.2f}",
            delta=f"{change:+.2f} ({change_pct:+.2f}%)",
        )
        if stock["market_state"]:
            st.caption(f"{stock['exchange']} - {stock['market_state']}")

    with signal_col:
        st.markdown(
            f'**Signal:** <span class="signal-tooltip" title="{tooltip}">{signal}</span>',
            unsafe_allow_html=True,
        )
        st.write(signal_reason)
        st.caption("Educational signal only, not personalized financial advice.")

    render_candlestick_chart(prices)


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
