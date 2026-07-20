from __future__ import annotations

from datetime import date, timedelta


def following_workweek(today: date) -> list[date]:
    """Return Monday-Friday of the week following/after the current date."""
    days_until_next_monday = (7 - today.weekday()) % 7
    if days_until_next_monday == 0:
        days_until_next_monday = 7
    monday = today + timedelta(days=days_until_next_monday)
    return [monday + timedelta(days=i) for i in range(5)]

