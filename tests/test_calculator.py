from pathlib import Path

import pytest

from white_keeper.calculator import calculate_exposure
from white_keeper.storage import load_records, save_record


def test_calculate_exposure_uses_specified_coefficients() -> None:
    result = calculate_exposure(
        start_time="10:00",
        end_time="13:20",
        season="summer",
        sunscreen=True,
        sunny=True,
    )

    assert result["total"] == pytest.approx(3.0)
    assert result["duration_hours"] == pytest.approx(3.3333333333)
    assert result["season_coefficient"] == 2.0
    assert result["sunscreen_coefficient"] == 0.3
    assert result["time_coefficient"] == pytest.approx(1.5)


def test_calculate_exposure_rejects_invalid_time_range() -> None:
    with pytest.raises(ValueError):
        calculate_exposure(
            start_time="14:00",
            end_time="13:00",
            season="spring",
            sunscreen=False,
            sunny=False,
        )


def test_save_and_load_records(tmp_path: Path) -> None:
    storage_path = tmp_path / "records.json"
    record = {
        "date": "2026-08-06",
        "start_time": "10:00",
        "end_time": "13:20",
        "season": "summer",
        "sunscreen": True,
        "sunny": True,
        "total": 3.0,
    }

    save_record(record, storage_path)
    loaded = load_records(storage_path)

    assert loaded[0]["date"] == "2026-08-06"
    assert loaded[0]["total"] == pytest.approx(3.0)
