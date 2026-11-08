from datetime import date, datetime, timedelta

from sqlmodel import select

from app.models import Client, Invoice, ReminderLog, User
from app.services.reminders import TZ, due_offset, is_allowed_contact_time, process_reminders

# Martes 10 de noviembre de 2026, 10:00 hora Colombia (día hábil, no festivo)
TUESDAY_10AM = datetime(2026, 11, 10, 10, 0, tzinfo=TZ)


def inv(due: date) -> Invoice:
    return Invoice(owner_id=1, client_id=1, number="F", amount_cop=1000, issue_date=due, due_date=due,
                   payment_reference="R")


def test_allowed_hours():
    assert is_allowed_contact_time(TUESDAY_10AM)
    assert not is_allowed_contact_time(TUESDAY_10AM.replace(hour=6))
    assert not is_allowed_contact_time(TUESDAY_10AM.replace(hour=19))
    assert is_allowed_contact_time(datetime(2026, 11, 14, 14, 0, tzinfo=TZ))      # sábado 2 p. m.
    assert not is_allowed_contact_time(datetime(2026, 11, 14, 15, 0, tzinfo=TZ))  # sábado 3 p. m.
    assert not is_allowed_contact_time(datetime(2026, 11, 15, 10, 0, tzinfo=TZ))  # domingo
    assert not is_allowed_contact_time(datetime(2026, 11, 16, 10, 0, tzinfo=TZ))  # festivo (Independencia de Cartagena)


def test_due_offset_rules():
    today = TUESDAY_10AM.date()
    assert due_offset(inv(today + timedelta(days=5)), today, set(), None) is None   # faltan 5 días
    assert due_offset(inv(today + timedelta(days=3)), today, set(), None) == -3
    assert due_offset(inv(today), today, {-3}, None) == 0
    assert due_offset(inv(today), today, {-3, 0}, None) is None                    # ya enviado
    # Proceso apagado mucho tiempo: solo el más reciente, no todos de golpe
    assert due_offset(inv(today - timedelta(days=15)), today, set(), None) == 14
    # Mínimo de días entre cobros de facturas vencidas
    assert due_offset(inv(today - timedelta(days=14)), today, {7}, today - timedelta(days=3)) is None
    assert due_offset(inv(today - timedelta(days=14)), today, {7}, today - timedelta(days=7)) == 14


def _setup(session, days_from_due: int) -> Invoice:
    user = User(email=f"u{days_from_due}@example.com", full_name="U", business_name="Negocio",
                password_hash="x", accepted_policy_version="v")
    session.add(user)
    session.commit()
    session.refresh(user)
    client = Client(owner_id=user.id, name="Cliente", email="c@example.com")
    session.add(client)
    session.commit()
    session.refresh(client)
    due = TUESDAY_10AM.date() - timedelta(days=days_from_due)
    invoice = Invoice(owner_id=user.id, client_id=client.id, number="F-9", amount_cop=100_000,
                      issue_date=due, due_date=due, payment_reference=f"REF-{days_from_due}")
    session.add(invoice)
    session.commit()
    session.refresh(invoice)
    return invoice


def _logs(session, invoice):
    return session.exec(select(ReminderLog).where(ReminderLog.invoice_id == invoice.id)).all()


def test_process_sends_once(client, session):
    invoice = _setup(session, days_from_due=0)
    process_reminders(session, now=TUESDAY_10AM, owner_id=invoice.owner_id)
    process_reminders(session, now=TUESDAY_10AM.replace(hour=11), owner_id=invoice.owner_id)
    logs = _logs(session, invoice)
    assert [log.offset_days for log in logs] == [0]


def test_process_respects_quiet_hours(client, session):
    invoice = _setup(session, days_from_due=7)
    assert process_reminders(session, now=TUESDAY_10AM.replace(hour=21), owner_id=invoice.owner_id) == 0
    assert _logs(session, invoice) == []


def test_paid_invoices_get_no_reminders(client, session):
    from app.models import InvoiceStatus
    invoice = _setup(session, days_from_due=7)
    invoice.status = InvoiceStatus.paid
    session.add(invoice)
    session.commit()
    assert process_reminders(session, now=TUESDAY_10AM, owner_id=invoice.owner_id) == 0
