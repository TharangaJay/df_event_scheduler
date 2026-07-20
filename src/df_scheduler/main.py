from __future__ import annotations

import argparse
import csv
import sys
import uuid
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from .assignments import append_assignment, choose_assignment, read_history
from .config import ROOT, load_settings
from .dates import following_workweek
from .email_report import render_schedule_email, render_test_email, send_email
from .holiday_calendar import load_exclusions
from .weather import classify_temperature, fetch_daily_max


ASSIGNMENT_HISTORY = ROOT / "data" / "assignment_history.csv"
FORECAST_HISTORY = ROOT / "data" / "forecast_history.csv"
UCI_HOLIDAYS = ROOT / "config" / "uci_holidays.yaml"


def append_forecast_rows(rows: list[dict], retrieved_at: datetime, settings: dict) -> None:
    fieldnames = [
        "run_id", "retrieved_at", "event_date", "weekday", "forecast_max_f",
        "weather_category", "eligible", "excluded", "exclusion_reason", "strategy",
        "assignment_method", "weather_source", "location_name", "latitude", "longitude",
    ]
    run_id = str(uuid.uuid4())
    with FORECAST_HISTORY.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        for row in rows:
            writer.writerow({
                "run_id": run_id,
                "retrieved_at": retrieved_at.isoformat(),
                "event_date": row["event_date"].isoformat(),
                "weekday": row["weekday"],
                "forecast_max_f": "" if row["forecast_max_f"] is None else f'{row["forecast_max_f"]:.2f}',
                "weather_category": row["weather_category"],
                "eligible": str(row["eligible"]).lower(),
                "excluded": str(bool(row["exclusion_reason"])).lower(),
                "exclusion_reason": row["exclusion_reason"],
                "strategy": row["strategy"],
                "assignment_method": row["assignment_method"],
                "weather_source": "Open-Meteo",
                "location_name": settings["location"]["name"],
                "latitude": settings["location"]["latitude"],
                "longitude": settings["location"]["longitude"],
            })


def build_schedule(today: date, persist: bool = True) -> tuple[list[dict], datetime, dict]:
    settings = load_settings()
    forecast, retrieved_at = fetch_daily_max(settings)
    target_dates = following_workweek(today)
    exclusions = load_exclusions({day.year for day in target_dates}, UCI_HOLIDAYS)
    history = read_history(ASSIGNMENT_HISTORY)
    rows = []
    for day in target_dates:
        if day not in forecast:
            raise ValueError(f"Open-Meteo response did not cover {day.isoformat()}")
        temp = forecast[day]
        category = classify_temperature(temp, settings["thresholds_f"])
        exclusion_reason = exclusions.get(day, "")
        eligible = category != "Ineligible" and not exclusion_reason
        strategy = ""
        method = ""
        if eligible:
            assignment = choose_assignment(day, category, history)
            strategy, method = assignment.strategy, assignment.method
            if persist:
                append_assignment(ASSIGNMENT_HISTORY, day, category, assignment, retrieved_at, temp)
                history = read_history(ASSIGNMENT_HISTORY)
        rows.append({
            "event_date": day,
            "weekday": day.strftime("%A"),
            "forecast_max_f": temp,
            "weather_category": category,
            "eligible": eligible,
            "exclusion_reason": exclusion_reason,
            "strategy": strategy,
            "assignment_method": method,
        })
    if persist:
        append_forecast_rows(rows, retrieved_at, settings)
    return rows, retrieved_at, settings


def print_schedule(rows: list[dict]) -> None:
    print("Date       Day        Max OAT  Category    Strategy      Status")
    for row in rows:
        status = row["exclusion_reason"] or ("Scheduled" if row["eligible"] else "Not eligible")
        print(
            f'{row["event_date"]} {row["weekday"]:<10} {row["forecast_max_f"]:>6.1f}°F '
            f'{row["weather_category"]:<11} {row["strategy"] or "—":<13} {status}'
        )


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Create and email the weekly UCI DF event schedule")
    parser.add_argument("--today", type=date.fromisoformat, help="Override today's date (YYYY-MM-DD)")
    parser.add_argument("--dry-run", action="store_true", help="Do not save history or send email")
    parser.add_argument("--no-email", action="store_true", help="Save history but do not send email")
    parser.add_argument("--test-email", action="store_true", help="Send only a connectivity test email")
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    settings = load_settings()
    tz = ZoneInfo(settings["location"]["timezone"])
    now = datetime.now(tz)
    if args.test_email:
        send_email("UCI DF Scheduler – Test Email", render_test_email(now))
        print("Test email accepted by SendGrid.")
        return 0
    today = args.today or now.date()
    rows, retrieved_at, settings = build_schedule(today, persist=not args.dry_run)
    print_schedule(rows)
    if not args.dry_run and not args.no_email:
        period = f'{rows[0]["event_date"]:%b %d}–{rows[-1]["event_date"]:%b %d, %Y}'
        subject = f'{settings["email"]["subject_prefix"]}: {period}'
        send_email(subject, render_schedule_email(rows, retrieved_at, settings["location"]["name"]))
        print("Schedule email accepted by SendGrid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

