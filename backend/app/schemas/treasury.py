from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field

from app.models.finance import (
    CashTransactionType,
    ChequeDirection,
    ChequeStatus,
    ProgressCertificateStatus,
)


class CashTransactionCreate(BaseModel):
    transaction_date: str
    transaction_type: CashTransactionType
    category: str = Field(min_length=2)
    description: Optional[str] = None
    amount: Decimal = Field(gt=0)
    payment_method: str = "cash"
    reference_number: Optional[str] = None
    project_id: Optional[int] = None


class CashTransactionUpdate(BaseModel):
    transaction_date: Optional[str] = None
    transaction_type: Optional[CashTransactionType] = None
    category: Optional[str] = None
    description: Optional[str] = None
    amount: Optional[Decimal] = Field(default=None, gt=0)
    payment_method: Optional[str] = None
    reference_number: Optional[str] = None
    project_id: Optional[int] = None


class CashTransactionResponse(CashTransactionCreate):
    id: int
    company_id: int

    model_config = {"from_attributes": True}


class CashFlowSummary(BaseModel):
    total_income: float
    total_expense: float
    net_cash_flow: float
    transaction_count: int


class ChequeCreate(BaseModel):
    direction: ChequeDirection
    cheque_number: str = Field(min_length=1)
    bank_name: str = Field(min_length=2)
    drawer_name: Optional[str] = None
    payee_name: Optional[str] = None
    amount: Decimal = Field(gt=0)
    issue_date: str
    due_date: str
    notes: Optional[str] = None
    customer_id: Optional[int] = None
    subcontractor_id: Optional[int] = None


class ChequeUpdate(BaseModel):
    cheque_number: Optional[str] = None
    bank_name: Optional[str] = None
    drawer_name: Optional[str] = None
    payee_name: Optional[str] = None
    amount: Optional[Decimal] = Field(default=None, gt=0)
    issue_date: Optional[str] = None
    due_date: Optional[str] = None
    status: Optional[ChequeStatus] = None
    notes: Optional[str] = None


class ChequeResponse(ChequeCreate):
    id: int
    company_id: int
    status: ChequeStatus

    model_config = {"from_attributes": True}


class SubcontractorCreate(BaseModel):
    code: str = Field(min_length=2)
    name_ar: str = Field(min_length=2)
    name_en: str = Field(min_length=2)
    contact_person: Optional[str] = None
    mobile: Optional[str] = None
    email: Optional[str] = None
    tax_number: Optional[str] = None


class SubcontractorResponse(SubcontractorCreate):
    id: int
    company_id: int

    model_config = {"from_attributes": True}


class SubcontractAgreementCreate(BaseModel):
    subcontractor_id: int
    project_id: Optional[int] = None
    contract_number: str = Field(min_length=2)
    description: Optional[str] = None
    contract_value: Decimal = Field(gt=0)
    retention_percent: Decimal = Field(default=10, ge=0, le=100)
    advance_payment: Decimal = Field(default=0, ge=0)
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class SubcontractAgreementResponse(SubcontractAgreementCreate):
    id: int
    company_id: int
    subcontractor_name: Optional[str] = None

    model_config = {"from_attributes": True}


class ProgressCertificateCalculate(BaseModel):
    agreement_id: int
    progress_percent: int = Field(ge=0, le=100)
    other_deductions: Decimal = Field(default=0, ge=0)


class ProgressCertificateCreate(BaseModel):
    agreement_id: int
    certificate_number: str = Field(min_length=2)
    period_from: str
    period_to: str
    progress_percent: int = Field(ge=0, le=100)
    other_deductions: Decimal = Field(default=0, ge=0)
    notes: Optional[str] = None


class ProgressCertificateResponse(BaseModel):
    id: int
    company_id: int
    agreement_id: int
    certificate_number: str
    period_from: str
    period_to: str
    progress_percent: int
    cumulative_value: Decimal
    current_gross: Decimal
    retention_amount: Decimal
    advance_deduction: Decimal
    other_deductions: Decimal
    net_payable: Decimal
    status: ProgressCertificateStatus
    notes: Optional[str] = None
    subcontractor_name: Optional[str] = None
    contract_number: Optional[str] = None

    model_config = {"from_attributes": True}
