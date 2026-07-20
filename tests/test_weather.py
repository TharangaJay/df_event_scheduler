from df_scheduler.weather import classify_temperature


THRESHOLDS = {"low_min": 80.0, "medium_min": 85.0, "high_min_exclusive": 90.0}


def test_boundaries():
    assert classify_temperature(79.99, THRESHOLDS) == "Ineligible"
    assert classify_temperature(80.0, THRESHOLDS) == "Low"
    assert classify_temperature(84.99, THRESHOLDS) == "Low"
    assert classify_temperature(85.0, THRESHOLDS) == "Medium"
    assert classify_temperature(90.0, THRESHOLDS) == "Medium"
    assert classify_temperature(90.01, THRESHOLDS) == "High"

