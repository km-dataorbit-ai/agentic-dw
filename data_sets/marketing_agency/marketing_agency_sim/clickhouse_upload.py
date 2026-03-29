from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

DEFAULT_DATABASE = "raw_marketing_agency_data"
INSERT_BATCH_SIZE = 50_000

# (column_name, ClickHouse type). "class" is quoted in DDL.
_TABLE_COLUMNS: dict[str, list[tuple[str, str]]] = {
    "raw_hubspot_companies": [
        ("_dataorbit_sync_id", "String"),
        ("_dataorbit_synced_at", "String"),
        ("_dataorbit_is_deleted", "Bool"),
        ("hs_object_id", "String"),
        ("name", "String"),
        ("domain", "String"),
        ("industry", "String"),
        ("hubspot_owner_id", "String"),
        ("createdate", "String"),
        ("hs_lastmodifieddate", "String"),
        ("properties", "String"),
    ],
    "raw_hubspot_contacts": [
        ("_dataorbit_sync_id", "String"),
        ("_dataorbit_synced_at", "String"),
        ("_dataorbit_is_deleted", "Bool"),
        ("hs_object_id", "String"),
        ("email", "String"),
        ("firstname", "String"),
        ("lastname", "String"),
        ("company", "String"),
        ("jobtitle", "String"),
        ("lifecyclestage", "String"),
        ("associated_company_id", "String"),
        ("hubspot_owner_id", "String"),
        ("properties", "String"),
    ],
    "raw_hubspot_deals": [
        ("_dataorbit_sync_id", "String"),
        ("_dataorbit_synced_at", "String"),
        ("_dataorbit_is_deleted", "Bool"),
        ("hs_object_id", "String"),
        ("dealname", "String"),
        ("amount", "Float64"),
        ("dealstage", "String"),
        ("pipeline", "String"),
        ("closedate", "String"),
        ("createdate", "String"),
        ("hs_deal_stage_probability", "Float64"),
        ("hubspot_owner_id", "String"),
        ("associated_company_ids", "String"),
        ("properties", "String"),
    ],
    "raw_hubspot_owners": [
        ("_dataorbit_sync_id", "String"),
        ("_dataorbit_synced_at", "String"),
        ("owner_id", "String"),
        ("email", "String"),
        ("first_name", "String"),
        ("last_name", "String"),
        ("user_id", "String"),
    ],
    "raw_netsuite_customers": [
        ("_dataorbit_sync_id", "String"),
        ("_dataorbit_synced_at", "String"),
        ("id", "String"),
        ("company_name", "String"),
        ("email", "String"),
        ("entity_id", "String"),
        ("subsidiary", "String"),
        ("terms", "String"),
        ("balance", "Float64"),
        ("category", "String"),
        ("last_modified_date", "String"),
        ("custom_fields", "String"),
    ],
    "raw_netsuite_invoices": [
        ("_dataorbit_sync_id", "String"),
        ("_dataorbit_synced_at", "String"),
        ("id", "String"),
        ("entity_id", "String"),
        ("tran_date", "String"),
        ("due_date", "String"),
        ("total", "Float64"),
        ("amount_remaining", "Float64"),
        ("status", "String"),
        ("line_items", "String"),
        ("last_modified_date", "String"),
    ],
    "raw_netsuite_payments": [
        ("_dataorbit_sync_id", "String"),
        ("_dataorbit_synced_at", "String"),
        ("id", "String"),
        ("customer_id", "String"),
        ("total", "Float64"),
        ("tran_date", "String"),
        ("apply_list", "String"),
        ("last_modified_date", "String"),
    ],
    "raw_netsuite_vendor_bills": [
        ("_dataorbit_sync_id", "String"),
        ("_dataorbit_synced_at", "String"),
        ("id", "String"),
        ("entity_id", "String"),
        ("tran_date", "String"),
        ("total", "Float64"),
        ("line_items", "String"),
        ("class", "String"),
        ("department", "String"),
        ("last_modified_date", "String"),
    ],
    "raw_harvest_clients": [
        ("_dataorbit_sync_id", "String"),
        ("_dataorbit_synced_at", "String"),
        ("id", "Int64"),
        ("name", "String"),
        ("is_active", "Bool"),
        ("address", "String"),
        ("currency", "String"),
    ],
    "raw_harvest_projects": [
        ("_dataorbit_sync_id", "String"),
        ("_dataorbit_synced_at", "String"),
        ("id", "Int64"),
        ("client_id", "Int64"),
        ("name", "String"),
        ("code", "String"),
        ("is_active", "Bool"),
        ("is_billable", "Bool"),
        ("budget", "Float64"),
        ("budget_by", "String"),
        ("fee", "Float64"),
        ("hourly_rate", "Float64"),
        ("cost_budget", "Float64"),
        ("starts_on", "String"),
        ("ends_on", "String"),
        ("over_budget_notification_percentage", "Float64"),
        ("created_at", "String"),
        ("updated_at", "String"),
    ],
    "raw_harvest_users": [
        ("_dataorbit_sync_id", "String"),
        ("_dataorbit_synced_at", "String"),
        ("id", "Int64"),
        ("first_name", "String"),
        ("last_name", "String"),
        ("email", "String"),
        ("is_active", "Bool"),
        ("is_contractor", "Bool"),
        ("roles", "String"),
        ("cost_rate", "Float64"),
        ("default_hourly_rate", "Float64"),
        ("weekly_capacity", "Int64"),
        ("created_at", "String"),
        ("updated_at", "String"),
    ],
    "raw_harvest_tasks": [
        ("_dataorbit_sync_id", "String"),
        ("_dataorbit_synced_at", "String"),
        ("id", "Int64"),
        ("name", "String"),
        ("is_default", "Bool"),
        ("default_hourly_rate", "Float64"),
        ("is_active", "Bool"),
    ],
    "raw_harvest_project_assignments": [
        ("_dataorbit_sync_id", "String"),
        ("_dataorbit_synced_at", "String"),
        ("id", "Int64"),
        ("project_id", "Int64"),
        ("user_id", "Int64"),
        ("is_active", "Bool"),
        ("hourly_rate", "Float64"),
        ("budget", "Float64"),
    ],
    "raw_harvest_time_entries": [
        ("_dataorbit_sync_id", "String"),
        ("_dataorbit_synced_at", "String"),
        ("id", "Int64"),
        ("user_id", "Int64"),
        ("project_id", "Int64"),
        ("task_id", "Int64"),
        ("spent_date", "String"),
        ("hours", "Float64"),
        ("billable", "Bool"),
        ("billable_rate", "Float64"),
        ("cost_rate", "Float64"),
        ("notes", "String"),
        ("is_locked", "Bool"),
        ("created_at", "String"),
        ("updated_at", "String"),
    ],
    "raw_bamboohr_employees": [
        ("_dataorbit_sync_id", "String"),
        ("_dataorbit_synced_at", "String"),
        ("id", "String"),
        ("display_name", "String"),
        ("first_name", "String"),
        ("last_name", "String"),
        ("work_email", "String"),
        ("department", "String"),
        ("division", "String"),
        ("job_title", "String"),
        ("supervisor_id", "String"),
        ("location", "String"),
        ("hire_date", "String"),
        ("termination_date", "String"),
        ("status", "String"),
        ("pay_rate", "Float64"),
        ("pay_type", "String"),
        ("pay_per", "String"),
        ("employee_number", "String"),
        ("custom_fields", "String"),
    ],
    "raw_bamboohr_time_off": [
        ("_dataorbit_sync_id", "String"),
        ("_dataorbit_synced_at", "String"),
        ("id", "String"),
        ("employee_id", "String"),
        ("time_off_type", "String"),
        ("start_date", "String"),
        ("end_date", "String"),
        ("status", "String"),
        ("amount", "Float64"),
        ("unit", "String"),
    ],
}


