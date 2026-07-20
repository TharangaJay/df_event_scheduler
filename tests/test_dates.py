from datetime import date

from df_scheduler.dates import following_workweek


def test_following_week_from_wednesday():
    assert following_workweek(date(2026, 7, 22)) == [
        date(2026, 7, 27), date(2026, 7, 28), date(2026, 7, 29),
        date(2026, 7, 30), date(2026, 7, 31),
    ]


def test_monday_uses_next_week_not_same_day():
    assert following_workweek(date(2026, 7, 20))[0] == date(2026, 7, 27)

