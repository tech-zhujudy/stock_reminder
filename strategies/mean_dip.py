"""
mean_dip.py – "3-Month Average Dip" strategy.

Triggers a buy signal when today's price is at least X% below the
average closing price over the past N days.
"""

from __future__ import annotations

import logging

import pandas as pd

from strategies import BaseStrategy, Signal

logger = logging.getLogger(__name__)


class MeanDipStrategy(BaseStrategy):
    """
    Buy signal: current price is ≥ threshold_pct% below the
    average closing price over lookback_days.
    """

    name = "mean_dip"

    def __init__(self, params: dict):
        super().__init__(params)
        self.lookback_days: int = params.get("lookback_days", 90)
        self.threshold_pct: float = params.get("threshold_pct", 10.0)

    def evaluate(self, ticker: str, history_df: pd.DataFrame) -> Signal | None:
        if history_df.empty or len(history_df) < 5:
            logger.warning(
                "[%s] Not enough data to evaluate mean_dip (%d rows).",
                ticker,
                len(history_df),
            )
            return None

        # Calculate average of PREVIOUS days (exclude the current/last row)
        avg_price = history_df["Close"].iloc[:-1].mean()
        current_price = float(history_df["Close"].iloc[-1])

        if avg_price == 0:
            return None

        pct_below = (avg_price - current_price) / avg_price * 100

        logger.debug(
            "[%s] past_avg=%.2f  current=%.2f  pct_below=%.2f%%",
            ticker,
            avg_price,
            current_price,
            pct_below,
        )

        if pct_below >= self.threshold_pct:
            return Signal(
                ticker=ticker,
                strategy_name=self.name,
                current_price=round(current_price, 2),
                reference_value=round(avg_price, 2),
                pct_diff=round(pct_below, 2),
                message=(
                    f"🔔 {ticker}: ${current_price:.2f} is {pct_below:.1f}% "
                    f"below the {self.lookback_days}-day average of ${avg_price:.2f}. "
                    f"Possible buying opportunity!"
                ),
            )

        return None
