from __future__ import annotations

import random
import uuid
from datetime import datetime, timedelta

from .constants import DEPARTMENTS, INVOICE_STATUS, SERVICE_LINES
from .schemas import (
    NetSuiteCustomerRow,
    NetSuiteInvoiceRow,
    NetSuitePaymentRow,
    NetSuiteVendorBillRow,
)
from .utils import iso_date, iso_ts, json_cell, rand_dt


class NetSuiteSimulator:
    def __init__(self, now: datetime, start: datetime, years: int) -> None:
        self.now = now
        self.start = start
        self.years = years

    def generate_customers(self, hubspot_companies: list) -> tuple[list[NetSuiteCustomerRow], dict[str, str]]:
        rows = []
        company_to_ns: dict[str, str] = {}
        for i, c in enumerate(hubspot_companies, start=1):
            ns_id = f"NS-CUST-{i:06d}"
            company_to_ns[c.hs_object_id] = ns_id
            rows.append(
                NetSuiteCustomerRow(
                    _dataorbit_sync_id=str(uuid.uuid4()),
                    _dataorbit_synced_at=iso_ts(self.now),
                    id=ns_id,
                    company_name=c.name,
                    email=f"finance@{c.domain}",
                    entity_id=c.hs_object_id,
                    subsidiary=random.choice(["US", "EMEA", "APAC"]),
                    terms=random.choice(["Net 15", "Net 30", "Net 45", "Net 60"]),
                    balance=0.0,
                    category=random.choice(["A", "B", "C"]),
                    last_modified_date=c.hs_lastmodifieddate,
                    custom_fields=json_cell({"segment": random.choice(["SMB", "Mid-Market", "Enterprise"])}),
                )
            )
        return rows, company_to_ns

    def generate_invoices_and_payments(
        self,
        harvest_projects: list,
        hs_to_hv_client: dict[str, int],
        company_to_ns: dict[str, str],
    ) -> tuple[list[NetSuiteInvoiceRow], list[NetSuitePaymentRow]]:
        invoices = []
        payments = []
        hv_to_hs = {v: k for k, v in hs_to_hv_client.items()}
        for i, p in enumerate(harvest_projects, start=1):
            hs_company_id = hv_to_hs[p.client_id]
            cust_id = company_to_ns[hs_company_id]
            inv_total = round(float(p.fee) * random.uniform(0.4, 1.2), 2)
            status = random.choice(INVOICE_STATUS)
            remaining = 0.0 if status == "Paid In Full" else round(inv_total * random.uniform(0.1, 0.8), 2)
            tran_d = (datetime.fromisoformat(p.starts_on) + timedelta(days=random.randint(0, 45))).date()
            due_d = tran_d + timedelta(days=random.choice([15, 30, 45, 60]))
            invoice_id = f"NS-INV-{i:07d}"
            invoices.append(
                NetSuiteInvoiceRow(
                    _dataorbit_sync_id=str(uuid.uuid4()),
                    _dataorbit_synced_at=iso_ts(self.now),
                    id=invoice_id,
                    entity_id=cust_id,
                    tran_date=iso_date(tran_d),
                    due_date=iso_date(due_d),
                    total=inv_total,
                    amount_remaining=remaining,
                    status=status,
                    line_items=json_cell(
                        [
                            {
                                "item": "Agency Services",
                                "description": p.name,
                                "quantity": round(inv_total / max(1.0, float(p.hourly_rate)), 2),
                                "rate": p.hourly_rate,
                                "amount": inv_total,
                            }
                        ]
                    ),
                    last_modified_date=iso_ts(rand_dt(self.start, self.now)),
                )
            )
            if status != "Open":
                paid_amt = round(inv_total - remaining, 2)
                payments.append(
                    NetSuitePaymentRow(
                        _dataorbit_sync_id=str(uuid.uuid4()),
                        _dataorbit_synced_at=iso_ts(self.now),
                        id=f"NS-PAY-{len(payments)+1:07d}",
                        customer_id=cust_id,
                        total=paid_amt,
                        tran_date=iso_date(tran_d + timedelta(days=random.randint(1, 40))),
                        apply_list=json_cell([{"invoice_id": invoice_id, "amount_applied": paid_amt}]),
                        last_modified_date=iso_ts(rand_dt(self.start, self.now)),
                    )
                )
        return invoices, payments

    def generate_vendor_bills(self) -> list[NetSuiteVendorBillRow]:
        rows = []
        months = max(3, self.years * 12)
        for i in range(1, months * 4 + 1):
            dt = (self.now - timedelta(days=random.randint(1, self.years * 365))).date()
            total = round(random.uniform(150, 6000), 2)
            rows.append(
                NetSuiteVendorBillRow(
                    _dataorbit_sync_id=str(uuid.uuid4()),
                    _dataorbit_synced_at=iso_ts(self.now),
                    id=f"NS-VB-{i:07d}",
                    entity_id=f"VEND-{random.randint(1,35):04d}",
                    tran_date=iso_date(dt),
                    total=total,
                    line_items=json_cell([{"description": random.choice(["Ad Spend", "Software", "Contractor"]), "amount": total}]),
                    class_name=random.choice(SERVICE_LINES),
                    department=random.choice(DEPARTMENTS),
                    last_modified_date=iso_ts(rand_dt(self.start, self.now)),
                )
            )
        return rows

