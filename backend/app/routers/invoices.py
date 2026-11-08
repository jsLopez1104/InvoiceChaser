import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, delete, select

from ..db import get_session
from ..models import Client, Invoice, InvoiceStatus, ReminderLog, User
from ..schemas import InvoiceIn, InvoiceOut, ReminderOut
from ..security import get_current_user
from ..services.payments import payment_link
from ..services.reminders import TZ
from .clients import get_owned_client

router = APIRouter(prefix="/invoices", tags=["invoices"])


def new_reference() -> str:
    return f"IC-{secrets.token_hex(8).upper()}"


def to_out(inv: Invoice, client: Client, session: Session) -> InvoiceOut:
    today = datetime.now(TZ).date()
    days = (today - inv.due_date).days
    overdue = inv.status == InvoiceStatus.pending and days > 0
    logs = session.exec(
        select(ReminderLog).where(ReminderLog.invoice_id == inv.id).order_by(ReminderLog.sent_at)
    ).all()
    return InvoiceOut(
        id=inv.id, client_id=client.id, client_name=client.name, number=inv.number,
        description=inv.description, amount_cop=inv.amount_cop, issue_date=inv.issue_date,
        due_date=inv.due_date, status=inv.status, is_overdue=overdue, days_overdue=max(days, 0) if overdue else 0,
        payment_reference=inv.payment_reference,
        payment_link=payment_link(inv) if inv.status == InvoiceStatus.pending else None,
        paid_at=inv.paid_at,
        reminders=[ReminderOut(id=r.id, offset_days=r.offset_days, channel=r.channel, sent_at=r.sent_at,
                               subject=r.subject) for r in logs],
    )


def get_owned_invoice(invoice_id: int, user: User, session: Session) -> Invoice:
    inv = session.get(Invoice, invoice_id)
    if inv is None or inv.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    return inv


@router.get("", response_model=list[InvoiceOut])
def list_invoices(
    status: InvoiceStatus | None = Query(default=None),
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    q = (select(Invoice, Client).join(Client, Client.id == Invoice.client_id)
         .where(Invoice.owner_id == user.id).order_by(Invoice.due_date))
    if status:
        q = q.where(Invoice.status == status)
    return [to_out(inv, c, session) for inv, c in session.exec(q).all()]


@router.post("", response_model=InvoiceOut, status_code=201)
def create_invoice(data: InvoiceIn, user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    client = get_owned_client(data.client_id, user, session)
    inv = Invoice(owner_id=user.id, payment_reference=new_reference(), **data.model_dump())
    session.add(inv)
    session.commit()
    session.refresh(inv)
    return to_out(inv, client, session)


@router.get("/{invoice_id}", response_model=InvoiceOut)
def get_invoice(invoice_id: int, user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    inv = get_owned_invoice(invoice_id, user, session)
    return to_out(inv, session.get(Client, inv.client_id), session)


@router.post("/{invoice_id}/mark-paid", response_model=InvoiceOut)
def mark_paid(invoice_id: int, user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    """Para pagos recibidos por fuera de la pasarela (transferencia, efectivo)."""
    inv = get_owned_invoice(invoice_id, user, session)
    if inv.status != InvoiceStatus.pending:
        raise HTTPException(status_code=409, detail="La factura no está pendiente")
    inv.status, inv.paid_at = InvoiceStatus.paid, datetime.now(timezone.utc)
    session.add(inv)
    session.commit()
    session.refresh(inv)
    return to_out(inv, session.get(Client, inv.client_id), session)


@router.post("/{invoice_id}/cancel", response_model=InvoiceOut)
def cancel(invoice_id: int, user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    inv = get_owned_invoice(invoice_id, user, session)
    if inv.status != InvoiceStatus.pending:
        raise HTTPException(status_code=409, detail="La factura no está pendiente")
    inv.status = InvoiceStatus.cancelled
    session.add(inv)
    session.commit()
    session.refresh(inv)
    return to_out(inv, session.get(Client, inv.client_id), session)


@router.delete("/{invoice_id}", status_code=204)
def delete_invoice(invoice_id: int, user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    inv = get_owned_invoice(invoice_id, user, session)
    session.exec(delete(ReminderLog).where(ReminderLog.invoice_id == inv.id))
    session.delete(inv)
    session.commit()
