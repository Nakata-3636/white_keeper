from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

PACKAGE_ROOT = Path(__file__).resolve().parent
SRC_ROOT = PACKAGE_ROOT.parent
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from white_keeper.calculator import calculate_exposure
from white_keeper.storage import load_records, save_record


DATA_PATH = Path("data/records.json")


def main() -> None:
    st.set_page_config(page_title="White Keeper", page_icon="☀️", layout="wide")

    st.title("White Keeper")
    st.caption("日焼け量を簡単に見積もるためのWebアプリです。")

    with st.form("exposure_form"):
        date = st.date_input("日付")
        start_time = st.text_input("外出開始時刻", value="10:00")
        end_time = st.text_input("外出終了時刻", value="13:20")
        season = st.selectbox("季節", ["winter", "spring", "summer", "autumn"])
        sunny = st.radio("天候", [True, False], format_func=lambda value: "晴れ" if value else "くもり/雨")
        sunscreen = st.radio("日焼け止め", [True, False], format_func=lambda value: "塗った" if value else "塗っていない")

        submitted = st.form_submit_button("計算して保存")

    if submitted:
        try:
            result = calculate_exposure(
                start_time=start_time,
                end_time=end_time,
                season=season,
                sunscreen=sunscreen,
                sunny=sunny,
            )
        except ValueError as exc:
            st.error(str(exc))
        else:
            record = {
                "date": date.strftime("%Y-%m-%d"),
                "start_time": start_time,
                "end_time": end_time,
                "season": season,
                "sunscreen": sunscreen,
                "sunny": sunny,
                "total": round(float(result["total"]), 3),
            }
            save_record(record, DATA_PATH)
            st.success("保存しました。")
            st.metric("日焼け量の積算値", f"{record['total']:.3f}")
            st.write(
                f"期間: {start_time}〜{end_time} / 季節係数: {result['season_coefficient']} / 日焼け止め係数: {result['sunscreen_coefficient']} / 時刻係数: {result['time_coefficient']}"
            )

    st.subheader("保存済み履歴")
    records = load_records(DATA_PATH)
    if records:
        st.dataframe(
            [
                {
                    "date": item["date"],
                    "start_time": item["start_time"],
                    "end_time": item["end_time"],
                    "season": item["season"],
                    "sunny": "晴れ" if item["sunny"] else "くもり/雨",
                    "sunscreen": "塗った" if item["sunscreen"] else "塗っていない",
                    "total": item["total"],
                }
                for item in records
            ]
        )
    else:
        st.info("まだ保存された記録はありません。")


if __name__ == "__main__":
    main()
