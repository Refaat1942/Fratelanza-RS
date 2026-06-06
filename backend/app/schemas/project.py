from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field

from app.models.real_estate import ProjectStatus, UnitStatus, UnitType


class ProjectCreate(BaseModel):
    name_ar: str = Field(min_length=2)
    name_en: str = Field(min_length=2)
    code: str = Field(min_length=2)
    description_ar: Optional[str] = None
    description_en: Optional[str] = None
    city: Optional[str] = None
    country: str = "Egypt"
    address: Optional[str] = None
    branch_id: Optional[int] = None


class ProjectUpdate(BaseModel):
    name_ar: Optional[str] = None
    name_en: Optional[str] = None
    code: Optional[str] = None
    description_ar: Optional[str] = None
    description_en: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    address: Optional[str] = None
    status: Optional[ProjectStatus] = None


class ProjectResponse(ProjectCreate):
    id: int
    company_id: int
    status: ProjectStatus
    total_units: int
    available_units: int
    cover_image_url: Optional[str] = None

    model_config = {"from_attributes": True}


class UnitCreate(BaseModel):
    floor_id: int
    unit_code: str
    unit_number: str
    unit_type: UnitType
    area_sqm: Decimal
    garden_area_sqm: Optional[Decimal] = None
    roof_area_sqm: Optional[Decimal] = None
    bedrooms: int = 0
    bathrooms: int = 0
    price: Decimal
    maintenance_fee: Optional[Decimal] = None
    delivery_date: Optional[str] = None


class UnitResponse(UnitCreate):
    id: int
    status: UnitStatus
    is_locked: bool

    model_config = {"from_attributes": True}


class ReservationCreate(BaseModel):
    customer_id: int
    unit_id: int
    deposit_amount: Decimal = Decimal("0")
    reservation_date: str
    expiry_date: str
    notes: Optional[str] = None


class ReservationUpdate(BaseModel):
    customer_id: Optional[int] = None
    deposit_amount: Optional[Decimal] = None
    reservation_date: Optional[str] = None
    expiry_date: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = None


class ContractCreate(BaseModel):
    customer_id: int
    unit_id: int
    reservation_id: Optional[int] = None
    total_price: Decimal
    contract_date: str
    contract_ar: Optional[str] = None
    contract_en: Optional[str] = None


class ContractUpdate(BaseModel):
    customer_id: Optional[int] = None
    total_price: Optional[Decimal] = None
    contract_date: Optional[str] = None
    status: Optional[str] = None
    is_signed: Optional[bool] = None
    contract_ar: Optional[str] = None
    contract_en: Optional[str] = None
