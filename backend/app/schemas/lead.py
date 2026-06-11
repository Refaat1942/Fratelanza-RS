from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field

from app.models.crm import LeadSource, LeadStage


class LeadCreate(BaseModel):
    full_name: str = Field(min_length=2)
    mobile: str = Field(min_length=8)
    email: Optional[str] = None
    source: LeadSource = LeadSource.WEBSITE
    stage: LeadStage = LeadStage.NEW
    customer_id: Optional[int] = None
    project_id: Optional[int] = None
    assigned_to_id: Optional[int] = None
    broker_id: Optional[int] = None
    budget_min: Optional[Decimal] = None
    budget_max: Optional[Decimal] = None
    notes: Optional[str] = None
    next_follow_up: Optional[str] = None


class LeadUpdate(BaseModel):
    full_name: Optional[str] = None
    mobile: Optional[str] = None
    email: Optional[str] = None
    source: Optional[LeadSource] = None
    stage: Optional[LeadStage] = None
    assigned_to_id: Optional[int] = None
    score: Optional[int] = None
    notes: Optional[str] = None
    next_follow_up: Optional[str] = None


class LeadAssignRequest(BaseModel):
    assigned_to_id: Optional[int] = None
    auto: bool = False


class LeadResponse(LeadCreate):
    id: int
    company_id: int
    score: int
    ai_score: Optional[Decimal] = None
    ai_qualification: Optional[str] = None
    assigned_to_name: Optional[str] = None

    model_config = {"from_attributes": True}
