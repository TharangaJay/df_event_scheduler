from datetime import date

from df_scheduler.config import ROOT
from df_scheduler.holiday_calendar import load_exclusions


def test_federal_and_uci_specific_closures_are_excluded():
    exclusions = load_exclusions({2026}, ROOT / "config" / "uci_holidays.yaml")
    assert date(2026, 7, 3) in exclusions
    assert date(2026, 3, 27) in exclusions
    assert date(2026, 12, 30) in exclusions

