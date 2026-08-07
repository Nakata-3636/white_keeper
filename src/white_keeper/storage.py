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
            loaded = json.load(handle)
            if isinstance(loaded, list):
                return loaded
            return []
    except json.JSONDecodeError:
        return []


def save_record(record: dict[str, Any], path: str | Path | None = None) -> None:
    storage_path = Path(path or "data/records.json")
    storage_path.parent.mkdir(parents=True, exist_ok=True)

    records = load_records(storage_path)
    record_id = record.get("record_id")

    if record_id is not None:
        updated_records = [
            record if item.get("record_id") == record_id else item for item in records
        ]
        if not any(item.get("record_id") == record_id for item in records):
            updated_records.append(record)
    else:
        updated_records = [*records, record]

    with storage_path.open("w", encoding="utf-8") as handle:
        json.dump(updated_records, handle, ensure_ascii=False, indent=2)
