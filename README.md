# News and Market Dashboard

A small Python dashboard built with Streamlit. It shows:

- News from the Inquirer via RSS
- A stock watch panel for `DDD`
- US stock-market news via RSS

## Setup

1. Create and activate a virtual environment.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies.

```powershell
pip install -r requirements.txt
```

3. Create your local environment file.

```powershell
Copy-Item .env.example .env
```

4. Edit `.env` if you want to use different RSS feeds.

## Run

```powershell
streamlit run app.py
```

The dashboard will open in your browser. Use the sidebar to change how many news items are shown.

## Project Structure

```text
app.py                  # Streamlit entry point
dashboard/config.py     # Default feed URLs and ticker settings
dashboard/news.py       # RSS loading and normalization
dashboard/stocks.py     # Yahoo Finance chart data and signal logic
dashboard/components.py # Reusable Streamlit panels
dashboard/ui.py         # Page layout and sidebar controls
dashboard/styles.py     # Dashboard CSS
```

## React Note

The app is still Python-first with Streamlit, which already renders its interface through a React frontend internally. A separate custom React UI can be added later by keeping `dashboard/news.py` and `dashboard/stocks.py` as the data layer and exposing them through a Python API.

## Start Automatically on Windows Sign-In

Run this once:

```powershell
.\install_startup.ps1
```

This creates a shortcut in your Windows Startup folder. On your next sign-in, it will run `start_dashboard.ps1` and start the dashboard at `http://localhost:8501`.

## Notes

- The default Inquirer feed is `https://newsinfo.inquirer.net/feed`. If you prefer another Inquirer section, change `INQUIRER_FEED_URL` in `.env` or the sidebar.
- The default US stock-market feed follows Yahoo Finance headlines for the S&P 500, Dow Jones Industrial Average, and Nasdaq Composite. Change `STOCK_MARKET_FEED_URL` in `.env` or the sidebar if you prefer another feed.
- The stock panel defaults to `DDD`. Change `WATCH_SYMBOL` in `.env` or the sidebar if you want to monitor a different ticker.
- The stock panel defaults to intraday `1m` candles and auto-refreshes every 60 seconds. Yahoo Finance data may still be delayed depending on the exchange and symbol.
