#!/usr/bin/env python3
"""CLI entrypoint for modular marketing agency dataset simulation."""

from __future__ import annotations

import argparse
from pathlib import Path

from marketing_agency_sim.config import Config
from marketing_agency_sim.orchestrator import generate_dataset


def parse_args() -> Config:
    parser = argparse.ArgumentParser(
        description="Generate synthetic marketing agency raw-layer CSV dataset."
    )
    parser.add_argument("--companies", type=int, default=120, help="Number of companies/clients.")
    parser.add_argument("--employees", type=int, default=65, help="Number of Bamboo/Harvest users.")
    parser.add_argument("--years", type=int, default=2, help="Time horizon in years.")
    parser.add_argument("--time-entries", type=int, default=85000, help="Harvest time entry row count.")
    parser.add_argument("--seed", type=int, default=42, help="RNG seed for reproducible data.")
    parser.add_argument("--outdir", type=Path, default=Path("simulated_dataset"), help="Output directory.")
    args = parser.parse_args()
    return Config(
        companies=args.companies,
        employees=args.employees,
        years=args.years,
        time_entries=args.time_entries,
        seed=args.seed,
        outdir=args.outdir,
    )


if __name__ == "__main__":
    generate_dataset(parse_args())
