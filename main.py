#!/usr/bin/env python3
"""
main.py – Stock Reminder orchestrator.

Usage:
    python main.py              # Run once (suitable for cron)
    python main.py --schedule   # Run continuously on a daily schedule
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import yaml

from data_fetcher import fetch_all_tickers, fetch_history
from notifier import send_email
from strategies import get_enabled_strategies

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

CONFIG_PATH = Path(__file__).parent / "config.yaml"


def load_config(path: Path = CONFIG_PATH) -> dict:
    """Load and return the YAML configuration."""
    with open(path, "r") as f:
        return yaml.safe_load(f)


def run_once(config: dict) -> None:
    """Execute a single scan across all tickers and strategies."""
    tickers = fetch_all_tickers(config)
    strategies = get_enabled_strategies(config)

    if not strategies:
        logger.warning("No strategies enabled – nothing to do.")
        return

    logger.info(
        "Scanning %d tickers with %d strategy(ies)…",
        len(tickers),
        len(strategies),
    )

    all_signals = []

    for ticker in tickers:
        # Use the longest lookback any strategy needs
        max_lookback = max(s.params.get("lookback_days", 90) for s in strategies)
        history = fetch_history(ticker, days=max_lookback)

        if history.empty:
            logger.warning("Skipping %s – no data available.", ticker)
            continue

        for strategy in strategies:
            signal = strategy.evaluate(ticker, history)
            if signal:
                logger.info("⚡ SIGNAL  %s", signal.message)
                all_signals.append(signal)
            else:
                logger.info("   OK      %s – no signal from %s", ticker, strategy.name)

    # ----- Summary -----
    logger.info("─" * 60)
    if all_signals:
        logger.info("🔔 %d signal(s) triggered.", len(all_signals))
        email_sent = send_email(config, all_signals)
        if email_sent:
            logger.info("✅ Email notification sent.")
        else:
            logger.warning("⚠️  Email was NOT sent (check config / logs).")
    else:
        logger.info("✅ No signals triggered – all tickers within range.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Stock Reminder")
    parser.add_argument(
        "--schedule",
        action="store_true",
        help="Keep running and execute daily at the configured time.",
    )
    parser.add_argument(
        "--config",
        type=str,
        default=str(CONFIG_PATH),
        help="Path to config.yaml (default: ./config.yaml).",
    )
    args = parser.parse_args()

    config = load_config(Path(args.config))

    if args.schedule:
        import schedule as sched
        import time

        run_time = config.get("schedule", {}).get("run_time", "09:30")
        logger.info("Scheduling daily run at %s …", run_time)
        sched.every().day.at(run_time).do(run_once, config)

        # Also run immediately on start
        run_once(config)

        while True:
            sched.run_pending()
            time.sleep(30)
    else:
        run_once(config)


if __name__ == "__main__":
    main()
