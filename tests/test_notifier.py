"""
test_notifier.py – Unit tests for the email notifier.
"""

from unittest.mock import MagicMock, patch

from notifier import _build_html, send_email
from strategies import Signal


def _sample_signals() -> list[Signal]:
    return [
        Signal(
            ticker="AAPL",
            strategy_name="mean_dip",
            current_price=150.00,
            reference_value=170.00,
            pct_diff=11.76,
            message="🔔 AAPL: $150.00 is 11.8% below the 90-day average of $170.00.",
        ),
        Signal(
            ticker="TSLA",
            strategy_name="mean_dip",
            current_price=200.00,
            reference_value=230.00,
            pct_diff=13.04,
            message="🔔 TSLA: $200.00 is 13.0% below the 90-day average of $230.00.",
        ),
    ]


class TestBuildHtml:
    def test_contains_ticker_names(self):
        html = _build_html(_sample_signals())
        assert "AAPL" in html
        assert "TSLA" in html

    def test_contains_prices(self):
        html = _build_html(_sample_signals())
        assert "$150.00" in html
        assert "$170.00" in html

    def test_contains_table_structure(self):
        html = _build_html(_sample_signals())
        assert "<table" in html
        assert "<th" in html
        assert "<td" in html


class TestSendEmail:
    def test_no_signals_skips_email(self):
        config = {"email": {"sender_email": "a@b.com", "sender_password": "x"}}
        result = send_email(config, [])
        assert result is False

    def test_missing_credentials_returns_false(self):
        config = {"email": {"sender_email": "", "sender_password": ""}}
        result = send_email(config, _sample_signals())
        assert result is False

    @patch("notifier.smtplib.SMTP")
    def test_successful_send(self, mock_smtp_class):
        mock_server = MagicMock()
        mock_smtp_class.return_value.__enter__ = MagicMock(return_value=mock_server)
        mock_smtp_class.return_value.__exit__ = MagicMock(return_value=False)

        config = {
            "email": {
                "smtp_server": "smtp.test.com",
                "smtp_port": 587,
                "sender_email": "test@test.com",
                "sender_password": "secret",
                "recipients": ["tech@zhujudy.com"],
            }
        }

        result = send_email(config, _sample_signals())
        assert result is True
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with("test@test.com", "secret")
