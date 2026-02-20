"""
data_fetcher.py – Fetch stock price history from Yahoo Finance via yfinance.
"""

import logging
from datetime import datetime, timedelta

import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)


def fetch_history(ticker: str, days: int = 90) -> pd.DataFrame:
    """
    Download historical daily closing prices for a single ticker.

    Args:
        ticker: Yahoo Finance ticker symbol (e.g. "AAPL", "BRK-B").
        days: Number of calendar days of history to retrieve.

    Returns:
        DataFrame with columns ["Date", "Close"], sorted ascending by date.
        Returns an empty DataFrame if the download fails.
    """
    end = datetime.today()
    start = end - timedelta(days=days)

    try:
        data = yf.download(
            ticker,
            start=start.strftime("%Y-%m-%d"),
            end=end.strftime("%Y-%m-%d"),
            progress=False,
            auto_adjust=True,
        )
        if data.empty:
            logger.warning("No data returned for %s", ticker)
            return pd.DataFrame(columns=["Date", "Close"])

        # Handle multi-level columns from yfinance
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)

        df = data[["Close"]].copy()
        df = df.reset_index()
        df.columns = ["Date", "Close"]
        df["Close"] = pd.to_numeric(df["Close"], errors="coerce")
        df = df.dropna(subset=["Close"])
        df = df.sort_values("Date").reset_index(drop=True)
        return df

    except Exception as e:
        logger.error("Failed to fetch data for %s: %s", ticker, e)
        return pd.DataFrame(columns=["Date", "Close"])


def fetch_current_price(ticker: str) -> float | None:
    """
    Get the most recent closing price for a ticker.

    Returns:
        The latest closing price, or None on failure.
    """
    df = fetch_history(ticker, days=5)
    if df.empty:
        return None
    return float(df["Close"].iloc[-1])


def fetch_all_tickers(config: dict) -> list[str]:
    """
    Flatten all ticker groups from the config into a single list.
    """
    tickers: list[str] = []
    for group_name, symbols in config.get("tickers", {}).items():
        if isinstance(symbols, list):
            tickers.extend(symbols)
    return tickers
