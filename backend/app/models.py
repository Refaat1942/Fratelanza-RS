import enum
import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Index, JSON, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.rbac import SystemRole
from app.db.base import Base


def new_uuid() -> str:
    return str(uuid.uuid4())


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class TenantMixin:
    company_id: Mapped[str | None] = mapped_column(ForeignKey("companies.id"), index=True, nullable=True)


class CompanyStatus(str, enum.Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TRIAL = "trial"


class UserStatus(str, enum.Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    PENDING = "pending"


class LeadSource(str, enum.Enum):
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"
    GOOGLE_ADS = "google_ads"
    WEBSITE = "website"
    REFERRAL = "referral"
    BROKER = "broker"
    CALL_CENTER = "call_center"
    WALK_IN = "walk_in"


class LeadStage(str, enum.Enum):
    NEW = "new"
    CONTACTED = "contacted"
    INTERESTED = "interested"
    SITE_VISIT = "site_visit"
    NEGOTIATION = "negotiation"
    RESERVATION = "reservation"
    CONTRACT_SIGNED = "contract_signed"
    LOST = "lost"


class UnitStatus(str, enum.Enum):
    AVAILABLE = "available"
    RESERVED = "reserved"
    CONTRACTED = "contracted"
    SOLD = "sold"
    DELIVERED = "delivered"
    BLOCKED = "blocked"


class UnitType(str, enum.Enum):
    APARTMENT = "apartment"
    VILLA = "villa"
    TWIN_HOUSE = "twin_house"
    TOWN_HOUSE = "town_house"
    CHALET = "chalet"
    PENTHOUSE = "penthouse"
    DUPLEX = "duplex"
    OFFICE = "office"
    RETAIL = "retail"
    CLINIC = "clinic"
    WAREHOUSE = "warehouse"


class ReservationStatus(str, enum.Enum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    CONVERTED_TO_CONTRACT = "converted_to_contract"


class ContractStatus(str, enum.Enum):
    DRAFT = "draft"
    APPROVED = "approved"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class InstallmentStatus(str, enum.Enum):
    UPCOMING = "upcoming"
    DUE = "due"
    OVERDUE = "overdue"
    PAID = "paid"


class TicketStatus(str, enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    WAITING_CUSTOMER = "waiting_customer"
    RESOLVED = "resolved"
    CLOSED = "closed"


class SubscriptionPlan(Base, TimestampMixin):
    __tablename__ = "subscription_plans"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    code: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name_ar: Mapped[str] = mapped_column(String(255))
    name_en: Mapped[str] = mapped_column(String(255))
    max_users: Mapped[int] = mapped_column(default=25)
    max_storage_gb: Mapped[int] = mapped_column(default=50)
    features: Mapped[dict] = mapped_column(JSON, default=dict)


class Company(Base, TimestampMixin):
    __tablename__ = "companies"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    subscription_plan_id: Mapped[str | None] = mapped_column(ForeignKey("subscription_plans.id"))
    name_ar: Mapped[str] = mapped_column(String(255), index=True)
    name_en: Mapped[str] = mapped_column(String(255), index=True)
    legal_name: Mapped[str | None] = mapped_column(String(255))
    tax_number: Mapped[str | None] = mapped_column(String(100))
    country: Mapped[str] = mapped_column(String(100), default="Egypt")
    city: Mapped[str | None] = mapped_column(String(100))
    status: Mapped[CompanyStatus] = mapped_column(Enum(CompanyStatus), default=CompanyStatus.TRIAL)
    storage_limit_gb: Mapped[int] = mapped_column(default=50)
    settings: Mapped[dict] = mapped_column(JSON, default=dict)

    branches: Mapped[list["Branch"]] = relationship(back_populates="company")


class Branch(Base, TimestampMixin, TenantMixin):
    __tablename__ = "branches"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    name_ar: Mapped[str] = mapped_column(String(255))
    name_en: Mapped[str] = mapped_column(String(255))
    city: Mapped[str | None] = mapped_column(String(100))
    address: Mapped[str | None] = mapped_column(Text)

    company: Mapped[Company | None] = relationship(back_populates="branches")


class User(Base, TimestampMixin, TenantMixin):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    branch_id: Mapped[str | None] = mapped_column(ForeignKey("branches.id"))
    full_name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    mobile: Mapped[str | None] = mapped_column(String(40), index=True)
    password_hash: Mapped[str] = mapped_column(String(512))
    role: Mapped[SystemRole] = mapped_column(Enum(SystemRole), index=True)
    status: Mapped[UserStatus] = mapped_column(Enum(UserStatus), default=UserStatus.PENDING)
    locale: Mapped[str] = mapped_column(String(8), default="ar")
    two_factor_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Customer(Base, TimestampMixin, TenantMixin):
    __tablename__ = "customers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    full_name: Mapped[str] = mapped_column(String(255), index=True)
    mobile: Mapped[str] = mapped_column(String(40), index=True)
    whatsapp: Mapped[str | None] = mapped_column(String(40))
    email: Mapped[str | None] = mapped_column(String(320), index=True)
    national_id: Mapped[str | None] = mapped_column(String(64), index=True)
    passport_number: Mapped[str | None] = mapped_column(String(64), index=True)
    address: Mapped[str | None] = mapped_column(Text)
    city: Mapped[str | None] = mapped_column(String(100))
    country: Mapped[str | None] = mapped_column(String(100))
    occupation: Mapped[str | None] = mapped_column(String(255))
    employer: Mapped[str | None] = mapped_column(String(255))
    income_range: Mapped[str | None] = mapped_column(String(100))
    notes: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)


class CustomerDocument(Base, TimestampMixin, TenantMixin):
    __tablename__ = "customer_documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    customer_id: Mapped[str] = mapped_column(ForeignKey("customers.id"), index=True)
    title: Mapped[str] = mapped_column(String(255))
    document_type: Mapped[str] = mapped_column(String(100))
    storage_key: Mapped[str] = mapped_column(String(1024))
    version: Mapped[int] = mapped_column(default=1)


class CustomerTimelineEvent(Base, TimestampMixin, TenantMixin):
    __tablename__ = "customer_timeline_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    customer_id: Mapped[str] = mapped_column(ForeignKey("customers.id"), index=True)
    event_type: Mapped[str] = mapped_column(String(100), index=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    actor_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    event_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Broker(Base, TimestampMixin, TenantMixin):
    __tablename__ = "brokers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    name: Mapped[str] = mapped_column(String(255), index=True)
    mobile: Mapped[str | None] = mapped_column(String(40))
    email: Mapped[str | None] = mapped_column(String(320))
    commission_rate: Mapped[Decimal] = mapped_column(Numeric(6, 3), default=Decimal("0.000"))
    status: Mapped[str] = mapped_column(String(32), default="active")


class Project(Base, TimestampMixin, TenantMixin):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    branch_id: Mapped[str | None] = mapped_column(ForeignKey("branches.id"))
    code: Mapped[str] = mapped_column(String(64), index=True)
    name_ar: Mapped[str] = mapped_column(String(255), index=True)
    name_en: Mapped[str] = mapped_column(String(255), index=True)
    city: Mapped[str | None] = mapped_column(String(100))
    country: Mapped[str | None] = mapped_column(String(100))
    launch_date: Mapped[date | None] = mapped_column(Date)
    delivery_date: Mapped[date | None] = mapped_column(Date)
    description: Mapped[str | None] = mapped_column(Text)


class Building(Base, TimestampMixin, TenantMixin):
    __tablename__ = "buildings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), index=True)
    code: Mapped[str] = mapped_column(String(64))
    name: Mapped[str] = mapped_column(String(255))


class Floor(Base, TimestampMixin, TenantMixin):
    __tablename__ = "floors"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    building_id: Mapped[str] = mapped_column(ForeignKey("buildings.id"), index=True)
    number: Mapped[int] = mapped_column(index=True)
    label: Mapped[str | None] = mapped_column(String(100))


class Unit(Base, TimestampMixin, TenantMixin):
    __tablename__ = "units"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), index=True)
    building_id: Mapped[str | None] = mapped_column(ForeignKey("buildings.id"), index=True)
    floor_id: Mapped[str | None] = mapped_column(ForeignKey("floors.id"), index=True)
    unit_code: Mapped[str] = mapped_column(String(100), index=True)
    unit_number: Mapped[str] = mapped_column(String(100), index=True)
    unit_type: Mapped[UnitType] = mapped_column(Enum(UnitType), index=True)
    status: Mapped[UnitStatus] = mapped_column(Enum(UnitStatus), default=UnitStatus.AVAILABLE, index=True)
    area: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    garden_area: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"))
    roof_area: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"))
    bedrooms: Mapped[int | None] = mapped_column()
    bathrooms: Mapped[int | None] = mapped_column()
    price: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    maintenance_fees: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0.00"))
    delivery_date: Mapped[date | None] = mapped_column(Date)
    media: Mapped[dict] = mapped_column(JSON, default=dict)

    __table_args__ = (Index("ix_units_company_code", "company_id", "unit_code", unique=True),)


class Lead(Base, TimestampMixin, TenantMixin):
    __tablename__ = "leads"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    customer_id: Mapped[str | None] = mapped_column(ForeignKey("customers.id"), index=True)
    broker_id: Mapped[str | None] = mapped_column(ForeignKey("brokers.id"), index=True)
    assigned_to_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), index=True)
    source: Mapped[LeadSource] = mapped_column(Enum(LeadSource), index=True)
    stage: Mapped[LeadStage] = mapped_column(Enum(LeadStage), default=LeadStage.NEW, index=True)
    score: Mapped[int] = mapped_column(default=0)
    budget_min: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    budget_max: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    interested_project_id: Mapped[str | None] = mapped_column(ForeignKey("projects.id"))
    notes: Mapped[str | None] = mapped_column(Text)


