"""Tablas de la base de datos."""
from datetime import date, datetime, timezone
from enum import Enum

from sqlmodel import Field, SQLModel, UniqueConstraint


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class InvoiceStatus(str, Enum):
    pending = "pending"
    paid = "paid"
    cancelled = "cancelled"


class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True, max_length=255)
    full_name: str = Field(max_length=120)
    business_name: str = Field(max_length=120)
    password_hash: str
    # Evidencia de autorización de tratamiento de datos (Ley 1581 de 2012)
    accepted_policy_version: str
    accepted_policy_at: datetime = Field(default_factory=utcnow)
    created_at: datetime = Field(default_factory=utcnow)


class Client(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    owner_id: int = Field(foreign_key="user.id", index=True)
    name: str = Field(max_length=120)
    email: str = Field(max_length=255)
    phone: str | None = Field(default=None, max_length=30)
    created_at: datetime = Field(default_factory=utcnow)


class Invoice(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    owner_id: int = Field(foreign_key="user.id", index=True)
    client_id: int = Field(foreign_key="client.id", index=True)
    number: str = Field(max_length=40)
    description: str = Field(default="", max_length=500)
    amount_cop: int  # pesos colombianos, sin decimales
    issue_date: date
    due_date: date = Field(index=True)
    status: InvoiceStatus = Field(default=InvoiceStatus.pending, index=True)
    payment_reference: str = Field(index=True, unique=True, max_length=64)
    paid_at: datetime | None = None
    wompi_transaction_id: str | None = Field(default=None, max_length=64)
    created_at: datetime = Field(default_factory=utcnow)


class ReminderLog(SQLModel, table=True):
    """Un registro por cada recordatorio enviado. La restricción única evita duplicados."""

    __table_args__ = (UniqueConstraint("invoice_id", "offset_days"),)

    id: int | None = Field(default=None, primary_key=True)
    invoice_id: int = Field(foreign_key="invoice.id", index=True)
    offset_days: int
    channel: str = Field(default="email", max_length=20)
    sent_at: datetime = Field(default_factory=utcnow)
    subject: str = Field(max_length=200)
    delivered: bool = True
