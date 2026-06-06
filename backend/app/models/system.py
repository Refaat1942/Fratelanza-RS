from typing import Optional

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin


class AuditLog(Base, TimestampMixin):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[Optional[int]] = mapped_column(ForeignKey("companies.id"), index=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), index=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    module: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_type: Mapped[Optional[str]] = mapped_column(String(100))
    entity_id: Mapped[Optional[int]] = mapped_column(Integer)
    ip_address: Mapped[Optional[str]] = mapped_column(String(50))
    user_agent: Mapped[Optional[str]] = mapped_column(String(500))
    details: Mapped[Optional[str]] = mapped_column(Text)


class Notification(Base, TimestampMixin):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[Optional[int]] = mapped_column(ForeignKey("companies.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    title_ar: Mapped[str] = mapped_column(String(255), nullable=False)
    title_en: Mapped[str] = mapped_column(String(255), nullable=False)
    message_ar: Mapped[Optional[str]] = mapped_column(Text)
    message_en: Mapped[Optional[str]] = mapped_column(Text)
    notification_type: Mapped[str] = mapped_column(String(50), default="in_app")
    channel: Mapped[str] = mapped_column(String(50), default="in_app")
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    reference_type: Mapped[Optional[str]] = mapped_column(String(50))
    reference_id: Mapped[Optional[int]] = mapped_column(Integer)


class Document(Base, TimestampMixin):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_url: Mapped[str] = mapped_column(String(500), nullable=False)
    file_type: Mapped[Optional[str]] = mapped_column(String(50))
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_type: Mapped[Optional[str]] = mapped_column(String(100))
    entity_id: Mapped[Optional[int]] = mapped_column(Integer)
    version: Mapped[int] = mapped_column(Integer, default=1)
    uploaded_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))


class SystemSetting(Base, TimestampMixin):
    __tablename__ = "system_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    value: Mapped[Optional[str]] = mapped_column(Text)
    value_type: Mapped[str] = mapped_column(String(20), default="string")
    description_ar: Mapped[Optional[str]] = mapped_column(Text)
    description_en: Mapped[Optional[str]] = mapped_column(Text)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
