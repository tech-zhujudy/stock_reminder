"""
test_strategies.py – Unit tests for the strategy engine.
"""

import pandas as pd
import pytest

from strategies import Signal
from strategies.mean_dip import MeanDipStrategy


def _make_history(prices: list[float]) -> pd.DataFrame:
    """Helper: create a DataFrame matching the expected schema."""
    dates = pd.date_range(end="2026-02-19", periods=len(prices), freq="B")
    return pd.DataFrame({"Date": dates, "Close": prices})


class TestMeanDipStrategy:
    """Tests for MeanDipStrategy."""

    def setup_method(self):
        self.strategy = MeanDipStrategy(
            {"lookback_days": 90, "threshold_pct": 10, "enabled": True}
        )

    def test_no_signal_when_price_is_above_average(self):
        # Current price ($110) is above the average ($105)
        prices = [100.0] * 44 + [110.0] * 44 + [110.0]
        history = _make_history(prices)
        signal = self.strategy.evaluate("AAPL", history)
        assert signal is None

    def test_no_signal_when_dip_below_threshold(self):
        # Average ≈ $100, current $95 → 5% below → NOT enough
        prices = [100.0] * 88 + [95.0]
        history = _make_history(prices)
        signal = self.strategy.evaluate("AAPL", history)
        assert signal is None

    def test_signal_when_dip_at_threshold(self):
        # Use many $100 values so the mean stays ≈ $100 even with one $90
        prices = [100.0] * 999 + [90.0]
        history = _make_history(prices)
        signal = self.strategy.evaluate("AAPL", history)
        assert signal is not None
        assert isinstance(signal, Signal)
        assert signal.ticker == "AAPL"
        assert signal.strategy_name == "mean_dip"
        assert signal.current_price == 90.0

    def test_signal_when_dip_exceeds_threshold(self):
        # Average ≈ $100, current $80 → 20% below → triggers
        prices = [100.0] * 88 + [80.0]
        history = _make_history(prices)
        signal = self.strategy.evaluate("AAPL", history)
        assert signal is not None
        assert signal.pct_diff >= 10.0

    def test_empty_dataframe_returns_none(self):
        empty = pd.DataFrame(columns=["Date", "Close"])
        signal = self.strategy.evaluate("AAPL", empty)
        assert signal is None

    def test_insufficient_data_returns_none(self):
        prices = [100.0, 90.0]  # only 2 rows
        history = _make_history(prices)
        signal = self.strategy.evaluate("AAPL", history)
        assert signal is None

    def test_custom_threshold(self):
        # With 5% threshold, a 6% dip should trigger
        strategy = MeanDipStrategy(
            {"lookback_days": 90, "threshold_pct": 5, "enabled": True}
        )
        prices = [100.0] * 88 + [94.0]
        history = _make_history(prices)
        signal = strategy.evaluate("TSLA", history)
        assert signal is not None
        assert signal.ticker == "TSLA"
