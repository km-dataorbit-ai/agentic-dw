# DataOrbit AI — Marketing Agency: Technical Implementation Spec

## Bottom-Up Architecture Guide: Source APIs → Analytics Outputs

March 2026

Table of Contents

# DataOrbit AI — Marketing Agency: Technical Implementation Spec

**Bottom-Up Architecture Guide: Source APIs → Analytics Outputs**

*Internal Engineering Reference — v1.0*

## Document Purpose

This document traces the complete data path for the marketing agency vertical template, from source system APIs through every layer of DataOrbit’s six-layer architecture to final analytics outputs. It is the engineering counterpart to the Marketing Agency Vertical Playbook (business-first) and implements the architecture described in the DataOrbit AI Product Blueprint.

**System combination:** HubSpot (CRM) + NetSuite (ERP/Finance) + Harvest (Time Tracking) + BambooHR (HRIS)

**Reading order:** Bottom-up — start at Layer 1 (source APIs and raw tables), work through each layer in build order.

## Layer 1: Managed Warehouse + Data Connectors

### 1.1 Source System API Inventory

Each connector module authenticates via OAuth, extracts data through the system’s REST API, handles pagination and rate limiting, and writes to raw tables preserving the source schema exactly.

#### *HubSpot (CRM)*

| API Endpoint | Objects Extracted | Key Fields | Sync Strategy |
| :---: | :---: | :---: | :---: |
| /crm/v3/objects/companies | Companies | id, name, domain, industry, hs\_object\_id, hubspot\_owner\_id, createdate, hs\_lastmodifieddate, custom properties | Incremental via hs\_lastmodifieddate |
| /crm/v3/objects/contacts | Contacts | id, email, firstname, lastname, company, jobtitle, lifecyclestage, hubspot\_owner\_id | Incremental via lastmodifieddate |
| /crm/v3/objects/deals | Deals / Opportunities | id, dealname, amount, dealstage, pipeline, closedate, hs\_deal\_stage\_probability, hubspot\_owner\_id, associated\_company\_ids | Incremental via hs\_lastmodifieddate |
| /crm/v3/objects/deals/associations | Deal-to-Company links | deal\_id, company\_id, association type | Full refresh (lightweight) |
| /crm/v3/owners | Owners / Users | id, email, firstName, lastName, userId | Full refresh |
| /crm/v3/objects/companies/properties | Custom property definitions | Property name, type, label, group | On-demand (schema detection) |

**Rate limits:** 100 requests/10 seconds (OAuth apps). Burst capacity: 150. **Pagination:** Cursor-based (after parameter), 100 records per page. **Key custom properties to detect:** Service line tags, contract type, retainer value, renewal date — these vary per customer and must be discovered during onboarding.

#### *NetSuite (ERP / Finance)*

| API Endpoint (SuiteTalk REST) | Objects Extracted | Key Fields | Sync Strategy |
| :---: | :---: | :---: | :---: |
| /record/v1/customer | Customers / Accounts | id, companyName, email, entityId, subsidiary, terms, balance, category | Incremental via lastModifiedDate |
| /record/v1/invoice | Invoices | id, entity (customer ref), tranDate, dueDate, total, amountRemaining, status, lineItems\[\] | Incremental via lastModifiedDate |
| /record/v1/customerPayment | Payments | id, customer, total, tranDate, applyList\[\] (applied-to invoices) | Incremental via lastModifiedDate |
| /record/v1/journalEntry | Revenue recognition entries | id, tranDate, lineItems\[\] (account, amount, entity) | Incremental via lastModifiedDate |
| /record/v1/vendorBill | Expenses / vendor invoices | id, entity (vendor), tranDate, total, lineItems\[\], class, department | Incremental via lastModifiedDate |
| /record/v1/employee | Employees (if used for billing rates) | id, entityId, email, firstName, lastName, department, billingClass | Full refresh |
| /record/v1/timeEntry | Time entries (if used in NetSuite) | id, employee, customer, hours, date, isBillable | Incremental |

