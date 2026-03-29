from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class Config:
    companies: int
    employees: int
    years: int
    time_entries: int
    seed: int
    """If set, load this file with python-dotenv before connecting."""
    dotenv_path: Path | None = None
    """If set, write run summary (counts) as JSON to this path."""
    manifest_path: Path | None = None
    wait_for_async_insert: int = 1
