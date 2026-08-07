from __future__ import annotations

from datetime import date, datetime
from typing import Iterable, Sequence


# 季節係数は月ごとに定義する（仕様書に基づく）
SEASON_COEFFICIENTS_BY_MONTH = {
    1: 0.4,
    2: 0.6,
    3: 1.0,
    4: 1.5,
    5: 2.0,
    6: 2.5,
    7: 2.5,
    8: 2.0,
    9: 1.5,
    10: 1.0,
    11: 0.6,
    12: 0.4,
}


# 時刻係数（時間帯ごと）
TIME_COEFFICIENTS = [
    ((0, 4), 0.0),
    ((5, 8), 0.5),
    ((9, 9), 1.0),
    ((10, 13), 2.0),
    ((14, 14), 1.0),
    ((15, 16), 0.5),
    ((17, 23), 0.0),
]


# 天候係数
WEATHER_COEFFICIENTS = {
    "sunny": 1.0,
    "cloudy": 0.8,
    "overcast": 0.6,
    "rain": 0.3,
    "snow": 0.3,
    "rain": 0.3,
}


# 日焼け止め係数（仕様書に基づく）
SUNSCREEN_COEFFICIENTS = {
    "none": 1.0,
    "no_reapply": 0.3,
    "reapply": 0.1,
}


SCORE_BANDS: list[tuple[float, float | None, str, str]] = [
    (0.0, 1.9, "低", "肌への影響は軽微です。"),
    (2.0, 4.9, "中", "やや日焼けの可能性があります。長時間の外出時はケアを推奨します。"),
    (5.0, 8.9, "高", "日焼けの危険性があります。冷却や保湿などのアフターケアを行ってください。"),
    (9.0, None, "極めて高", "強い紫外線ダメージを受けています。しっかりと肌を休ませてください。"),
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
    # 範囲外でも安全に0を返す
    return 0.0


def _coerce_date(date_value: date | str) -> date:
    if isinstance(date_value, str):
        try:
            return datetime.strptime(date_value, "%Y-%m-%d").date()
        except ValueError as exc:
            raise ValueError("日付は YYYY-MM-DD 形式で入力してください。") from exc
    if isinstance(date_value, date):
        return date_value
    raise ValueError("date_value は date または YYYY-MM-DD 文字列で指定してください。")


def _coerce_periods(periods: Sequence[tuple[str, str]] | Sequence[dict[str, str]]) -> list[tuple[str, str]]:
    normalized_periods: list[tuple[str, str]] = []
    for period in periods:
        if isinstance(period, dict):
            start_time = period.get("start_time")
            end_time = period.get("end_time")
        else:
            start_time, end_time = period
        if not start_time or not end_time:
            raise ValueError("外出区間には開始時刻と終了時刻が必要です。")
        normalized_periods.append((start_time, end_time))
    if not normalized_periods:
        raise ValueError("外出区間を1件以上入力してください。")
    return normalized_periods


def _calculate_time_weight(start_minutes: int, end_minutes: int) -> tuple[float, float]:
    duration_minutes = end_minutes - start_minutes
    duration_hours = duration_minutes / 60.0
    current_minute = start_minutes
    weighted_time_coefficient = 0.0

    while current_minute < end_minutes:
        hour = (current_minute // 60) % 24
        next_minute = min(end_minutes, ((current_minute // 60) + 1) * 60)
        segment_minutes = next_minute - current_minute
        weighted_time_coefficient += _get_time_coefficient(hour) * (segment_minutes / 60.0)
        current_minute = next_minute

    return duration_hours, weighted_time_coefficient


def get_score_band(total: float) -> dict[str, str | float | None]:
    for lower_bound, upper_bound, label, message in SCORE_BANDS:
        if total >= lower_bound and (upper_bound is None or total <= upper_bound):
            return {
                "lower_bound": lower_bound,
                "upper_bound": upper_bound,
                "label": label,
                "message": message,
            }
    return {
        "lower_bound": 0.0,
        "upper_bound": None,
        "label": "極めて高",
        "message": "強い紫外線ダメージを受けています。しっかりと肌を休ませてください。",
    }


def calculate_exposure_periods(
    *,
    periods: Sequence[tuple[str, str]] | Sequence[dict[str, str]],
    date_value: date | str,
    weather: str,
    sunscreen: str,
) -> dict[str, float | int | str | list[dict[str, float | str]]]:
    """複数の外出区間に対する日焼け量を計算する。"""
    parsed_date = _coerce_date(date_value)
    normalized_periods = _coerce_periods(periods)

    if weather not in WEATHER_COEFFICIENTS:
        raise ValueError("天候は指定された選択肢のいずれかで指定してください。")
    weather_coefficient = WEATHER_COEFFICIENTS[weather]

    if sunscreen not in SUNSCREEN_COEFFICIENTS:
        raise ValueError("日焼け止めは 'none','no_reapply','reapply' のいずれかで指定してください。")
    sunscreen_coefficient = SUNSCREEN_COEFFICIENTS[sunscreen]

    season_coefficient = SEASON_COEFFICIENTS_BY_MONTH.get(parsed_date.month, 1.0)

    total_duration_hours = 0.0
    total_time_weight = 0.0
    period_details: list[dict[str, float | str]] = []

    for start_time, end_time in normalized_periods:
        start_minutes = _parse_time(start_time)
        end_minutes = _parse_time(end_time)

        if start_minutes >= end_minutes:
            raise ValueError("開始時刻は終了時刻より前である必要があります。")

        duration_hours, weighted_time_coefficient = _calculate_time_weight(start_minutes, end_minutes)
        time_coefficient = weighted_time_coefficient / duration_hours if duration_hours > 0 else 0.0
        period_total = (
            duration_hours
            * 1.0
            * season_coefficient
            * time_coefficient
            * weather_coefficient
            * sunscreen_coefficient
        )

        total_duration_hours += duration_hours
        total_time_weight += weighted_time_coefficient
        period_details.append(
            {
                "start_time": start_time,
                "end_time": end_time,
                "duration_hours": duration_hours,
                "time_coefficient": time_coefficient,
                "total": period_total,
            }
        )

    time_coefficient = total_time_weight / total_duration_hours if total_duration_hours > 0 else 0.0
    total = sum(float(item["total"]) for item in period_details)

    score_band = get_score_band(total)

    return {
        "total": total,
        "duration_hours": total_duration_hours,
        "season_coefficient": season_coefficient,
        "sunscreen_coefficient": sunscreen_coefficient,
        "time_coefficient": time_coefficient,
        "weather_coefficient": weather_coefficient,
        "score_label": score_band["label"],
        "score_message": score_band["message"],
        "period_details": period_details,
    }


def calculate_exposure(
    *,
    start_time: str,
    end_time: str,
    date_value: date | str,
    weather: str,
    sunscreen: str,
) -> dict[str, float | int | str]:
    """仕様書に基づいた日焼け量（紫外線暴露スコア）を計算する。

    - `date_value` は datetime.date または YYYY-MM-DD 形式の文字列。
    - `weather` は 'sunny' | 'cloudy' | 'rain' のいずれか。
    - `sunscreen` は 'none' | 'no_reapply' | 'reapply' のいずれか。
    """
    return calculate_exposure_periods(
        periods=[(start_time, end_time)],
        date_value=date_value,
        weather=weather,
        sunscreen=sunscreen,
    )
