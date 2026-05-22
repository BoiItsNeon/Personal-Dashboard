"""Top-level Streamlit page assembly."""

import os

import streamlit as st

from dashboard.components import render_feed_panel, render_stock_panel
from dashboard.config import (
    APP_CAPTION,
    APP_TITLE,
    DEFAULT_INQUIRER_FEED,
    DEFAULT_STOCK_MARKET_FEED,
    DEFAULT_WATCH_SYMBOL,
)
from dashboard.styles import DASHBOARD_CSS


def render_sidebar() -> tuple[int, int, str, str, str]:
    """Render sidebar controls and return the user's current settings."""

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

    return inquirer_limit, market_limit, inquirer_feed_url, market_feed_url, watch_symbol


def render_dashboard() -> None:
    """Configure the page layout and assemble the dashboard panels."""

    st.set_page_config(
        page_title=APP_TITLE,
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    st.markdown(DASHBOARD_CSS, unsafe_allow_html=True)

    st.title(APP_TITLE)
    st.caption(APP_CAPTION)

    inquirer_limit, market_limit, inquirer_feed_url, market_feed_url, watch_symbol = render_sidebar()

    render_stock_panel(watch_symbol)
    st.divider()

    news_col, market_col = st.columns([1.1, 1])

    with news_col:
        render_feed_panel("News from the Inquirer", inquirer_feed_url, inquirer_limit)

    with market_col:
        render_feed_panel("US Stock Market News", market_feed_url, market_limit)