class Reservation(Base, TimestampMixin, TenantMixin):
    __tablename__ = "reservations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    reservation_number: Mapped[str] = mapped_column(String(100), index=True)
    customer_id: Mapped[str] = mapped_column(ForeignKey("customers.id"), index=True)
    unit_id: Mapped[str] = mapped_column(ForeignKey("units.id"), index=True)
    sales_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    deposit: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0.00"))
    reservation_date: Mapped[date] = mapped_column(Date)
    expiry_date: Mapped[date] = mapped_column(Date)
    status: Mapped[ReservationStatus] = mapped_column(
        Enum(ReservationStatus), default=ReservationStatus.DRAFT, index=True
    )

    __table_args__ = (Index("ix_reservations_company_number", "company_id", "reservation_number", unique=True),)


class Contract(Base, TimestampMixin, TenantMixin):
    __tablename__ = "contracts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    contract_number: Mapped[str] = mapped_column(String(100), index=True)
    reservation_id: Mapped[str | None] = mapped_column(ForeignKey("reservations.id"), index=True)
    customer_id: Mapped[str] = mapped_column(ForeignKey("customers.id"), index=True)
    unit_id: Mapped[str] = mapped_column(ForeignKey("units.id"), index=True)
    status: Mapped[ContractStatus] = mapped_column(Enum(ContractStatus), default=ContractStatus.DRAFT)
    total_value: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    signed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    active_version: Mapped[int] = mapped_column(default=1)

    __table_args__ = (Index("ix_contracts_company_number", "company_id", "contract_number", unique=True),)


