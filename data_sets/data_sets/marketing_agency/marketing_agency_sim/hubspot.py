from __future__ import annotations

import random
import uuid
from datetime import datetime, timedelta

from .constants import FIRST_NAMES, INDUSTRIES, LAST_NAMES, SERVICE_LINES
from .schemas import HubSpotCompanyRow, HubSpotContactRow, HubSpotDealRow, HubSpotOwnerRow
from .utils import iso_date, iso_ts, json_cell, rand_dt


class HubSpotSimulator:
    def __init__(self, now: datetime, start: datetime, years: int) -> None:
        self.now = now
        self.start = start
        self.years = years

    def generate_owners(self) -> list[HubSpotOwnerRow]:
        rows = []
        for i in range(1, 11):
            first, last = random.choice(FIRST_NAMES), random.choice(LAST_NAMES)
            rows.append(
                HubSpotOwnerRow(
                    _dataorbit_sync_id=str(uuid.uuid4()),
                    _dataorbit_synced_at=iso_ts(self.now),
                    owner_id=f"HS-OWN-{i:04d}",
                    email=f"{first.lower()}.{last.lower()}@agency.example.com",
                    first_name=first,
                    last_name=last,
                    user_id=f"USR-{i:05d}",
                )
            )
        return rows

    def generate_companies(self, companies: int) -> list[HubSpotCompanyRow]:
        rows = []
        for i in range(1, companies + 1):
            domain = f"client{i:03d}.example.com"
            created = rand_dt(self.now - timedelta(days=self.years * 365), self.now - timedelta(days=30))
            modified = rand_dt(created, self.now)
            contract_type = random.choice(["Retainer", "Project", "Hybrid"])
            retainer_value = round(random.uniform(2500, 25000), 2)
            renewal = created.date() + timedelta(days=random.choice([180, 365, 730]))
            rows.append(
                HubSpotCompanyRow(
                    _dataorbit_sync_id=str(uuid.uuid4()),
                    _dataorbit_synced_at=iso_ts(self.now),
                    _dataorbit_is_deleted=False,
                    hs_object_id=f"HS-COMP-{i:06d}",
                    name=f"{random.choice(['Blue', 'North', 'Bright', 'Prime', 'Nova'])} {random.choice(['Labs', 'Retail', 'Health', 'Capital', 'Digital'])} {i}",
                    domain=domain,
                    industry=random.choice(INDUSTRIES),
                    hubspot_owner_id=f"HS-OWN-{random.randint(1, 10):04d}",
                    createdate=iso_ts(created),
                    hs_lastmodifieddate=iso_ts(modified),
                    properties=json_cell(
                        {
                            "service_line_tags": random.sample(SERVICE_LINES, k=random.randint(1, 3)),
                            "contract_type": contract_type,
                            "retainer_value": retainer_value,
                            "renewal_date": iso_date(renewal),
                        }
                    ),
                )
            )
        return rows

    def generate_contacts_and_deals(
        self, companies: list[HubSpotCompanyRow]
    ) -> tuple[list[HubSpotContactRow], list[HubSpotDealRow]]:
        contacts = []
        deals = []
        deal_counter = 1
        for c in companies:
            for k in range(random.randint(2, 6)):
                first, last = random.choice(FIRST_NAMES), random.choice(LAST_NAMES)
                contacts.append(
                    HubSpotContactRow(
                        _dataorbit_sync_id=str(uuid.uuid4()),
                        _dataorbit_synced_at=iso_ts(self.now),
                        _dataorbit_is_deleted=False,
                        hs_object_id=f"HS-CON-{len(contacts)+1:07d}",
                        email=f"{first.lower()}.{last.lower()}.{k}@{c.domain}",
                        firstname=first,
                        lastname=last,
                        company=c.name,
                        jobtitle=random.choice(["CMO", "Marketing Manager", "VP Growth", "Founder"]),
                        lifecyclestage=random.choice(["lead", "marketingqualifiedlead", "opportunity", "customer"]),
                        associated_company_id=c.hs_object_id,
                        hubspot_owner_id=c.hubspot_owner_id,
                        properties=json_cell({"source": random.choice(["Inbound", "Referral", "Outbound"])}),
                    )
                )
            for _ in range(random.randint(1, 4)):
                created = rand_dt(self.start, self.now - timedelta(days=10))
                close_d = (created + timedelta(days=random.randint(15, 120))).date()
                stage = random.choice(["appointmentscheduled", "qualifiedtobuy", "closedwon", "closedlost"])
                prob = {"appointmentscheduled": 25, "qualifiedtobuy": 55, "closedwon": 100, "closedlost": 0}[stage]
                deals.append(
                    HubSpotDealRow(
                        _dataorbit_sync_id=str(uuid.uuid4()),
                        _dataorbit_synced_at=iso_ts(self.now),
                        _dataorbit_is_deleted=False,
                        hs_object_id=f"HS-DEA-{deal_counter:07d}",
                        dealname=f"{c.name} - {random.choice(['Growth', 'Retainer', 'Rebuild', 'Campaign'])}",
                        amount=round(random.uniform(5000, 120000), 2),
                        dealstage=stage,
                        pipeline="default",
                        closedate=iso_date(close_d),
                        createdate=iso_ts(created),
                        hs_deal_stage_probability=float(prob),
                        hubspot_owner_id=c.hubspot_owner_id,
                        associated_company_ids=json_cell([c.hs_object_id]),
                        properties=json_cell({"service_line": random.choice(SERVICE_LINES)}),
                    )
                )
                deal_counter += 1
        return contacts, deals

