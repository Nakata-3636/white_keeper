from __future__ import annotations

from datetime import datetime


SEASON_COEFFICIENTS = {
    "winter": 0.5,
    "spring": 1.0,
    "summer": 2.0,
    "autumn": 1.0,
}

SUNSCREEN_COEFFICIENTS = {True: 0.3, False: 1.0}
TIME_COEFFICIENTS = [
    ((0, 4), 0.0),
    ((5, 9), 1.0),
    ((10, 15), 1.5),
    ((16, 18), 0.5),
    ((19, 24), 0.0),
]


def _parse_time(time_text: str) -> int:
    try:
        parsed = datetime.strptime(time_text, "%H:%M")
    except ValueError as exc:
        raise ValueError("時刻は HH:MM 形式で入力してください。") from exc

    return parsed.hour * 60 + parsed.minute


def _get_time_coefficient(hour: int) -> float:
    for (start_hour, end_hour), coefficient in TIME_COEFFICIENTS:
        if start_hour <= hour <= end_hour:
            return coefficient
    raise ValueError("時刻係数の範囲に該当しません。")


def calculate_exposure(
    *,
    start_time: str,
    end_time: str,
    season: str,
    sunscreen: bool,
    sunny: bool,
) -> dict[str, float | int | bool | str]:
    start_minutes = _parse_time(start_time)
    end_minutes = _parse_time(end_time)

    if start_minutes >= end_minutes:
        raise ValueError("開始時刻は終了時刻より前である必要があります。")

    season_key = season.lower()
    if season_key not in SEASON_COEFFICIENTS:
        raise ValueError("季節の指定が不正です。")

    duration_minutes = end_minutes - start_minutes
    duration_hours = duration_minutes / 60.0

    season_coefficient = SEASON_COEFFICIENTS[season_key]
    sunscreen_coefficient = SUNSCREEN_COEFFICIENTS[sunscreen]

    current_minute = start_minutes
    weighted_time_coefficient = 0.0
    while current_minute < end_minutes:
        hour = (current_minute // 60) % 24
        next_minute = min(end_minutes, ((current_minute // 60) + 1) * 60)
        segment_minutes = next_minute - current_minute
        weighted_time_coefficient += _get_time_coefficient(hour) * (segment_minutes / 60.0)
        current_minute = next_minute

    time_coefficient = weighted_time_coefficient / duration_hours
    total = duration_hours * season_coefficient * sunscreen_coefficient * time_coefficient

    return {
        "total": total,
        "duration_hours": duration_hours,
        "season_coefficient": season_coefficient,
        "sunscreen_coefficient": sunscreen_coefficient,
        "time_coefficient": time_coefficient,
        "sunny": sunny,
    }
