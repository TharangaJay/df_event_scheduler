from __future__ import annotations

import csv
import secrets
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Callable


STRATEGIES = ("Baseline", "Intervention")


@dataclass(frozen=True)
class Assignment:
    strategy: str
    method: str
    paired_with_date: str = ""


def read_history(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def choose_assignment(
    event_date: date,
    category: str,
    history: list[dict[str, str]],
    chooser: Callable[[tuple[str, str]], str] = secrets.choice,
) -> Assignment:
    existing = next((row for row in history if row["event_date"] == event_date.isoformat()), None)
    if existing:
        return Assignment(existing["strategy"], "existing", existing.get("paired_with_date", ""))

    weekday = event_date.strftime("%A")
    matching = [
        row for row in history
        if row["weekday"] == weekday and row["weather_category"] == category
    ]
    matching.sort(key=lambda row: row["event_date"])
    if len(matching) % 2 == 0:
        return Assignment(chooser(STRATEGIES), "random")

    previous = matching[-1]
    opposite = "Intervention" if previous["strategy"] == "Baseline" else "Baseline"
    return Assignment(opposite, "opposite_previous", previous["event_date"])


def append_assignment(
    path: Path,
    event_date: date,
    category: str,
    assignment: Assignment,
    assigned_at: datetime,
    forecast_max_f: float,
) -> None:
    history = read_history(path)
    if any(row["event_date"] == event_date.isoformat() for row in history):
        return
    fieldnames = [
        "event_date", "weekday", "weather_category", "strategy", "assignment_method",
        "paired_with_date", "assigned_at", "forecast_max_f",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    write_header = not path.exists() or path.stat().st_size == 0
    with path.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()
        writer.writerow({
            "event_date": event_date.isoformat(),
            "weekday": event_date.strftime("%A"),
            "weather_category": category,
            "strategy": assignment.strategy,
            "assignment_method": assignment.method,
            "paired_with_date": assignment.paired_with_date,
            "assigned_at": assigned_at.isoformat(),
            "forecast_max_f": f"{forecast_max_f:.2f}",
        })

