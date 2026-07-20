from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import holidays
import yaml


def _date_range(start: date, end: date):
    current = start
    while current <= end:
        yield current
        current += timedelta(days=1)


def load_exclusions(years: set[int], uci_file: Path) -> dict[date, str]:
    excluded: dict[date, str] = {}
    federal = holidays.US(years=sorted(years), observed=True)
    excluded.update({day: f"US federal holiday: {name}" for day, name in federal.items()})

    with uci_file.open("r", encoding="utf-8") as handle:
        configured = (yaml.safe_load(handle) or {}).get("years", {})
    configured_years = {int(year) for year in configured}
    missing = years - configured_years
    if missing:
        missing_text = ", ".join(str(year) for year in sorted(missing))
        raise ValueError(
            f"UCI closure dates have not been configured for: {missing_text}. "
            "Update config/uci_holidays.yaml from the official UCI Staff Calendar."
        )

    for year in years:
        entries = configured.get(year, configured.get(str(year), []))
        for entry in entries:
            if "date" in entry:
                excluded[date.fromisoformat(entry["date"])] = entry["name"]
            else:
                start = date.fromisoformat(entry["start"])
                end = date.fromisoformat(entry["end"])
                for day in _date_range(start, end):
                    excluded[day] = entry["name"]
    return excluded

