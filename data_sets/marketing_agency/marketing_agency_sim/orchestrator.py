from __future__ import annotations

import json
import random
from datetime import datetime, timedelta

from .bamboohr import BambooHRSimulator
from .config import Config
from .harvest import HarvestSimulator
from .hubspot import HubSpotSimulator
from .netsuite import NetSuiteSimulator
from .utils import iso_ts, models_to_rows, write_csv


def generate_dataset(cfg: Config) -> None:
    random.seed(cfg.seed)
    now = datetime.now()
    start = now - timedelta(days=cfg.years * 365)

    hubspot_sim = HubSpotSimulator(now=now, start=start, years=cfg.years)
    bamboohr_sim = BambooHRSimulator(now=now, start=start, years=cfg.years)
    harvest_sim = HarvestSimulator(now=now, start=start, years=cfg.years)
    netsuite_sim = NetSuiteSimulator(now=now, start=start, years=cfg.years)

    hubspot_owners = hubspot_sim.generate_owners()
    hubspot_companies = hubspot_sim.generate_companies(cfg.companies)
    hubspot_contacts, hubspot_deals = hubspot_sim.generate_contacts_and_deals(hubspot_companies)

    bamboo_employees = bamboohr_sim.generate_employees(cfg.employees)
    bamboo_time_off = bamboohr_sim.generate_time_off(bamboo_employees)

    harvest_clients, hs_to_hv_client = harvest_sim.generate_clients(hubspot_companies)
    harvest_users = harvest_sim.generate_users_from_employees(bamboo_employees)
    harvest_tasks = harvest_sim.generate_tasks()
    harvest_projects, harvest_project_assignments = harvest_sim.generate_projects_and_assignments(
        hubspot_deals, hs_to_hv_client, harvest_users
    )
    harvest_time_entries = harvest_sim.generate_time_entries(
        cfg.time_entries, harvest_users, harvest_projects, harvest_tasks
    )

    netsuite_customers, company_to_ns = netsuite_sim.generate_customers(hubspot_companies)
    netsuite_invoices, netsuite_payments = netsuite_sim.generate_invoices_and_payments(
        harvest_projects, hs_to_hv_client, company_to_ns
    )
    netsuite_vendor_bills = netsuite_sim.generate_vendor_bills()

    files = {
        "raw_hubspot_companies.csv": models_to_rows(hubspot_companies),
        "raw_hubspot_contacts.csv": models_to_rows(hubspot_contacts),
        "raw_hubspot_deals.csv": models_to_rows(hubspot_deals),
        "raw_hubspot_owners.csv": models_to_rows(hubspot_owners),
        "raw_netsuite_customers.csv": models_to_rows(netsuite_customers),
        "raw_netsuite_invoices.csv": models_to_rows(netsuite_invoices),
        "raw_netsuite_payments.csv": models_to_rows(netsuite_payments),
        "raw_netsuite_vendor_bills.csv": models_to_rows(netsuite_vendor_bills),
        "raw_harvest_clients.csv": models_to_rows(harvest_clients),
        "raw_harvest_projects.csv": models_to_rows(harvest_projects),
        "raw_harvest_users.csv": models_to_rows(harvest_users),
        "raw_harvest_tasks.csv": models_to_rows(harvest_tasks),
        "raw_harvest_project_assignments.csv": models_to_rows(harvest_project_assignments),
        "raw_harvest_time_entries.csv": models_to_rows(harvest_time_entries),
        "raw_bamboohr_employees.csv": models_to_rows(bamboo_employees),
        "raw_bamboohr_time_off.csv": models_to_rows(bamboo_time_off),
    }
    for filename, rows in files.items():
        write_csv(cfg.outdir / filename, rows)

    manifest = {
        "generated_at": iso_ts(now),
        "seed": cfg.seed,
        "parameters": {
            "companies": cfg.companies,
            "employees": cfg.employees,
            "years": cfg.years,
            "time_entries": cfg.time_entries,
        },
        "files": {k: len(v) for k, v in files.items()},
    }
    with (cfg.outdir / "manifest.json").open("w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"Dataset written to: {cfg.outdir}")
    for name, count in manifest["files"].items():
        print(f" - {name}: {count} rows")

