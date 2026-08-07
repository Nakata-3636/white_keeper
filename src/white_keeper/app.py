from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import streamlit as st

PACKAGE_ROOT = Path(__file__).resolve().parent
SRC_ROOT = PACKAGE_ROOT.parent
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from white_keeper.calculator import calculate_exposure
from white_keeper.storage import delete_record, load_records, save_record
from white_keeper.weather import WEATHER_OPTIONS, weather_label_to_key


DATA_PATH = Path("data/records.json")
SUNSCREEN_OPTIONS = ["なし", "あり（塗り直しなし）", "あり（2〜3時間ごとに塗り直し）"]


def _get_score_message(score_label: str, score_message: str) -> str:
    return f"【{score_label}】{score_message}"


def _parse_periods(period_count: int) -> list[tuple[str, str]]:
    periods: list[tuple[str, str]] = []
    for index in range(period_count):
        start_time = st.session_state.get(f"start_time_{index}", "10:00")
        end_time = st.session_state.get(f"end_time_{index}", "13:20")
        periods.append((start_time, end_time))
    return periods


def _is_displayable_record(record: dict[str, object]) -> bool:
    record_id = record.get("record_id")
    return isinstance(record_id, str) and len(record_id.strip()) > 0


def main() -> None:
    st.set_page_config(page_title="White Keeper", page_icon="☀️", layout="wide")

    st.title("White Keeper")
    st.caption("日付・外出区間から、日焼け量を見積もります。")

    date = st.date_input("日付")

    st.subheader("外出区間")
    period_count = int(st.number_input("区間数", min_value=1, max_value=5, value=1, step=1))
    for index in range(period_count):
        st.markdown(f"#### 区間 {index + 1}")
        col_start, col_end = st.columns(2)
        with col_start:
            st.text_input("開始時刻", key=f"start_time_{index}", value=st.session_state.get(f"start_time_{index}", "10:00"))
        with col_end:
            st.text_input("終了時刻", key=f"end_time_{index}", value=st.session_state.get(f"end_time_{index}", "13:20"))

    weather_label = st.selectbox(
        "天候",
        WEATHER_OPTIONS,
        index=0,
        help="手動で選択してください。",
    )
    sunscreen_label = st.selectbox("日焼け止め", SUNSCREEN_OPTIONS)

    if st.button("計算して保存", type="primary"):
        try:
            periods = _parse_periods(period_count)
            weather_key = weather_label_to_key(weather_label)
            sunscreen_key = (
                "none"
                if sunscreen_label == "なし"
                else ("no_reapply" if sunscreen_label == "あり（塗り直しなし）" else "reapply")
            )

            result = calculate_exposure_periods_for_app(
                periods=periods,
                date_value=date,
                weather=weather_key,
                sunscreen=sunscreen_key,
            )
        except ValueError as exc:
            st.error(str(exc))
        else:
            record = {
                "record_id": datetime.now().strftime("%Y%m%d%H%M%S%f"),
                "version": 2,
                "date": date.strftime("%Y-%m-%d"),
                "periods": [
                    {"start_time": start_time, "end_time": end_time} for start_time, end_time in periods
                ],
                "weather": weather_label,
                "sunscreen": sunscreen_label,
                "total": round(float(result["total"]), 3),
                "score_label": result["score_label"],
                "score_message": result["score_message"],
            }
            save_record(record, DATA_PATH)
            st.success("保存しました。")
            st.metric("日焼け量の積算値", f"{record['total']:.3f}")
            st.info(_get_score_message(str(record["score_label"]), str(record["score_message"])))
            st.write(
                f"季節係数: {result['season_coefficient']} / 日焼け止め係数: {result['sunscreen_coefficient']} / 時刻係数: {result['time_coefficient']} / 天候係数: {result['weather_coefficient']}"
            )
            if result.get("period_details"):
                st.write("区間別内訳")
                st.dataframe(result["period_details"])

    st.subheader("保存済み履歴")
    records = load_records(DATA_PATH)
    display_records = [item for item in records if _is_displayable_record(item)]
    hidden_count = len(records) - len(display_records)

    if display_records:
        total_sum = sum(float(item.get("total", 0.0)) for item in display_records)
        st.metric("履歴の積算値", f"{total_sum:.3f}")
        st.dataframe(
            [
                {
                    "date": item.get("date", "-"),
                    "periods": len(item.get("periods", [])) if isinstance(item.get("periods"), list) else 1,
                    "weather": item.get("weather", "-"),
                    "sunscreen": item.get("sunscreen", "-"),
                    "score_label": item.get("score_label", "-"),
                    "total": item.get("total"),
                }
                for item in display_records
            ]
        )

        if hidden_count > 0:
            st.caption(f"旧形式の履歴 {hidden_count} 件は非表示です。")

        st.markdown("#### 履歴削除")
        for record in display_records:
            record_id = str(record.get("record_id", ""))
            if not record_id:
                continue
            cols = st.columns([4, 1])
            with cols[0]:
                st.write(
                    f"{record.get('date', '-')}",
                    f"/ {record.get('weather', '-')} / {record.get('sunscreen', '-')} / {record.get('total', '-')}",
                )
            with cols[1]:
                if st.button("削除", key=f"delete_{record_id}"):
                    if delete_record(record_id, DATA_PATH):
                        st.success("履歴を削除しました。")
                        st.rerun()
                    else:
                        st.error("削除できませんでした。")
    else:
        st.info("まだ保存された記録はありません。")


def calculate_exposure_periods_for_app(
    *,
    periods: list[tuple[str, str]],
    date_value,
    weather: str,
    sunscreen: str,
) -> dict[str, object]:
    from white_keeper.calculator import calculate_exposure_periods

    return calculate_exposure_periods(periods=periods, date_value=date_value, weather=weather, sunscreen=sunscreen)


if __name__ == "__main__":
    main()
