from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_records(path: str | Path | None = None) -> list[dict[str, Any]]:
    storage_path = Path(path or "data/records.json")
    if not storage_path.exists():
        return []

    try:
        with storage_path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except json.JSONDecodeError:
        return []


def save_record(record: dict[str, Any], path: str | Path | None = None) -> None:
    storage_path = Path(path or "data/records.json")
    storage_path.parent.mkdir(parents=True, exist_ok=True)

    records = load_records(storage_path)
    existing = [item for item in records if item.get("date") == record.get("date")]
    if existing:
        updated_records = [
            record if item.get("date") == record.get("date") else item for item in records
        ]
    else:
        updated_records = [*records, record]

    with storage_path.open("w", encoding="utf-8") as handle:
        json.dump(updated_records, handle, ensure_ascii=False, indent=2)