class ContractVersion(Base, TimestampMixin, TenantMixin):
    __tablename__ = "contract_versions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    contract_id: Mapped[str] = mapped_column(ForeignKey("contracts.id"), index=True)
    version: Mapped[int] = mapped_column(default=1)
    language: Mapped[str] = mapped_column(String(8), default="ar")
    body_html: Mapped[str] = mapped_column(Text)
    approved_by_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class PaymentPlan(Base, TimestampMixin, TenantMixin):
    __tablename__ = "payment_plans"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    name: Mapped[str] = mapped_column(String(255))
    frequency: Mapped[str] = mapped_column(String(32))
    down_payment_percentage: Mapped[Decimal] = mapped_column(Numeric(6, 3), default=Decimal("0.000"))
    years: Mapped[int] = mapped_column(default=1)
    rules: Mapped[dict] = mapped_column(JSON, default=dict)


class Installment(Base, TimestampMixin, TenantMixin):
    __tablename__ = "installments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    contract_id: Mapped[str] = mapped_column(ForeignKey("contracts.id"), index=True)
    due_date: Mapped[date] = mapped_column(Date, index=True)
    due_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    paid_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0.00"))
    status: Mapped[InstallmentStatus] = mapped_column(
        Enum(InstallmentStatus), default=InstallmentStatus.UPCOMING, index=True
    )


class Payment(Base, TimestampMixin, TenantMixin):
    __tablename__ = "payments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    installment_id: Mapped[str | None] = mapped_column(ForeignKey("installments.id"), index=True)
    contract_id: Mapped[str] = mapped_column(ForeignKey("contracts.id"), index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    paid_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    method: Mapped[str] = mapped_column(String(64))
    reference_number: Mapped[str | None] = mapped_column(String(100), index=True)


class BrokerCommission(Base, TimestampMixin, TenantMixin):
    __tablename__ = "broker_commissions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    broker_id: Mapped[str] = mapped_column(ForeignKey("brokers.id"), index=True)
    contract_id: Mapped[str] = mapped_column(ForeignKey("contracts.id"), index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    status: Mapped[str] = mapped_column(String(32), default="pending_approval")
    settled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Ticket(Base, TimestampMixin, TenantMixin):
    __tablename__ = "tickets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    customer_id: Mapped[str | None] = mapped_column(ForeignKey("customers.id"), index=True)
    assigned_to_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), index=True)
    subject: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    status: Mapped[TicketStatus] = mapped_column(Enum(TicketStatus), default=TicketStatus.OPEN)
    priority: Mapped[str] = mapped_column(String(32), default="normal")
    sla_due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Notification(Base, TimestampMixin, TenantMixin):
    __tablename__ = "notifications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), index=True)
    channel: Mapped[str] = mapped_column(String(32))
    title: Mapped[str] = mapped_column(String(255))
    body: Mapped[str] = mapped_column(Text)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    delivery_status: Mapped[str] = mapped_column(String(32), default="pending")


class AuditLog(Base, TimestampMixin, TenantMixin):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    actor_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), index=True)
    action: Mapped[str] = mapped_column(String(128), index=True)
    entity_type: Mapped[str] = mapped_column(String(128), index=True)
    entity_id: Mapped[str | None] = mapped_column(String(64), index=True)
    ip_address: Mapped[str | None] = mapped_column(String(64))
    details: Mapped[dict] = mapped_column(JSON, default=dict)
