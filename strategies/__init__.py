"""
strategies – Extensible trading strategy engine.

To add a new strategy:
1. Create a new file in this package (e.g. strategies/my_strategy.py).
2. Subclass BaseStrategy and implement the evaluate() method.
3. Register it in STRATEGY_REGISTRY below.
4. Add a matching section in config.yaml under 'strategies'.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass

import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class Signal:
    """A trade signal emitted by a strategy."""

    ticker: str
    strategy_name: str
    current_price: float
    reference_value: float
    pct_diff: float
    message: str


class BaseStrategy(ABC):
    """Abstract base class for trading strategies."""

    name: str = "base"

    def __init__(self, params: dict):
        self.params = params

    @abstractmethod
    def evaluate(self, ticker: str, history_df: pd.DataFrame) -> Signal | None:
        """
        Evaluate the strategy for a given ticker.

        Args:
            ticker: The stock ticker symbol.
            history_df: DataFrame with columns ["Date", "Close"].

        Returns:
            A Signal if the strategy triggers, otherwise None.
        """
        ...


# ---- Registry ---------------------------------------------------------------

# Import concrete strategies (kept here to avoid circular imports)
from strategies.mean_dip import MeanDipStrategy  # noqa: E402

STRATEGY_REGISTRY: dict[str, type[BaseStrategy]] = {
    "mean_dip": MeanDipStrategy,
}


def get_enabled_strategies(config: dict) -> list[BaseStrategy]:
    """
    Instantiate all strategies that are enabled in the config.
    """
    strategies_config = config.get("strategies", {})
    enabled: list[BaseStrategy] = []

    for name, params in strategies_config.items():
        if not params.get("enabled", False):
            continue
        cls = STRATEGY_REGISTRY.get(name)
        if cls is None:
            logger.warning("Unknown strategy '%s' in config – skipping.", name)
            continue
        enabled.append(cls(params))
        logger.info("Loaded strategy: %s", name)

    return enabled
