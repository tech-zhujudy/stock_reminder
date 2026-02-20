"""
notifier.py – Email notification sender.

Sends an HTML-formatted email summarising all triggered trade signals.
"""

from __future__ import annotations

import logging
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from strategies import Signal

logger = logging.getLogger(__name__)


def _build_html(signals: list[Signal]) -> str:
    """Build a styled HTML email body from a list of signals."""
    rows = ""
    for s in signals:
        rows += f"""
        <tr>
            <td style="padding:8px 12px;border-bottom:1px solid #eee;font-weight:600;">{s.ticker}</td>
            <td style="padding:8px 12px;border-bottom:1px solid #eee;">{s.strategy_name}</td>
            <td style="padding:8px 12px;border-bottom:1px solid #eee;">${s.current_price:.2f}</td>
            <td style="padding:8px 12px;border-bottom:1px solid #eee;">${s.reference_value:.2f}</td>
            <td style="padding:8px 12px;border-bottom:1px solid #eee;color:#d9534f;font-weight:600;">
                {s.pct_diff:.1f}% below avg
            </td>
        </tr>"""

    html = f"""\
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family:'Segoe UI',Arial,sans-serif;color:#333;max-width:700px;margin:auto;">
  <h2 style="color:#2c3e50;">📈 Stock Reminder – Trade Signals</h2>
  <p style="color:#666;font-size:14px;">{datetime.now().strftime("%A, %B %d, %Y %I:%M %p")}</p>

  <table style="width:100%;border-collapse:collapse;margin:16px 0;">
    <thead>
      <tr style="background:#f8f9fa;">
        <th style="padding:10px 12px;text-align:left;border-bottom:2px solid #dee2e6;">Ticker</th>
        <th style="padding:10px 12px;text-align:left;border-bottom:2px solid #dee2e6;">Strategy</th>
        <th style="padding:10px 12px;text-align:left;border-bottom:2px solid #dee2e6;">Current</th>
        <th style="padding:10px 12px;text-align:left;border-bottom:2px solid #dee2e6;">Avg</th>
        <th style="padding:10px 12px;text-align:left;border-bottom:2px solid #dee2e6;">Signal</th>
      </tr>
    </thead>
    <tbody>
      {rows}
    </tbody>
  </table>

  <h3 style="color:#2c3e50;">Signal Details</h3>
  <ul style="line-height:1.8;">
    {"".join(f"<li>{s.message}</li>" for s in signals)}
  </ul>

  <hr style="border:none;border-top:1px solid #eee;margin:24px 0;">
  <p style="font-size:12px;color:#999;">
    This is an automated alert from <strong>Stock Reminder</strong>.
    Not financial advice – always do your own research.
  </p>
</body>
</html>"""
    return html


def send_email(config: dict, signals: list[Signal]) -> bool:
    """
    Send an HTML email with all triggered signals.

    Args:
        config: The full application config dict (reads 'email' section).
        signals: List of Signal objects to include in the email.

    Returns:
        True if the email was sent successfully, False otherwise.
    """
    if not signals:
        logger.info("No signals to send – skipping email.")
        return False

    email_cfg = config.get("email", {})
    smtp_server = email_cfg.get("smtp_server", "smtp.gmail.com")
    smtp_port = email_cfg.get("smtp_port", 587)
    sender = email_cfg.get("sender_email", "")
    password = email_cfg.get("sender_password", "")
    recipients = email_cfg.get("recipients", [])

    if not sender or not password:
        logger.error("Email sender credentials are not configured.")
        return False
    if not recipients:
        logger.error("No email recipients configured.")
        return False

    # Build message
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"📈 Stock Reminder – {len(signals)} Signal(s) Triggered"
    msg["From"] = sender
    msg["To"] = ", ".join(recipients)

    # Plain-text fallback
    plain = "Stock Reminder – Trade Signals\n\n"
    for s in signals:
        plain += f"  • {s.message}\n"

    msg.attach(MIMEText(plain, "plain"))
    msg.attach(MIMEText(_build_html(signals), "html"))

    try:
        with smtplib.SMTP(smtp_server, smtp_port, timeout=30) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(sender, password)
            server.sendmail(sender, recipients, msg.as_string())
        logger.info("Email sent to %s", ", ".join(recipients))
        return True
    except Exception as e:
        logger.error("Failed to send email: %s", e)
        return False
