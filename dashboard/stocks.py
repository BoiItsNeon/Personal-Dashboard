"""Yahoo Finance data loading and stock signal helpers."""

import pandas as pd
import requests
import streamlit as st


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
