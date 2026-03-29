from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

# Leading "_" on field names makes Pydantic v2 treat them as private — they never appear in
# model_dump() and ClickHouse gets NULLs. Use public Python names + Field(alias=...) instead.

_ROW = ConfigDict(populate_by_name=True)


class HubSpotCompanyRow(BaseModel):
    model_config = _ROW

    dataorbit_sync_id: str = Field(alias="_dataorbit_sync_id")
    dataorbit_synced_at: str = Field(alias="_dataorbit_synced_at")
    dataorbit_is_deleted: bool = Field(alias="_dataorbit_is_deleted")
    hs_object_id: str
    name: str
    domain: str
    industry: str
    hubspot_owner_id: str
    createdate: str
    hs_lastmodifieddate: str
    properties: str


class HubSpotContactRow(BaseModel):
    model_config = _ROW

    dataorbit_sync_id: str = Field(alias="_dataorbit_sync_id")
    dataorbit_synced_at: str = Field(alias="_dataorbit_synced_at")
    dataorbit_is_deleted: bool = Field(alias="_dataorbit_is_deleted")
    hs_object_id: str
    email: str
    firstname: str
    lastname: str
    company: str
    jobtitle: str
    lifecyclestage: str
    associated_company_id: str
    hubspot_owner_id: str
    properties: str


class HubSpotDealRow(BaseModel):
    model_config = _ROW

    dataorbit_sync_id: str = Field(alias="_dataorbit_sync_id")
    dataorbit_synced_at: str = Field(alias="_dataorbit_synced_at")
    dataorbit_is_deleted: bool = Field(alias="_dataorbit_is_deleted")
    hs_object_id: str
    dealname: str
    amount: float
    dealstage: str
    pipeline: str
    closedate: str
    createdate: str
    hs_deal_stage_probability: float
    hubspot_owner_id: str
    associated_company_ids: str
    properties: str


class HubSpotOwnerRow(BaseModel):
    model_config = _ROW

    dataorbit_sync_id: str = Field(alias="_dataorbit_sync_id")
    dataorbit_synced_at: str = Field(alias="_dataorbit_synced_at")
    owner_id: str
    email: str
    first_name: str
    last_name: str
    user_id: str


class NetSuiteCustomerRow(BaseModel):
    model_config = _ROW

    dataorbit_sync_id: str = Field(alias="_dataorbit_sync_id")
    dataorbit_synced_at: str = Field(alias="_dataorbit_synced_at")
    id: str
    company_name: str
    email: str
    entity_id: str
    subsidiary: str
    terms: str
    balance: float
    category: str
    last_modified_date: str
    custom_fields: str


class NetSuiteInvoiceRow(BaseModel):
    model_config = _ROW

    dataorbit_sync_id: str = Field(alias="_dataorbit_sync_id")
    dataorbit_synced_at: str = Field(alias="_dataorbit_synced_at")
    id: str
    entity_id: str
    tran_date: str
    due_date: str
    total: float
    amount_remaining: float
    status: str
    line_items: str
    last_modified_date: str


class NetSuitePaymentRow(BaseModel):
    model_config = _ROW

    dataorbit_sync_id: str = Field(alias="_dataorbit_sync_id")
    dataorbit_synced_at: str = Field(alias="_dataorbit_synced_at")
    id: str
    customer_id: str
    total: float
    tran_date: str
    apply_list: str
    last_modified_date: str


class NetSuiteVendorBillRow(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    dataorbit_sync_id: str = Field(alias="_dataorbit_sync_id")
    dataorbit_synced_at: str = Field(alias="_dataorbit_synced_at")
    id: str
    entity_id: str
    tran_date: str
    total: float
    line_items: str
    class_name: str = Field(alias="class")
    department: str
    last_modified_date: str


class HarvestClientRow(BaseModel):
    model_config = _ROW

    dataorbit_sync_id: str = Field(alias="_dataorbit_sync_id")
    dataorbit_synced_at: str = Field(alias="_dataorbit_synced_at")
    id: int
    name: str
    is_active: bool
    address: str
    currency: str


class HarvestProjectRow(BaseModel):
    model_config = _ROW

    dataorbit_sync_id: str = Field(alias="_dataorbit_sync_id")
    dataorbit_synced_at: str = Field(alias="_dataorbit_synced_at")
    id: int
    client_id: int
    name: str
    code: str
    is_active: bool
    is_billable: bool
    budget: float
    budget_by: str
    fee: float
    hourly_rate: float
    cost_budget: float
    starts_on: str
    ends_on: str
    over_budget_notification_percentage: float
    created_at: str
    updated_at: str


class HarvestUserRow(BaseModel):
    model_config = _ROW

    dataorbit_sync_id: str = Field(alias="_dataorbit_sync_id")
    dataorbit_synced_at: str = Field(alias="_dataorbit_synced_at")
    id: int
    first_name: str
    last_name: str
    email: str
    is_active: bool
    is_contractor: bool
    roles: str
    cost_rate: float
    default_hourly_rate: float
    weekly_capacity: int
    created_at: str
    updated_at: str


class HarvestTaskRow(BaseModel):
    model_config = _ROW

    dataorbit_sync_id: str = Field(alias="_dataorbit_sync_id")
    dataorbit_synced_at: str = Field(alias="_dataorbit_synced_at")
    id: int
    name: str
    is_default: bool
    default_hourly_rate: float
    is_active: bool


class HarvestProjectAssignmentRow(BaseModel):
    model_config = _ROW

    dataorbit_sync_id: str = Field(alias="_dataorbit_sync_id")
    dataorbit_synced_at: str = Field(alias="_dataorbit_synced_at")
    id: int
    project_id: int
    user_id: int
    is_active: bool
    hourly_rate: float
    budget: float


class HarvestTimeEntryRow(BaseModel):
    model_config = _ROW

    dataorbit_sync_id: str = Field(alias="_dataorbit_sync_id")
    dataorbit_synced_at: str = Field(alias="_dataorbit_synced_at")
    id: int
    user_id: int
    project_id: int
    task_id: int
    spent_date: str
    hours: float
    billable: bool
    billable_rate: float
    cost_rate: float
    notes: str
    is_locked: bool
    created_at: str
    updated_at: str


class BambooEmployeeRow(BaseModel):
    model_config = _ROW

    dataorbit_sync_id: str = Field(alias="_dataorbit_sync_id")
    dataorbit_synced_at: str = Field(alias="_dataorbit_synced_at")
    id: str
    display_name: str
    first_name: str
    last_name: str
    work_email: str
    department: str
    division: str
    job_title: str
    supervisor_id: str
    location: str
    hire_date: str
    termination_date: str
    status: str
    pay_rate: float
    pay_type: str
    pay_per: str
    employee_number: str
    custom_fields: str


class BambooTimeOffRow(BaseModel):
    model_config = _ROW

    dataorbit_sync_id: str = Field(alias="_dataorbit_sync_id")
    dataorbit_synced_at: str = Field(alias="_dataorbit_synced_at")
    id: str
    employee_id: str
    time_off_type: str
    start_date: str
    end_date: str
    status: str
    amount: float
    unit: str
