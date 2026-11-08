"""Esquemas de entrada/salida. Todo lo que entra por request se valida aquí."""
from datetime import date, datetime

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

from .models import InvoiceStatus


# ---------- Auth ----------
class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=2, max_length=120)
    business_name: str = Field(min_length=2, max_length=120)
    accept_privacy_policy: bool

    @field_validator("accept_privacy_policy")
    @classmethod
    def must_accept(cls, v: bool) -> bool:
        if not v:
            raise ValueError("Debes aceptar la política de tratamiento de datos")
        return v


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: int
    email: str
    full_name: str
    business_name: str
    accepted_policy_version: str
    accepted_policy_at: datetime


# ---------- Clientes ----------
class ClientIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=30, pattern=r"^\+?[0-9 ]{7,20}$")


class ClientOut(BaseModel):
    id: int
    name: str
    email: str
    phone: str | None
    created_at: datetime


# ---------- Facturas ----------
class InvoiceIn(BaseModel):
    client_id: int = Field(gt=0)
    number: str = Field(min_length=1, max_length=40)
    description: str = Field(default="", max_length=500)
    amount_cop: int = Field(gt=0, le=10_000_000_000)
    issue_date: date
    due_date: date

    @model_validator(mode="after")
    def check_dates(self):
        if self.due_date < self.issue_date:
            raise ValueError("La fecha de vencimiento no puede ser anterior a la de emisión")
        return self


class ReminderOut(BaseModel):
    id: int
    offset_days: int
    channel: str
    sent_at: datetime
    subject: str


class InvoiceOut(BaseModel):
    id: int
    client_id: int
    client_name: str
    number: str
    description: str
    amount_cop: int
    issue_date: date
    due_date: date
    status: InvoiceStatus
    is_overdue: bool
    days_overdue: int
    payment_reference: str
    payment_link: str | None
    paid_at: datetime | None
    reminders: list[ReminderOut] = []


class DashboardOut(BaseModel):
    total_pending_cop: int
    total_overdue_cop: int
    total_paid_cop: int
    count_pending: int
    count_overdue: int
    count_paid: int
    reminders_sent: int
    recent_reminders: list[dict]
