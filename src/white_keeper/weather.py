from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
import json
from functools import lru_cache
from urllib.parse import quote, urlencode
from urllib.request import urlopen
from urllib.error import URLError


WEATHER_LABELS: dict[str, str] = {
    "sunny": "晴れ",
    "cloudy": "曇り",
    "overcast": "厚い曇り",
    "rain": "雨・雪",
}

WEATHER_OPTIONS = ["晴れ", "曇り", "厚い曇り", "雨・雪"]
WEATHER_KEYS_BY_LABEL = {label: key for key, label in WEATHER_LABELS.items()}
SEVERITY_ORDER = {"sunny": 0, "cloudy": 1, "overcast": 2, "rain": 3}


@dataclass(frozen=True)
class Location:
    name: str
    latitude: float
    longitude: float
    timezone: str = "Asia/Tokyo"


def _parse_date(date_value: date | str) -> date:
    if isinstance(date_value, date):
        return date_value
    return datetime.strptime(date_value, "%Y-%m-%d").date()


def _open_json(url: str) -> dict[str, object]:
    with urlopen(url, timeout=10) as response:  # noqa: S310
        payload = response.read().decode("utf-8")
    return json.loads(payload)


@lru_cache(maxsize=128)
def resolve_location(region_query: str) -> Location:
    query = region_query.strip()
    if not query:
        raise ValueError("地域を入力してください。")

    url = "https://geocoding-api.open-meteo.com/v1/search?" + urlencode(
        {"name": query, "count": 1, "language": "ja", "format": "json"}
    )
    data = _open_json(url)
    results = data.get("results")
    if not isinstance(results, list) or not results:
        raise ValueError("地域から位置情報を取得できませんでした。")

    first = results[0]
    if not isinstance(first, dict):
        raise ValueError("地域から位置情報を取得できませんでした。")

    name_parts = [str(first.get(part, "")).strip() for part in ("admin1", "admin2", "name")]
    name = "".join(part for part in name_parts if part)
    return Location(
        name=name or query,
        latitude=float(first["latitude"]),
        longitude=float(first["longitude"]),
        timezone=str(first.get("timezone", "Asia/Tokyo")),
    )


def _weather_key_from_code(code: int) -> str:
    if code == 0:
        return "sunny"
    if code in {1, 2}:
        return "cloudy"
    if code in {3, 45, 48}:
        return "overcast"
    if code in {51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 71, 73, 75, 77, 80, 81, 82, 85, 86, 95, 96, 99}:
        return "rain"
    return "overcast"


def _weather_key_from_hourly_codes(codes: list[int]) -> str:
    if not codes:
        raise ValueError("天候データが取得できませんでした。")
    return max((_weather_key_from_code(code) for code in codes), key=lambda key: SEVERITY_ORDER[key])


def _fetch_weather_code(location: Location, date_value: date) -> tuple[str, list[int]]:
    endpoint = "https://api.open-meteo.com/v1/forecast"
    if date_value < date.today():
        endpoint = "https://archive-api.open-meteo.com/v1/archive"

    url = endpoint + "?" + urlencode(
        {
            "latitude": location.latitude,
            "longitude": location.longitude,
            "start_date": date_value.isoformat(),
            "end_date": date_value.isoformat(),
            "hourly": "weather_code",
            "timezone": location.timezone,
        }
    )
    data = _open_json(url)
    hourly = data.get("hourly")
    if not isinstance(hourly, dict):
        raise ValueError("天候データが取得できませんでした。")

    codes = hourly.get("weather_code")
    if not isinstance(codes, list):
        raise ValueError("天候データが取得できませんでした。")

    int_codes = [int(code) for code in codes]
    return _weather_key_from_hourly_codes(int_codes), int_codes


def fetch_weather_suggestion(region_query: str, date_value: date | str) -> dict[str, object]:
    parsed_date = _parse_date(date_value)
    try:
        location = resolve_location(region_query)
        weather_key, weather_codes = _fetch_weather_code(location, parsed_date)
    except (ValueError, URLError, TimeoutError, json.JSONDecodeError, KeyError):
        return {
            "source": "manual",
            "weather_key": None,
            "weather_label": None,
            "location_name": region_query.strip(),
            "weather_codes": [],
            "message": "天候の自動取得に失敗したため、手動で選択してください。",
        }

    return {
        "source": "api",
        "weather_key": weather_key,
        "weather_label": WEATHER_LABELS[weather_key],
        "location_name": location.name,
        "weather_codes": weather_codes,
        "message": f"{location.name} の天候候補を自動取得しました。",
    }


def weather_label_to_key(label: str) -> str:
    try:
        return WEATHER_KEYS_BY_LABEL[label]
    except KeyError as exc:
        raise ValueError("天候の選択肢が不正です。") from exc