from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.core.rbac import Permission, SystemRole
from app.models import (
    CompanyStatus,
    ContractStatus,
    InstallmentStatus,
    LeadSource,
    LeadStage,
    ReservationStatus,
    UnitStatus,
    UnitType,
    UserStatus,
)


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserRead(ORMModel):
    id: str
    company_id: str | None
    branch_id: str | None
    full_name: str
    email: EmailStr
    mobile: str | None
    role: SystemRole
    status: UserStatus
    locale: str
    permissions: list[Permission] = []


class UserCreate(BaseModel):
    company_id: str | None = None
    branch_id: str | None = None
    full_name: str
    email: EmailStr
    mobile: str | None = None
    password: str = Field(min_length=8)
    role: SystemRole


class CompanyCreate(BaseModel):
    name_ar: str
    name_en: str
    legal_name: str | None = None
    tax_number: str | None = None
    country: str = "Egypt"
    city: str | None = None
    storage_limit_gb: int = 50


class CompanyRead(ORMModel):
    id: str
    name_ar: str
    name_en: str
    legal_name: str | None
    country: str
    city: str | None
    status: CompanyStatus
    storage_limit_gb: int


class BranchCreate(BaseModel):
    company_id: str
    name_ar: str
    name_en: str
    city: str | None = None
    address: str | None = None


class BranchRead(ORMModel):
    id: str
    company_id: str | None
    name_ar: str
    name_en: str
    city: str | None
    address: str | None


class CustomerCreate(BaseModel):
    full_name: str
    mobile: str
    whatsapp: str | None = None
    email: EmailStr | None = None
    national_id: str | None = None
    passport_number: str | None = None
    address: str | None = None
    city: str | None = None
    country: str | None = None
    occupation: str | None = None
    employer: str | None = None
    income_range: str | None = None
    notes: str | None = None


class CustomerRead(ORMModel):
    id: str
    company_id: str | None
    full_name: str
    mobile: str
    whatsapp: str | None
    email: EmailStr | None
    national_id: str | None
    passport_number: str | None
    city: str | None
    country: str | None
    occupation: str | None
    employer: str | None
    income_range: str | None
    notes: str | None
    created_at: datetime


class ProjectCreate(BaseModel):
    company_id: str | None = None
    branch_id: str | None = None
    code: str
    name_ar: str
    name_en: str
    city: str | None = None
    country: str | None = None
    launch_date: date | None = None
    delivery_date: date | None = None
    description: str | None = None


class ProjectRead(ORMModel):
    id: str
    company_id: str | None
    code: str
    name_ar: str
    name_en: str
    city: str | None
    country: str | None
    delivery_date: date | None


class UnitCreate(BaseModel):
    company_id: str | None = None
    project_id: str
    building_id: str | None = None
    floor_id: str | None = None
    unit_code: str
    unit_number: str
    unit_type: UnitType
    area: Decimal
    garden_area: Decimal = Decimal("0.00")
    roof_area: Decimal = Decimal("0.00")
    bedrooms: int | None = None
    bathrooms: int | None = None
    price: Decimal
    maintenance_fees: Decimal = Decimal("0.00")
    delivery_date: date | None = None


class UnitRead(ORMModel):
    id: str
    company_id: str | None
    project_id: str
    unit_code: str
    unit_number: str
    unit_type: UnitType
    status: UnitStatus
    area: Decimal
    price: Decimal
    maintenance_fees: Decimal
    delivery_date: date | None


class LeadCreate(BaseModel):
    customer_id: str | None = None
    broker_id: str | None = None
    assigned_to_user_id: str | None = None
    source: LeadSource
    stage: LeadStage = LeadStage.NEW
    score: int = 0
    budget_min: Decimal | None = None
    budget_max: Decimal | None = None
    interested_project_id: str | None = None
    notes: str | None = None


class LeadRead(ORMModel):
    id: str
    company_id: str | None
    customer_id: str | None
    broker_id: str | None
    assigned_to_user_id: str | None
    source: LeadSource
    stage: LeadStage
    score: int
    notes: str | None


class ReservationCreate(BaseModel):
    reservation_number: str
    customer_id: str
    unit_id: str
    sales_user_id: str | None = None
    deposit: Decimal = Decimal("0.00")
    reservation_date: date
    expiry_date: date


class ReservationRead(ORMModel):
    id: str
    company_id: str | None
    reservation_number: str
    customer_id: str
    unit_id: str
    deposit: Decimal
    reservation_date: date
    expiry_date: date
    status: ReservationStatus


class ContractCreate(BaseModel):
    contract_number: str
    reservation_id: str | None = None
    customer_id: str
    unit_id: str
    total_value: Decimal


class ContractRead(ORMModel):
    id: str
    company_id: str | None
    contract_number: str
    reservation_id: str | None
    customer_id: str
    unit_id: str
    status: ContractStatus
    total_value: Decimal
    active_version: int


class InstallmentRead(ORMModel):
    id: str
    company_id: str | None
    contract_id: str
    due_date: date
    due_amount: Decimal
    paid_amount: Decimal
    status: InstallmentStatus


class DashboardKPI(BaseModel):
    key: str
    label_ar: str
    label_en: str
    value: int | float | str
    change_percentage: float | None = None


class ExecutiveDashboard(BaseModel):
    kpis: list[DashboardKPI]
    sales_pipeline: dict[str, int]
    unit_inventory: dict[str, int]
    collections: dict[str, Decimal]
