import csv
from datetime import date, datetime
from zoneinfo import ZoneInfo

from df_scheduler import main


def test_forecast_history_records_eligible_and_ineligible_days(tmp_path, monkeypatch):
    history_path = tmp_path / "forecast_history.csv"
    monkeypatch.setattr(main, "FORECAST_HISTORY", history_path)
    rows = [
        {
            "event_date": date(2026, 10, 19), "weekday": "Monday",
            "forecast_max_f": 82.34, "weather_category": "Low", "eligible": True,
            "exclusion_reason": "", "strategy": "Intervention", "assignment_method": "random",
        },
        {
            "event_date": date(2026, 10, 20), "weekday": "Tuesday",
            "forecast_max_f": 71.08, "weather_category": "Ineligible", "eligible": False,
            "exclusion_reason": "", "strategy": "", "assignment_method": "",
        },
    ]
    settings = {"location": {"name": "KSNA", "latitude": 33.6798, "longitude": -117.8674}}
    retrieved = datetime(2026, 10, 14, 8, tzinfo=ZoneInfo("America/Los_Angeles"))

    main.append_forecast_rows(rows, retrieved, settings)

    with history_path.open(newline="", encoding="utf-8") as handle:
        saved = list(csv.DictReader(handle))

    assert saved[0]["eligible"] == "true"
    assert saved[0]["strategy"] == "Intervention"
    assert saved[1]["eligible"] == "false"
    assert saved[1]["strategy"] == ""
