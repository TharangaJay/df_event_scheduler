from datetime import date

from df_scheduler.assignments import choose_assignment


def row(day, category, strategy):
    event_date = date.fromisoformat(day)
    return {
        "event_date": day,
        "weekday": event_date.strftime("%A"),
        "weather_category": category,
        "strategy": strategy,
        "paired_with_date": "",
    }


def test_first_occurrence_is_random():
    result = choose_assignment(date(2026, 7, 29), "Medium", [], chooser=lambda _: "Intervention")
    assert result.strategy == "Intervention"
    assert result.method == "random"


def test_second_occurrence_is_opposite():
    history = [row("2026-07-22", "Medium", "Intervention")]
    result = choose_assignment(date(2026, 7, 29), "Medium", history)
    assert result.strategy == "Baseline"
    assert result.method == "opposite_previous"
    assert result.paired_with_date == "2026-07-22"


def test_weather_categories_have_independent_history():
    history = [row("2026-07-22", "High", "Intervention")]
    result = choose_assignment(
        date(2026, 7, 29), "Medium", history, chooser=lambda _: "Baseline"
    )
    assert result.strategy == "Baseline"
    assert result.method == "random"


def test_rerun_reuses_existing_assignment():
    history = [row("2026-07-29", "Medium", "Baseline")]
    result = choose_assignment(date(2026, 7, 29), "Medium", history)
    assert result.strategy == "Baseline"
    assert result.method == "existing"

