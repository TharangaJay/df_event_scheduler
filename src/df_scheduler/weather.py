from __future__ import annotations

from datetime import date, datetime
from typing import Any
from zoneinfo import ZoneInfo

import requests


def fetch_daily_max(settings: dict[str, Any], timeout: int = 30) -> tuple[dict[date, float], datetime]:
    location = settings["location"]
    weather = settings["weather"]
    params = {
        "latitude": location["latitude"],
        "longitude": location["longitude"],
        "daily": "temperature_2m_max",
        "temperature_unit": "fahrenheit",
        "timezone": location["timezone"],
        "forecast_days": weather.get("forecast_days", 16),
    }
    response = requests.get(weather["api_url"], params=params, timeout=timeout)
    response.raise_for_status()
    payload = response.json()
    dates = payload.get("daily", {}).get("time", [])
    temperatures = payload.get("daily", {}).get("temperature_2m_max", [])
    if not dates or len(dates) != len(temperatures):
        raise ValueError("Open-Meteo returned incomplete daily maximum-temperature data")
    values = {date.fromisoformat(d): float(t) for d, t in zip(dates, temperatures) if t is not None}
    retrieved_at = datetime.now(ZoneInfo(location["timezone"]))
    return values, retrieved_at


def classify_temperature(temp_f: float, thresholds: dict[str, float]) -> str:
    if temp_f > thresholds["high_min_exclusive"]:
        return "High"
    if temp_f >= thresholds["medium_min"]:
        return "Medium"
    if temp_f >= thresholds["low_min"]:
        return "Low"
    return "Ineligible"

