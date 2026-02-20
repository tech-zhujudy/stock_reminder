# 📈 Stock Reminder

A Python application that tracks stock prices, evaluates trading strategies, and sends email notifications when trade signals are triggered.

## Tracked Stocks

| Group | Tickers |
|---|---|
| **Energy** | BRK.B, OXY, XLE, VDE |
| **Magnificent Seven** | NVDA, AAPL, MSFT, GOOGL, META, AMZN, TSLA |
| **S&P 500** | SPY |

## Strategies

### Mean Dip (default)
Sends a **buy signal** when a stock's current price drops **≥ 10%** below its 3-month average closing price.

> You can add your own strategies by subclassing `BaseStrategy` in the `strategies/` directory.

---

## Quick Start

### 1. Prerequisites

- Python 3.9 or later
- A Gmail account (or any SMTP provider) for sending notifications

### 2. Install dependencies

```bash
cd stock_reminder
pip install -r requirements.txt
```

### 3. Configure

Edit **`config.yaml`**:

```yaml
email:
  smtp_server: smtp.gmail.com
  smtp_port: 587
  sender_email: "your-email@gmail.com"
  sender_password: "your-app-password"
  recipients:
    - "tech@zhujudy.com"
```

> **Gmail users:** Use an [App Password](https://support.google.com/accounts/answer/185833) instead of your account password.  
> Go to *Google Account → Security → 2-Step Verification → App Passwords* and generate one.

### 4. Run

```bash
# Run once (ideal for cron jobs)
python main.py

# Run on a daily schedule (stays alive)
python main.py --schedule
```

### 5. (Optional) Set up a cron job

To run every weekday at 9:30 AM:

```bash
crontab -e
# Add this line:
30 9 * * 1-5 cd /path/to/stock_reminder && python main.py >> /tmp/stock_reminder.log 2>&1
```

---

## Adding a Custom Strategy

1. Create a new file in `strategies/`, e.g. `strategies/rsi.py`:

```python
from strategies import BaseStrategy, Signal
import pandas as pd

class RSIStrategy(BaseStrategy):
    name = "rsi"

    def evaluate(self, ticker: str, history_df: pd.DataFrame) -> Signal | None:
        # Your logic here
        ...
```

2. Register it in `strategies/__init__.py`:

```python
from strategies.rsi import RSIStrategy

STRATEGY_REGISTRY["rsi"] = RSIStrategy
```

3. Enable it in `config.yaml`:

```yaml
strategies:
  rsi:
    enabled: true
    # your custom params here
```

---

## Project Structure

```
stock_reminder/
├── config.yaml            # Tickers, strategies, email settings
├── main.py                # Entry point / orchestrator
├── data_fetcher.py        # Fetch prices via Yahoo Finance
├── strategies/
│   ├── __init__.py        # Strategy base class & registry
│   └── mean_dip.py        # 3-month average dip strategy
├── notifier.py            # Email sender
├── requirements.txt       # Python dependencies
├── tests/
│   ├── test_strategies.py # Strategy unit tests
│   └── test_notifier.py   # Notifier unit tests
└── README.md
```

---

## Running Tests

```bash
python -m pytest tests/ -v
```

---

## Disclaimer

This tool is for informational purposes only. It is **not financial advice**. Always do your own research before making investment decisions.
