from datetime import datetime

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from ..db import get_session
from ..models import Client, Invoice, InvoiceStatus, ReminderLog, User
from ..schemas import DashboardOut
from ..security import get_current_user
from ..services.reminders import TZ

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardOut)
def dashboard(user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    today = datetime.now(TZ).date()
    invoices = session.exec(select(Invoice).where(Invoice.owner_id == user.id)).all()
    pending = [i for i in invoices if i.status == InvoiceStatus.pending]
    overdue = [i for i in pending if i.due_date < today]
    paid = [i for i in invoices if i.status == InvoiceStatus.paid]
    recent = session.exec(
        select(ReminderLog, Invoice, Client)
        .join(Invoice, Invoice.id == ReminderLog.invoice_id)
        .join(Client, Client.id == Invoice.client_id)
        .where(Invoice.owner_id == user.id)
        .order_by(ReminderLog.sent_at.desc())
    ).all()
    return DashboardOut(
        total_pending_cop=sum(i.amount_cop for i in pending),
        total_overdue_cop=sum(i.amount_cop for i in overdue),
        total_paid_cop=sum(i.amount_cop for i in paid),
        count_pending=len(pending), count_overdue=len(overdue), count_paid=len(paid),
        reminders_sent=len(recent),
        recent_reminders=[
            {"invoice_number": inv.number, "client": c.name, "subject": r.subject,
             "offset_days": r.offset_days, "sent_at": r.sent_at.isoformat()}
            for r, inv, c in recent[:10]
        ],
    )
