from __future__ import annotations

import html
import os
from datetime import date, datetime
from typing import Any

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail


def render_schedule_email(
    rows: list[dict[str, Any]],
    retrieved_at: datetime,
    location_name: str,
) -> str:
    body_rows = []
    for row in rows:
        temp = "—" if row["forecast_max_f"] is None else f'{row["forecast_max_f"]:.1f}°F'
        status = row["exclusion_reason"] or ("Eligible" if row["eligible"] else "Not eligible")
        body_rows.append(
            "<tr>"
            f'<td>{html.escape(row["event_date"].strftime("%b %d, %Y"))}</td>'
            f'<td>{html.escape(row["weekday"])}</td>'
            f"<td>{temp}</td>"
            f'<td>{html.escape(row["weather_category"] or "—")}</td>'
            f'<td>{html.escape(row["strategy"] or "—")}</td>'
            f'<td>{html.escape(status)}</td>'
            "</tr>"
        )
    return f"""
    <html><body>
    <h2>UCI Demand Flexibility Schedule</h2>
    <p><strong>Forecast retrieved:</strong> {html.escape(retrieved_at.strftime('%B %d, %Y at %I:%M %p %Z'))}<br>
    <strong>Source:</strong> Open-Meteo<br>
    <strong>Location:</strong> {html.escape(location_name)}</p>
    <table style="border-collapse:collapse" border="1" cellpadding="7">
      <thead><tr><th>Date</th><th>Day</th><th>Max OAT</th><th>Category</th><th>Strategy</th><th>Status</th></tr></thead>
      <tbody>{''.join(body_rows)}</tbody>
    </table>
    <p>Thresholds: Low 80–&lt;85°F; Medium 85–90°F; High &gt;90°F.</p>
    </body></html>
    """


def send_email(subject: str, html_body: str) -> None:
    required = ["SENDGRID_API_KEY", "SENDGRID_FROM_EMAIL", "DF_NOTIFICATION_EMAILS"]
    missing = [name for name in required if not os.environ.get(name)]
    if missing:
        raise RuntimeError(f"Missing required email environment variables: {', '.join(missing)}")
    recipients = [value.strip() for value in os.environ["DF_NOTIFICATION_EMAILS"].split(",") if value.strip()]
    message = Mail(
        from_email=os.environ["SENDGRID_FROM_EMAIL"],
        to_emails=recipients,
        subject=subject,
        html_content=html_body,
    )
    response = SendGridAPIClient(os.environ["SENDGRID_API_KEY"]).send(message)
    if response.status_code < 200 or response.status_code >= 300:
        raise RuntimeError(f"SendGrid returned HTTP {response.status_code}")


def render_test_email(now: datetime) -> str:
    return (
        "<html><body><h2>UCI DF Scheduler Test</h2>"
        f"<p>The scheduler successfully sent this test at {html.escape(now.strftime('%B %d, %Y at %I:%M %p %Z'))}.</p>"
        "<p>No forecast was retrieved and no strategy assignment history was changed.</p>"
        "</body></html>"
    )