**Authentication:** Token-Based Authentication (TBA) — OAuth 1.0a variant. Requires account-level setup. **Rate limits:** 10 concurrent requests; throttled at ~100 requests/minute for RESTlet calls. **Pagination:** Offset-based (limit + offset), max 1000 per page. **Key complexity:** NetSuite’s data model is highly customizable. Subsidiaries, classes, and departments are customer-configured hierarchies. The connector must detect which ones are used and how they map to service lines, projects, and cost centers.

#### *Harvest (Time Tracking)*

| API Endpoint | Objects Extracted | Key Fields | Sync Strategy |
| :---: | :---: | :---: | :---: |
| /v2/time\_entries | Time entries | id, user.id, project.id, task.id, spent\_date, hours, billable, billable\_rate, cost\_rate, notes, is\_locked, created\_at, updated\_at | Incremental via updated\_since parameter |
| /v2/projects | Projects | id, client.id, name, code, is\_active, is\_billable, budget, budget\_by (hours/amount), over\_budget\_notification\_percentage, fee, hourly\_rate, cost\_budget | Full refresh (low volume) |
| /v2/clients | Clients | id, name, is\_active, address, currency | Full refresh (low volume) |
| /v2/users | Users (team members) | id, first\_name, last\_name, email, is\_active, is\_contractor, roles\[\], cost\_rate, default\_hourly\_rate, weekly\_capacity | Full refresh |
| /v2/tasks | Task types | id, name, is\_default, default\_hourly\_rate, is\_active | Full refresh |
| /v2/project\_assignments | User-to-project assignments | id, project.id, user.id, is\_active, hourly\_rate, budget | Full refresh |
| /v2/invoices | Invoices (if Harvest billing used) | id, client\_id, amount, due\_amount, sent\_at, paid\_at, state | Incremental |

**Rate limits:** 100 requests/15 seconds per access token. **Pagination:** Cursor-based (page + per\_page), max 2000 per page for time entries. **Key note:** Harvest is the linchpin for the agency use case. Time entries are the highest-volume table (~85K records over 2 years) and the bridge between delivery cost and revenue. The billable\_rate and cost\_rate on each time entry are critical — they determine effective bill rate and project margin.

#### *BambooHR (HRIS)*

| API Endpoint | Objects Extracted | Key Fields | Sync Strategy |
| :---: | :---: | :---: | :---: |
| /v1/employees/directory | Employee directory | id, displayName, firstName, lastName, workEmail, department, division, jobTitle, supervisor, location, hireDate, status | Full refresh |
| /v1/employees/{id} | Employee detail | All standard + custom fields: payRate, payType, payPer, employeeNumber, terminationDate | Incremental via lastChanged |
| /v1/time\_off/requests | PTO / time off | id, employeeId, type, start, end, status, amount (days/hours) | Incremental via date range |
| /v1/employees/changed | Change log | employeeId, changedFields, date | Used for incremental detection |

**Authentication:** API key (per-company) — simpler than OAuth but requires manual setup during onboarding. **Rate limits:** Undocumented officially; generally ~100 requests/minute. **Key complexity:** Compensation data (payRate, payType) is essential for computing cost-per-hour but is sensitive. Must be handled carefully in the data quality layer (access-controlled, never surfaced raw to non-finance users). payType can be “Salary” or “Hourly” — both must be normalized to an hourly cost rate.

### 1.2 Raw Table Schema

Raw tables preserve source structure exactly. No transformation, no normalization, no filtering. This is the audit trail.

