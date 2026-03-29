#!/usr/bin/env python3
"""CLI entrypoint: generate synthetic marketing agency data and load into ClickHouse."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Running `python marketing_agency_sim/simulate_...py` puts only the inner folder on sys.path;
# the package root is the parent directory (folder that contains `marketing_agency_sim/`).
_pkg_root = Path(__file__).resolve().parent.parent
if str(_pkg_root) not in sys.path:
    sys.path.insert(0, str(_pkg_root))

from marketing_agency_sim.config import Config
from marketing_agency_sim.orchestrator import generate_dataset


def parse_args() -> Config:
    parser = argparse.ArgumentParser(
        description="Generate synthetic marketing agency raw data and insert into ClickHouse (async insert)."
    )
    parser.add_argument("--companies", type=int, default=120, help="Number of companies/clients.")
    parser.add_argument("--employees", type=int, default=65, help="Number of Bamboo/Harvest users.")
    parser.add_argument("--years", type=int, default=2, help="Time horizon in years.")
    parser.add_argument("--time-entries", type=int, default=85000, help="Harvest time entry row count.")
    parser.add_argument("--seed", type=int, default=42, help="RNG seed for reproducible data.")
    parser.add_argument(
        "--env-file",
        type=Path,
        default=None,
        help="Path to .env (default: marketing_agency/.env then ./.env if present).",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=None,
        help="Optional path to write a JSON summary (table row counts).",
    )
    parser.add_argument(
        "--wait-for-async-insert",
        type=int,
        default=1,
        choices=(0, 1),
        help="ClickHouse wait_for_async_insert: 1 wait for flush (safer), 0 return after queueing.",
    )
    args = parser.parse_args()
    return Config(
        companies=args.companies,
        employees=args.employees,
        years=args.years,
        time_entries=args.time_entries,
        seed=args.seed,
        dotenv_path=args.env_file,
        manifest_path=args.manifest,
        wait_for_async_insert=args.wait_for_async_insert,
    )


if __name__ == "__main__":
    generate_dataset(parse_args())
