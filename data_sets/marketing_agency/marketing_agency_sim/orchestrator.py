from __future__ import annotations

import json
import random
from datetime import datetime, timedelta

from .bamboohr import BambooHRSimulator
from .clickhouse_upload import (
    clickhouse_database_name,
    create_clickhouse_client,
    ensure_database,
    ensure_tables,
    insert_rows_async,
    load_dotenv_file,
)
from .config import Config
from .harvest import HarvestSimulator
from .hubspot import HubSpotSimulator
from .netsuite import NetSuiteSimulator
from .utils import iso_ts, models_to_rows


def generate_dataset(cfg: Config) -> None:
    load_dotenv_file(cfg.dotenv_path)
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

    tables = {
        "raw_hubspot_companies": models_to_rows(hubspot_companies),
        "raw_hubspot_contacts": models_to_rows(hubspot_contacts),
        "raw_hubspot_deals": models_to_rows(hubspot_deals),
        "raw_hubspot_owners": models_to_rows(hubspot_owners),
        "raw_netsuite_customers": models_to_rows(netsuite_customers),
        "raw_netsuite_invoices": models_to_rows(netsuite_invoices),
        "raw_netsuite_payments": models_to_rows(netsuite_payments),
        "raw_netsuite_vendor_bills": models_to_rows(netsuite_vendor_bills),
        "raw_harvest_clients": models_to_rows(harvest_clients),
        "raw_harvest_projects": models_to_rows(harvest_projects),
        "raw_harvest_users": models_to_rows(harvest_users),
        "raw_harvest_tasks": models_to_rows(harvest_tasks),
        "raw_harvest_project_assignments": models_to_rows(harvest_project_assignments),
        "raw_harvest_time_entries": models_to_rows(harvest_time_entries),
        "raw_bamboohr_employees": models_to_rows(bamboo_employees),
        "raw_bamboohr_time_off": models_to_rows(bamboo_time_off),
    }

    db = clickhouse_database_name()
    client = create_clickhouse_client()
    ensure_database(client, db)
    ensure_tables(client, db)

    counts: dict[str, int] = {}
    for table, rows in tables.items():
        n = insert_rows_async(
            client,
            db,
            table,
            rows,
            wait_for_async_insert=cfg.wait_for_async_insert,
        )
        counts[table] = n
        print(f"{db}.{table}: {n} rows")

    if cfg.manifest_path is not None:
        cfg.manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest = {
            "generated_at": iso_ts(now),
            "seed": cfg.seed,
            "clickhouse_database": db,
            "parameters": {
                "companies": cfg.companies,
                "employees": cfg.employees,
                "years": cfg.years,
                "time_entries": cfg.time_entries,
            },
            "tables": counts,
        }
        with cfg.manifest_path.open("w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