```sql
-- Schema: raw.*

-- HubSpot
CREATE TABLE raw.hubspot_companies (
    _dataorbit_sync_id      UUID,
    _dataorbit_synced_at    TIMESTAMP,
    _dataorbit_is_deleted   BOOLEAN DEFAULT FALSE,
    hs_object_id            VARCHAR(50),
    name                    TEXT,
    domain                  TEXT,
    industry                TEXT,
    hubspot_owner_id        VARCHAR(50),
    createdate              TIMESTAMP,
    hs_lastmodifieddate     TIMESTAMP,
    -- All other standard + custom properties stored as JSONB
    properties              JSONB
);

CREATE TABLE raw.hubspot_contacts (
    _dataorbit_sync_id      UUID,
    _dataorbit_synced_at    TIMESTAMP,
    _dataorbit_is_deleted   BOOLEAN DEFAULT FALSE,
    hs_object_id            VARCHAR(50),
    email                   TEXT,
    firstname               TEXT,
    lastname                TEXT,
    company                 TEXT,
    jobtitle                TEXT,
    lifecyclestage          TEXT,
    associated_company_id   VARCHAR(50),
    hubspot_owner_id        VARCHAR(50),
    properties              JSONB
);

CREATE TABLE raw.hubspot_deals (
    _dataorbit_sync_id      UUID,
    _dataorbit_synced_at    TIMESTAMP,
    _dataorbit_is_deleted   BOOLEAN DEFAULT FALSE,
    hs_object_id            VARCHAR(50),
    dealname                TEXT,
    amount                  NUMERIC(15,2),
    dealstage               TEXT,
    pipeline                TEXT,
    closedate               DATE,
    createdate              TIMESTAMP,
    hs_deal_stage_probability NUMERIC(5,2),
    hubspot_owner_id        VARCHAR(50),
    associated_company_ids  TEXT[],
    properties              JSONB
);

CREATE TABLE raw.hubspot_owners (
    _dataorbit_sync_id      UUID,
    _dataorbit_synced_at    TIMESTAMP,
    owner_id                VARCHAR(50),
    email                   TEXT,
    first_name              TEXT,
    last_name               TEXT,
    user_id                 VARCHAR(50)
);

-- NetSuite
CREATE TABLE raw.netsuite_customers (
    _dataorbit_sync_id      UUID,
    _dataorbit_synced_at    TIMESTAMP,
    id                      VARCHAR(50),
    company_name            TEXT,
    email                   TEXT,
    entity_id               TEXT,
    subsidiary              TEXT,
    terms                   TEXT,       -- e.g., "Net 30", "Net 60"
    balance                 NUMERIC(15,2),
    category                TEXT,
    last_modified_date      TIMESTAMP,
    custom_fields           JSONB
);

CREATE TABLE raw.netsuite_invoices (
    _dataorbit_sync_id      UUID,
    _dataorbit_synced_at    TIMESTAMP,
    id                      VARCHAR(50),
    entity_id               VARCHAR(50),  -- FK to customer
    tran_date               DATE,
    due_date                DATE,
    total                   NUMERIC(15,2),
    amount_remaining        NUMERIC(15,2),
    status                  TEXT,          -- "Open", "Paid In Full", "Partially Paid"
    line_items              JSONB,         -- [{item, description, quantity, rate, amount}]
    last_modified_date      TIMESTAMP
);

CREATE TABLE raw.netsuite_payments (
    _dataorbit_sync_id      UUID,
    _dataorbit_synced_at    TIMESTAMP,
    id                      VARCHAR(50),
    customer_id             VARCHAR(50),
    total                   NUMERIC(15,2),
    tran_date               DATE,
    apply_list              JSONB,         -- [{invoice_id, amount_applied}]
    last_modified_date      TIMESTAMP
);

CREATE TABLE raw.netsuite_vendor_bills (
    _dataorbit_sync_id      UUID,
    _dataorbit_synced_at    TIMESTAMP,
    id                      VARCHAR(50),
    entity_id               VARCHAR(50),  -- FK to vendor
    tran_date               DATE,
    total                   NUMERIC(15,2),
    line_items              JSONB,
    class                   TEXT,          -- Maps to service line or project
    department              TEXT,
    last_modified_date      TIMESTAMP
);

-- Harvest
CREATE TABLE raw.harvest_time_entries (
    _dataorbit_sync_id      UUID,
    _dataorbit_synced_at    TIMESTAMP,
    id                      BIGINT,
    user_id                 BIGINT,
    project_id              BIGINT,
    task_id                 BIGINT,
    spent_date              DATE,
    hours                   NUMERIC(6,2),
    billable                BOOLEAN,
    billable_rate           NUMERIC(10,2),
    cost_rate               NUMERIC(10,2),
    notes                   TEXT,
    is_locked               BOOLEAN,
    created_at              TIMESTAMP,
    updated_at              TIMESTAMP
);

CREATE TABLE raw.harvest_projects (
    _dataorbit_sync_id      UUID,
    _dataorbit_synced_at    TIMESTAMP,
    id                      BIGINT,
    client_id               BIGINT,
    name                    TEXT,
    code                    TEXT,
    is_active               BOOLEAN,
    is_billable             BOOLEAN,
    budget                  NUMERIC(10,2),
    budget_by               TEXT,          -- "project", "project_cost", "task", "person"
    fee                     NUMERIC(15,2),
    hourly_rate             NUMERIC(10,2),
    cost_budget             NUMERIC(15,2),
    starts_on               DATE,
    ends_on                 DATE,
    over_budget_notification_percentage NUMERIC(5,2),
    created_at              TIMESTAMP,
    updated_at              TIMESTAMP
);

CREATE TABLE raw.harvest_clients (
    _dataorbit_sync_id      UUID,
    _dataorbit_synced_at    TIMESTAMP,
    id                      BIGINT,
    name                    TEXT,
    is_active               BOOLEAN,
    address                 TEXT,
    currency                TEXT
);

CREATE TABLE raw.harvest_users (
    _dataorbit_sync_id      UUID,
    _dataorbit_synced_at    TIMESTAMP,
    id                      BIGINT,
    first_name              TEXT,
    last_name               TEXT,
    email                   TEXT,
    is_active               BOOLEAN,
    is_contractor           BOOLEAN,
    roles                   TEXT[],
    cost_rate               NUMERIC(10,2),
    default_hourly_rate     NUMERIC(10,2),
    weekly_capacity         INTEGER,       -- seconds per week (default 144000 = 40hrs)
    created_at              TIMESTAMP,
    updated_at              TIMESTAMP
);

CREATE TABLE raw.harvest_tasks (
    _dataorbit_sync_id      UUID,
    _dataorbit_synced_at    TIMESTAMP,
    id                      BIGINT,
    name                    TEXT,
    is_default              BOOLEAN,
    default_hourly_rate     NUMERIC(10,2),
    is_active               BOOLEAN
);

CREATE TABLE raw.harvest_project_assignments (
    _dataorbit_sync_id      UUID,
    _dataorbit_synced_at    TIMESTAMP,
    id                      BIGINT,
    project_id              BIGINT,
    user_id                 BIGINT,
    is_active               BOOLEAN,
    hourly_rate             NUMERIC(10,2),
    budget                  NUMERIC(10,2)
);

-- BambooHR
CREATE TABLE raw.bamboohr_employees (
    _dataorbit_sync_id      UUID,
    _dataorbit_synced_at    TIMESTAMP,
    id                      VARCHAR(50),
    display_name            TEXT,
    first_name              TEXT,
    last_name               TEXT,
    work_email              TEXT,
    department              TEXT,
    division                TEXT,
    job_title               TEXT,
    supervisor_id           VARCHAR(50),
    location                TEXT,
    hire_date               DATE,
    termination_date        DATE,
    status                  TEXT,          -- "Active", "Inactive"
    pay_rate                NUMERIC(12,2),
    pay_type                TEXT,          -- "Salary", "Hourly"
    pay_per                 TEXT,          -- "Year", "Hour", "Month"
    employee_number         TEXT,
    custom_fields           JSONB
);

CREATE TABLE raw.bamboohr_time_off (
    _dataorbit_sync_id      UUID,
    _dataorbit_synced_at    TIMESTAMP,
    id                      VARCHAR(50),
    employee_id             VARCHAR(50),
    time_off_type           TEXT,
    start_date              DATE,
    end_date                DATE,
    status                  TEXT,          -- "approved", "pending", "denied"
    amount                  NUMERIC(6,2), -- days or hours
    unit                    TEXT           -- "days", "hours"
);
