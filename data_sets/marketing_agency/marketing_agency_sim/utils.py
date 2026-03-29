from __future__ import annotations

import csv
import json
import random
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from pydantic import BaseModel


def iso_ts(d: datetime) -> str:
    return d.strftime("%Y-%m-%d %H:%M:%S")


def iso_date(d: date) -> str:
    return d.isoformat()


def rand_dt(start: datetime, end: datetime) -> datetime:
    delta = int((end - start).total_seconds())
    return start + timedelta(seconds=random.randint(0, max(1, delta)))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def json_cell(value: Any) -> str:
    return json.dumps(value, separators=(",", ":"), ensure_ascii=True)


def models_to_rows(models: list[BaseModel]) -> list[dict[str, Any]]:
    return [m.model_dump(by_alias=True) for m in models]

