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
    outdir: Path

