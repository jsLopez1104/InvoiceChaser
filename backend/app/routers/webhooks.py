import logging
import secrets
import time
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlmodel import Session, select

from ..config import get_settings
from ..db import get_session
from ..limiter import limiter
from ..models import Invoice, InvoiceStatus
from ..services.payments import build_fake_event, verify_event

router = APIRouter(prefix="/webhooks", tags=["webhooks"])
settings = get_settings()
log = logging.getLogger("invoicechaser.webhooks")
# Aleatorio en cada arranque: el repo es público, así que un secreto fijo permitiría falsificar eventos.
DEMO_EVENTS_SECRET = secrets.token_hex(32)


def events_secret() -> str:
    return settings.wompi_events_secret or (DEMO_EVENTS_SECRET if settings.demo_mode else "")


def apply_event(event: dict, session: Session) -> dict:
    secret = events_secret()
    if not secret or not verify_event(event, secret):
        raise HTTPException(status_code=401, detail="Firma inválida")
    if event.get("event") != "transaction.updated":
        return {"ok": True, "ignored": True}
    tx = event["data"]["transaction"]
    inv = session.exec(select(Invoice).where(Invoice.payment_reference == tx["reference"])).first()
    if inv is None:
        return {"ok": True, "ignored": True}
    # Idempotente: un evento repetido no cambia nada.
    if tx["status"] == "APPROVED" and inv.status == InvoiceStatus.pending:
        if int(tx["amount_in_cents"]) != inv.amount_cop * 100:
            log.warning("Monto no coincide en %s", inv.payment_reference)
            raise HTTPException(status_code=400, detail="Monto no coincide")
        inv.status = InvoiceStatus.paid
        inv.paid_at = datetime.now(timezone.utc)
        inv.wompi_transaction_id = str(tx["id"])
        session.add(inv)
        session.commit()
    return {"ok": True}


@router.post("/wompi")
async def wompi_webhook(request: Request, session: Session = Depends(get_session)):
    try:
        event = await request.json()
    except ValueError:
        raise HTTPException(status_code=400, detail="JSON inválido")
    if not isinstance(event, dict):
        raise HTTPException(status_code=400, detail="JSON inválido")
    return apply_event(event, session)


@router.get("/demo/invoice/{reference}")
def demo_invoice(reference: str, session: Session = Depends(get_session)):
    """Datos públicos mínimos para la página de pago simulado (solo en modo demo)."""
    if not settings.demo_mode or settings.wompi_public_key:
        raise HTTPException(status_code=404)
    inv = session.exec(select(Invoice).where(Invoice.payment_reference == reference)).first()
    if inv is None:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    return {"number": inv.number, "amount_cop": inv.amount_cop, "status": inv.status, "due_date": inv.due_date}


@router.post("/demo/pay/{reference}")
@limiter.limit("10/minute")
def demo_pay(request: Request, reference: str, session: Session = Depends(get_session)):
    """Simula a Wompi: arma un evento firmado y lo pasa por el MISMO flujo de verificación."""
    if not settings.demo_mode or settings.wompi_public_key:
        raise HTTPException(status_code=404)
    inv = session.exec(select(Invoice).where(Invoice.payment_reference == reference)).first()
    if inv is None:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    event = build_fake_event(reference, inv.amount_cop * 100, events_secret(), int(time.time()))
    return apply_event(event, session)
