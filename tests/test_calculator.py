from pathlib import Path

import pytest

from white_keeper.calculator import calculate_exposure, calculate_exposure_periods, get_score_band
from white_keeper.storage import load_records, save_record


def test_calculate_exposure_uses_specified_coefficients() -> None:
    result = calculate_exposure(
        start_time="10:00",
        end_time="13:20",
        date_value="2026-07-15",
        weather="sunny",
        sunscreen="no_reapply",
    )

    assert result["total"] == pytest.approx(5.0)
    assert result["duration_hours"] == pytest.approx(3.3333333333)
    assert result["season_coefficient"] == 2.5
    assert result["sunscreen_coefficient"] == 0.3
    assert result["time_coefficient"] == pytest.approx(2.0)


def test_calculate_exposure_rejects_invalid_time_range() -> None:
    with pytest.raises(ValueError):
        calculate_exposure(
            start_time="14:00",
            end_time="13:00",
            date_value="2026-03-01",
            weather="cloudy",
            sunscreen="none",
        )


def test_calculate_exposure_uses_specified_weather_coefficients() -> None:
    result = calculate_exposure(
        start_time="14:00",
        end_time="15:00",
        date_value="2026-04-01",
        weather="cloudy",
        sunscreen="none",
    )

    assert result["weather_coefficient"] == 0.8
    assert result["total"] == pytest.approx(1.2)


def test_calculate_exposure_periods_matches_spec_example() -> None:
    result = calculate_exposure_periods(
        periods=[("11:00", "14:00"), ("14:00", "14:30")],
        date_value="2026-08-05",
        weather="sunny",
        sunscreen="no_reapply",
    )

    assert result["total"] == pytest.approx(3.9)
    assert result["score_label"] == "中"


def test_get_score_band_returns_high_band() -> None:
    band = get_score_band(9.0)

    assert band["label"] == "極めて高"


def test_save_and_load_records(tmp_path: Path) -> None:
    storage_path = tmp_path / "records.json"
    record = {
        "record_id": "abc123",
        "date": "2026-08-06",
        "start_time": "10:00",
        "end_time": "13:20",
        "periods": [{"start_time": "10:00", "end_time": "13:20"}],
        "weather": "晴れ",
        "sunscreen": "あり（塗り直しなし）",
        "total": 3.0,
    }

    save_record(record, storage_path)
    loaded = load_records(storage_path)

    assert loaded[0]["date"] == "2026-08-06"
    assert loaded[0]["total"] == pytest.approx(3.0)
