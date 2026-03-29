from __future__ import annotations

import random
import uuid
from datetime import datetime, timedelta

from .constants import DEPARTMENTS, FIRST_NAMES, LAST_NAMES, PTO_TYPES
from .schemas import BambooEmployeeRow, BambooTimeOffRow
from .utils import iso_date, iso_ts, json_cell


class BambooHRSimulator:
    def __init__(self, now: datetime, start: datetime, years: int) -> None:
        self.now = now
        self.start = start
        self.years = years

    def generate_employees(self, employees: int) -> list[BambooEmployeeRow]:
        rows = []
        total_days = max(1, (self.now - self.start).days)
        for i in range(1, employees + 1):
            first, last = random.choice(FIRST_NAMES), random.choice(LAST_NAMES)
            pay_type = random.choice(["Salary", "Hourly"])
            pay_per = "Year" if pay_type == "Salary" else "Hour"
            pay_rate = round(random.uniform(52000, 140000), 2) if pay_type == "Salary" else round(random.uniform(25, 95), 2)
            is_active = random.random() > 0.08
            rows.append(
                BambooEmployeeRow(
                    _dataorbit_sync_id=str(uuid.uuid4()),
                    _dataorbit_synced_at=iso_ts(self.now),
                    id=f"BAM-{i:05d}",
                    display_name=f"{first} {last}",
                    first_name=first,
                    last_name=last,
                    work_email=f"{first.lower()}.{last.lower()}.{i}@agency.example.com",
                    department=random.choice(DEPARTMENTS),
                    division=random.choice(["Demand Gen", "Creative", "Ops"]),
                    job_title=random.choice(["Specialist", "Manager", "Director", "Analyst"]),
                    supervisor_id=f"BAM-{max(1, i-1):05d}",
                    location=random.choice(["Remote", "New York", "Austin", "London"]),
                    hire_date=iso_date((self.start + timedelta(days=random.randint(0, total_days - 1))).date()),
                    termination_date="" if is_active else iso_date((self.now - timedelta(days=random.randint(1, 120))).date()),
                    status="Active" if is_active else "Inactive",
                    pay_rate=pay_rate,
                    pay_type=pay_type,
                    pay_per=pay_per,
                    employee_number=f"EMP{i:05d}",
                    custom_fields=json_cell({"utilization_target": random.choice([0.7, 0.75, 0.8, 0.85])}),
                )
            )
        return rows

    def generate_time_off(self, employees: list[BambooEmployeeRow]) -> list[BambooTimeOffRow]:
        rows = []
        for i in range(1, max(20, len(employees) * 3)):
            emp = random.choice(employees)
            start_d = (self.start + timedelta(days=random.randint(0, self.years * 365 - 20))).date()
            duration = random.randint(1, 10)
            end_d = start_d + timedelta(days=duration - 1)
            unit = random.choice(["days", "hours"])
            amount = duration if unit == "days" else duration * 8
            rows.append(
                BambooTimeOffRow(
                    _dataorbit_sync_id=str(uuid.uuid4()),
                    _dataorbit_synced_at=iso_ts(self.now),
                    id=f"PTO-{i:06d}",
                    employee_id=emp.id,
                    time_off_type=random.choice(PTO_TYPES),
                    start_date=iso_date(start_d),
                    end_date=iso_date(end_d),
                    status=random.choice(["approved", "pending", "denied"]),
                    amount=float(amount),
                    unit=unit,
                )
            )
        return rows

