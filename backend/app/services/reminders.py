"""Motor de recordatorios.

Reglas:
1. Cada factura pendiente tiene recordatorios en días fijos respecto al vencimiento
   (por defecto -3, 0, 7, 14, 21).
2. Nunca se envía dos veces el mismo recordatorio (restricción única invoice_id + offset_days).
3. Si el proceso estuvo apagado, solo se envía el recordatorio más reciente que corresponda,
   no todos los atrasados de golpe.
4. Horario permitido (inspirado en la Ley 2300 de 2023, "Dejen de fregar"):
   lunes a viernes 7:00-19:00 y sábados 8:00-15:00, hora Colombia. Nunca domingos ni festivos.
5. Entre dos recordatorios de cobro (factura ya vencida) pasan al menos `min_days_between_overdue` días.
"""
import logging
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import holidays
from sqlmodel import Session, select

from ..config import get_settings
from ..models import Client, Invoice, InvoiceStatus, ReminderLog, User
from .email import reminder_email, send_email
from .payments import payment_link

settings = get_settings()
log = logging.getLogger("invoicechaser.reminders")
TZ = ZoneInfo(settings.timezone)
CO_HOLIDAYS = holidays.country_holidays("CO")


def is_allowed_contact_time(now_local: datetime) -> bool:
    if now_local.date() in CO_HOLIDAYS:
        return False
    wd, h = now_local.weekday(), now_local.hour  # lunes = 0
    if wd <= 4:
        return 7 <= h < 19
    if wd == 5:
        return 8 <= h < 15
    return False


def due_offset(invoice: Invoice, today: date, already_sent: set[int], last_overdue_sent: date | None) -> int | None:
    """Devuelve el offset que toca enviar hoy, o None."""
    days_from_due = (today - invoice.due_date).days
    candidates = [o for o in settings.reminder_offset_list if o <= days_from_due and o not in already_sent]
    if not candidates:
        return None
    offset = max(candidates)  # solo el más reciente (regla 3)
    # Si ya existe un recordatorio enviado con offset mayor, los anteriores ya no tienen sentido.
    if already_sent and offset < max(already_sent):
        return None
    if offset > 0 and last_overdue_sent is not None:
        if (today - last_overdue_sent).days < settings.min_days_between_overdue:
            return None
    return offset


def process_reminders(session: Session, now: datetime | None = None, owner_id: int | None = None) -> int:
    """Revisa las facturas pendientes y envía lo que corresponda. Devuelve cuántos envió."""
    now_local = (now or datetime.now(TZ)).astimezone(TZ)
    if not is_allowed_contact_time(now_local):
        log.info("Fuera de horario permitido (%s): no se envían recordatorios", now_local.isoformat())
        return 0
    today = now_local.date()
    sent = 0
    q = (
        select(Invoice, Client, User)
        .join(Client, Client.id == Invoice.client_id)
        .join(User, User.id == Invoice.owner_id)
        .where(Invoice.status == InvoiceStatus.pending)
    )
    if owner_id is not None:
        q = q.where(Invoice.owner_id == owner_id)
    rows = session.exec(q).all()
    for invoice, client, user in rows:
        logs = session.exec(select(ReminderLog).where(ReminderLog.invoice_id == invoice.id)).all()
        already = {r.offset_days for r in logs}
        overdue_dates = [r.sent_at.astimezone(TZ).date() if r.sent_at.tzinfo else r.sent_at.date()
                         for r in logs if r.offset_days > 0]
        offset = due_offset(invoice, today, already, max(overdue_dates) if overdue_dates else None)
        if offset is None:
            continue
        subject, body = reminder_email(
            client_name=client.name, business_name=user.business_name, number=invoice.number,
            amount_cop=invoice.amount_cop, due_date=invoice.due_date.isoformat(),
            offset_days=max(offset, (today - invoice.due_date).days) if offset > 0 else offset,
            payment_link=payment_link(invoice),
        )
        if not send_email(client.email, subject, body):
            continue  # no se registra: se reintenta en la próxima corrida
        session.add(ReminderLog(invoice_id=invoice.id, offset_days=offset, subject=subject, sent_at=now_local))
        session.commit()
        sent += 1
    log.info("Recordatorios enviados: %s", sent)
    return sent
