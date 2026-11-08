"""Datos de ejemplo para la demo. Todos los nombres y correos son ficticios."""
from datetime import datetime, timedelta

from sqlmodel import Session, select

from .config import get_settings
from .models import Client, Invoice, InvoiceStatus, ReminderLog, User
from .routers.invoices import new_reference
from .security import hash_password
from .services.reminders import TZ

settings = get_settings()
DEMO_EMAIL = "demo@invoicechaser.dev"
DEMO_PASSWORD = "demo12345"


def seed_demo(session: Session) -> None:
    if session.exec(select(User).where(User.email == DEMO_EMAIL)).first():
        return
    user = User(email=DEMO_EMAIL, full_name="Usuario Demo", business_name="Transportes Ejemplo S.A.S.",
                password_hash=hash_password(DEMO_PASSWORD), accepted_policy_version=settings.privacy_policy_version)
    session.add(user)
    session.commit()
    session.refresh(user)

    clients = [
        Client(owner_id=user.id, name="Ferretería La Esquina", email="pagos@ferreteria-ejemplo.co", phone="3001234567"),
        Client(owner_id=user.id, name="Distribuidora Andina", email="cartera@andina-ejemplo.co"),
        Client(owner_id=user.id, name="Café Montaña Ltda.", email="admin@cafe-ejemplo.co", phone="3109876543"),
    ]
    session.add_all(clients)
    session.commit()
    for c in clients:
        session.refresh(c)

    today = datetime.now(TZ).date()
    specs = [
        # (cliente, número, descripción, monto, días desde vencimiento, estado)
        (0, "FV-1001", "Flete Medellín - Bogotá", 1_850_000, -10, InvoiceStatus.pending),
        (1, "FV-1002", "Flete Rionegro - Cali", 2_400_000, -2, InvoiceStatus.pending),
        (2, "FV-1003", "Transporte de café, 3 viajes", 3_150_000, 9, InvoiceStatus.pending),
        (0, "FV-0998", "Flete Guarne - Cartagena", 4_200_000, 16, InvoiceStatus.pending),
        (1, "FV-0990", "Flete Medellín - Pereira", 1_200_000, 25, InvoiceStatus.paid),
        (2, "FV-0985", "Transporte de insumos", 980_000, 40, InvoiceStatus.paid),
    ]
    for ci, number, desc, amount, days_from_due, status in specs:
        due = today - timedelta(days=days_from_due)
        inv = Invoice(owner_id=user.id, client_id=clients[ci].id, number=number, description=desc,
                      amount_cop=amount, issue_date=due - timedelta(days=30), due_date=due, status=status,
                      payment_reference=new_reference())
        if status == InvoiceStatus.paid:
            inv.paid_at = datetime.combine(due + timedelta(days=5), datetime.min.time(), TZ)
        session.add(inv)
        session.commit()
        session.refresh(inv)
        # Historial de recordatorios ya enviados
        for off in settings.reminder_offset_list:
            if off <= days_from_due and (status == InvoiceStatus.pending or off <= 7):
                sent = datetime.combine(due + timedelta(days=off), datetime.min.time(), TZ).replace(hour=9)
                session.add(ReminderLog(invoice_id=inv.id, offset_days=off, sent_at=sent,
                                        subject=f"Recordatorio factura {number} ({off:+d} días)"))
        session.commit()
