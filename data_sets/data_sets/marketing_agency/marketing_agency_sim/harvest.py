from __future__ import annotations

import json
import random
import uuid
from datetime import datetime, timedelta

from .constants import FIRST_NAMES, LAST_NAMES, TASKS
from .schemas import (
    BambooEmployeeRow,
    HarvestClientRow,
    HarvestProjectAssignmentRow,
    HarvestProjectRow,
    HarvestTaskRow,
    HarvestTimeEntryRow,
    HarvestUserRow,
)
from .utils import iso_date, iso_ts, json_cell, rand_dt


class HarvestSimulator:
    def __init__(self, now: datetime, start: datetime, years: int) -> None:
        self.now = now
        self.start = start
        self.years = years

    def generate_clients(self, hubspot_companies: list) -> tuple[list[HarvestClientRow], dict[str, int]]:
        clients = []
        hs_to_hv_client: dict[str, int] = {}
        for i, c in enumerate(hubspot_companies, start=1):
            hid = 1_000_000 + i
            hs_to_hv_client[c.hs_object_id] = hid
            clients.append(
                HarvestClientRow(
                    _dataorbit_sync_id=str(uuid.uuid4()),
                    _dataorbit_synced_at=iso_ts(self.now),
                    id=hid,
                    name=c.name,
                    is_active=True,
                    address=f"{random.randint(100,999)} Market St",
                    currency="USD",
                )
            )
        return clients, hs_to_hv_client

    def generate_users_from_employees(self, employees: list[BambooEmployeeRow]) -> list[HarvestUserRow]:
        rows = []
        for i, emp in enumerate(employees, start=1):
            hourly_cost = round(emp.pay_rate / 2080, 2) if emp.pay_type == "Salary" else emp.pay_rate
            first = emp.first_name or random.choice(FIRST_NAMES)
            last = emp.last_name or random.choice(LAST_NAMES)
            rows.append(
                HarvestUserRow(
                    _dataorbit_sync_id=str(uuid.uuid4()),
                    _dataorbit_synced_at=iso_ts(self.now),
                    id=2_000_000 + i,
                    first_name=first,
                    last_name=last,
                    email=emp.work_email,
                    is_active=emp.status == "Active",
                    is_contractor=random.random() < 0.18,
                    roles=json_cell([random.choice(["Manager", "Contributor", "Executive"])]),
                    cost_rate=hourly_cost,
                    default_hourly_rate=round(hourly_cost * random.uniform(2.2, 3.5), 2),
                    weekly_capacity=random.choice([126000, 144000, 162000]),
                    created_at=iso_ts(rand_dt(self.start, self.now - timedelta(days=30))),
                    updated_at=iso_ts(rand_dt(self.now - timedelta(days=60), self.now)),
                )
            )
        return rows

    def generate_tasks(self) -> list[HarvestTaskRow]:
        return [
            HarvestTaskRow(
                _dataorbit_sync_id=str(uuid.uuid4()),
                _dataorbit_synced_at=iso_ts(self.now),
                id=3_000_000 + i,
                name=name,
                is_default=i == 0,
                default_hourly_rate=round(random.uniform(115, 220), 2),
                is_active=True,
            )
            for i, name in enumerate(TASKS)
        ]

    def generate_projects_and_assignments(
        self,
        hubspot_deals: list,
        hs_to_hv_client: dict[str, int],
        harvest_users: list[HarvestUserRow],
    ) -> tuple[list[HarvestProjectRow], list[HarvestProjectAssignmentRow]]:
        projects = []
        assignments = []
        won_deals = [d for d in hubspot_deals if d.dealstage == "closedwon"]
        for i, d in enumerate(won_deals, start=1):
            cid = json.loads(d.associated_company_ids)[0]
            project_id = 4_000_000 + i
            budget = round(float(d.amount) * random.uniform(0.6, 1.1), 2)
            projects.append(
                HarvestProjectRow(
                    _dataorbit_sync_id=str(uuid.uuid4()),
                    _dataorbit_synced_at=iso_ts(self.now),
                    id=project_id,
                    client_id=hs_to_hv_client[cid],
                    name=f"{d.dealname} Project",
                    code=f"PRJ-{i:05d}",
                    is_active=random.random() > 0.2,
                    is_billable=True,
                    budget=budget,
                    budget_by=random.choice(["project", "project_cost", "task", "person"]),
                    fee=round(float(d.amount) * random.uniform(0.8, 1.2), 2),
                    hourly_rate=round(random.uniform(120, 250), 2),
                    cost_budget=round(budget * random.uniform(0.45, 0.72), 2),
                    starts_on=d.closedate,
                    ends_on=iso_date((datetime.fromisoformat(d.closedate) + timedelta(days=random.randint(60, 365))).date()),
                    over_budget_notification_percentage=float(random.choice([80, 90, 100])),
                    created_at=d.createdate,
                    updated_at=iso_ts(rand_dt(self.now - timedelta(days=120), self.now)),
                )
            )
            assigned_users = random.sample(harvest_users, k=min(len(harvest_users), random.randint(2, 8)))
            for u in assigned_users:
                assignments.append(
                    HarvestProjectAssignmentRow(
                        _dataorbit_sync_id=str(uuid.uuid4()),
                        _dataorbit_synced_at=iso_ts(self.now),
                        id=5_000_000 + len(assignments) + 1,
                        project_id=project_id,
                        user_id=u.id,
                        is_active=True,
                        hourly_rate=round(float(u.default_hourly_rate) * random.uniform(0.95, 1.15), 2),
                        budget=round(random.uniform(20, 300), 2),
                    )
                )
        return projects, assignments

    def generate_time_entries(
        self,
        time_entries: int,
        harvest_users: list[HarvestUserRow],
        harvest_projects: list[HarvestProjectRow],
        harvest_tasks: list[HarvestTaskRow],
    ) -> list[HarvestTimeEntryRow]:
        rows = []
        for i in range(1, time_entries + 1):
            u = random.choice(harvest_users)
            p = random.choice(harvest_projects)
            t = random.choice(harvest_tasks)
            spent = (self.start + timedelta(days=random.randint(0, self.years * 365 - 1))).date()
            hours = round(random.choice([0.5, 1.0, 1.5, 2.0, 3.0, 4.0, 6.0, 8.0]), 2)
            billable = random.random() < 0.9
            rows.append(
                HarvestTimeEntryRow(
                    _dataorbit_sync_id=str(uuid.uuid4()),
                    _dataorbit_synced_at=iso_ts(self.now),
                    id=6_000_000 + i,
                    user_id=u.id,
                    project_id=p.id,
                    task_id=t.id,
                    spent_date=iso_date(spent),
                    hours=hours,
                    billable=billable,
                    billable_rate=p.hourly_rate if billable else 0.0,
                    cost_rate=u.cost_rate,
                    notes=random.choice(["Weekly work", "Client request", "Optimization", "Reporting", "Implementation"]),
                    is_locked=random.random() < 0.1,
                    created_at=iso_ts(rand_dt(self.start, self.now)),
                    updated_at=iso_ts(rand_dt(self.start, self.now)),
                )
            )
        return rows

