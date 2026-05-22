"""Default settings for feeds, stock symbols, and dashboard metadata."""

APP_TITLE = "News and Market Dashboard"
APP_CAPTION = "Latest Inquirer headlines plus US stock-market news."

DEFAULT_INQUIRER_FEED = "https://newsinfo.inquirer.net/feed"
DEFAULT_STOCK_MARKET_FEED = (
    "https://feeds.finance.yahoo.com/rss/2.0/headline?"
    "s=%5EGSPC,%5EDJI,%5EIXIC&region=US&lang=en-US"
)
DEFAULT_WATCH_SYMBOL = "DDD"
DEFAULT_STOCK_RANGE = "1d"
DEFAULT_STOCK_INTERVAL = "1m"
DEFAULT_AUTO_REFRESH_SECONDS = 60