def load_dotenv_file(dotenv_path: Path | None) -> None:
    if dotenv_path is not None:
        load_dotenv(dotenv_path)
        return
    root = Path(__file__).resolve().parent.parent
    for p in (root / ".env", Path.cwd() / ".env"):
        if p.is_file():
            load_dotenv(p)
            return


def clickhouse_database_name() -> str:
    return os.environ.get("CLICKHOUSE_DATABASE", DEFAULT_DATABASE)


def create_clickhouse_client() -> Any:
    import clickhouse_connect

    secure = os.environ.get("CLICKHOUSE_SECURE", "").lower() in ("1", "true", "yes")
    return clickhouse_connect.get_client(
        host=os.environ.get("CLICKHOUSE_HOST", "localhost"),
        port=int(os.environ.get("CLICKHOUSE_PORT", "8123")),
        username=os.environ.get("CLICKHOUSE_USER", "default"),
        password=os.environ.get("CLICKHOUSE_PASSWORD", ""),
        database="default",
        secure=secure,
    )


def _ddl_create_table(database: str, table: str) -> str:
    lines = []
    for col, typ in _TABLE_COLUMNS[table]:
        name_sql = "`class`" if col == "class" else col
        lines.append(f"    {name_sql} Nullable({typ})")
    cols_sql = ",\n".join(lines)
    return (
        f"CREATE TABLE IF NOT EXISTS {database}.{table} (\n"
        f"{cols_sql}\n"
        f") ENGINE = MergeTree\nORDER BY tuple()"
    )


def ensure_database(client: clickhouse_connect.driver.client.Client, database: str) -> None:
    client.command(f"CREATE DATABASE IF NOT EXISTS {database}")


def ensure_tables(client: clickhouse_connect.driver.client.Client, database: str) -> None:
    for table in _TABLE_COLUMNS:
        client.command(_ddl_create_table(database, table))


def insert_rows_async(
    client: Any,
    database: str,
    table: str,
    rows: list[dict[str, Any]],
    *,
    wait_for_async_insert: int = 1,
    batch_size: int = INSERT_BATCH_SIZE,
) -> int:
    if not rows:
        return 0
    cols = [c for c, _ in _TABLE_COLUMNS[table]]
    data = [[row.get(c) for c in cols] for row in rows]
    settings = {"async_insert": 1, "wait_for_async_insert": wait_for_async_insert}
    total = 0
    for i in range(0, len(data), batch_size):
        chunk = data[i : i + batch_size]
        client.insert(
            table,
            chunk,
            column_names=cols,
            database=database,
            settings=settings,
        )
        total += len(chunk)
    return total
