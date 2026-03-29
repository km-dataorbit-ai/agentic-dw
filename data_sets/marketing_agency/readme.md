# Marketing agency synthetic dataset

This folder contains a **simulator** that generates synthetic **raw-layer** CSV files for a marketing-agency stack: **HubSpot**, **NetSuite**, **Harvest**, and **BambooHR**. The column layout matches the raw tables described in [Marketing_Agency.md](Marketing_Agency.md).

---

## Prerequisites

- **Python 3.10+** (tested with 3.12)
- **Pydantic v2** (listed in [requirements.txt](requirements.txt))

On many Linux distributions, system Python is “externally managed,” so use a **virtual environment** in this directory.

### One-time setup

From this folder (`marketing_agency`):

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

---

## How to run the generator

Always run the script **from this directory** so the `marketing_agency_sim` package resolves correctly.

### Default run (writes to `simulated_dataset/`)

```bash
cd /path/to/marketing_agency
.venv/bin/python simulate_marketing_agency_dataset.py
```

### Custom output directory and scale

```bash
.venv/bin/python simulate_marketing_agency_dataset.py \
  --outdir ./my_run \
  --companies 200 \
  --employees 90 \
  --years 3 \
  --time-entries 120000 \
  --seed 7
```

### CLI options

| Option | Default | Meaning |
|--------|---------|---------|
| `--companies` | `120` | HubSpot companies / NetSuite customers / Harvest clients (aligned 1:1) |
| `--employees` | `65` | BambooHR employees and matching Harvest users |
| `--years` | `2` | Rough time span for dates (e.g. time entries, PTO) |
| `--time-entries` | `85000` | Number of Harvest time-entry rows |
| `--seed` | `42` | RNG seed for reproducible output |
| `--outdir` | `simulated_dataset` | Directory for CSVs and `manifest.json` |

If you do not use `.venv`, install dependencies however you prefer, then run the same command with `python3` instead of `.venv/bin/python`.

---

## Code structure

```
marketing_agency/
├── simulate_marketing_agency_dataset.py   # CLI: argparse → Config → generate_dataset()
├── requirements.txt                       # pydantic
├── Marketing_Agency.md                    # Spec / raw table definitions
└── marketing_agency_sim/
    ├── __init__.py                        # Exports simulator classes
    ├── config.py                          # Config dataclass (CLI parameters)
    ├── constants.py                       # Shared name lists, domains of random values
    ├── schemas.py                         # Pydantic models = one model per CSV row shape
    ├── utils.py                           # CSV write, JSON cells, datetime helpers, model → dict
    ├── orchestrator.py                    # Wires simulators; writes files + manifest.json
    ├── hubspot.py                         # class HubSpotSimulator
    ├── netsuite.py                        # class NetSuiteSimulator
    ├── harvest.py                         # class HarvestSimulator
    └── bamboohr.py                        # class BambooHRSimulator
```

### Flow

1. **`simulate_marketing_agency_dataset.py`** builds a `Config` and calls `generate_dataset(cfg)`.
2. **`orchestrator.py`** seeds the RNG, instantiates one simulator per product, generates **Pydantic model instances** (validated row shapes), converts them to dicts for CSV, and writes output.
3. Each **`*Simulator`** class owns the random logic for its system; **`schemas.py`** is the single place that encodes **column names and types** for each exported table.

To change behavior, edit the relevant simulator module. To tighten or extend the CSV schema, add or adjust models in `schemas.py` and update the corresponding generator methods.

---

## Generated output

Everything is written under **`--outdir`** (default: `simulated_dataset/`).

### `manifest.json`

JSON summary of the run:

- `generated_at` — wall-clock timestamp when the run finished  
- `seed` — RNG seed used  
- `parameters` — `companies`, `employees`, `years`, `time_entries`  
- `files` — map of filename → row count  

Exact row counts depend on randomness (except fixed structures like owners/tasks); **`manifest.json` is the source of truth** for your last run.

### CSV files (raw-layer naming)

| File | Source system | Role |
|------|---------------|------|
| `raw_hubspot_owners.csv` | HubSpot | Sales owners (referenced by company/contact/deal `hubspot_owner_id`) |
| `raw_hubspot_companies.csv` | HubSpot | Companies; `hs_object_id` is the canonical client key |
| `raw_hubspot_contacts.csv` | HubSpot | Contacts; `associated_company_id` → company `hs_object_id` |
| `raw_hubspot_deals.csv` | HubSpot | Deals; `associated_company_ids` is JSON array of company IDs |
| `raw_netsuite_customers.csv` | NetSuite | Customers; `entity_id` matches HubSpot `hs_object_id` |
| `raw_netsuite_invoices.csv` | NetSuite | Invoices; `entity_id` → NetSuite customer `id` |
| `raw_netsuite_payments.csv` | NetSuite | Payments; `customer_id` → customer `id`; `apply_list` JSON |
| `raw_netsuite_vendor_bills.csv` | NetSuite | Vendor spend; `line_items` JSON |
| `raw_harvest_clients.csv` | Harvest | Clients; names align with HubSpot companies |
| `raw_harvest_projects.csv` | Harvest | Projects from closed-won deals; `client_id` → Harvest client `id` |
| `raw_harvest_users.csv` | Harvest | Users aligned with BambooHR employees (email / identity) |
| `raw_harvest_tasks.csv` | Harvest | Task catalog |
| `raw_harvest_project_assignments.csv` | Harvest | User ↔ project; `project_id`, `user_id` |
| `raw_harvest_time_entries.csv` | Harvest | Time; `user_id`, `project_id`, `task_id` |
| `raw_bamboohr_employees.csv` | BambooHR | HR master; `id` (e.g. `BAM-…`) |
| `raw_bamboohr_time_off.csv` | BambooHR | PTO; `employee_id` → employee `id` |

### How IDs link across systems (conceptual)

- **HubSpot company** `hs_object_id` ↔ **NetSuite** `netsuite_customers.entity_id` ↔ **Harvest** client (implicit via generation order and naming).
- **Closed-won HubSpot deals** drive **Harvest projects** and related **NetSuite invoices** (same client lineage).
- **BambooHR employees** drive **Harvest users** (paired by generation order and shared email).

For full SQL-oriented column definitions, see [Marketing_Agency.md](Marketing_Agency.md) § raw table schema.

---

## Regenerating

Re-running the same command overwrites files in `--outdir`. Use a different `--outdir` or `--seed` if you want to keep multiple variants side by side.

```bash
.venv/bin/python simulate_marketing_agency_dataset.py --outdir simulated_dataset --seed 42
```
