"""Integración con Wompi (pasarela colombiana).

- Link de pago: Web Checkout con firma de integridad
  SHA256(referencia + monto_en_centavos + moneda + secreto_integridad).
- Webhook: se verifica el checksum del evento
  SHA256(valores de signature.properties + timestamp + secreto_eventos).
  Un webhook sin firma válida se rechaza siempre.
"""
import hashlib
import hmac
from urllib.parse import urlencode

from ..config import get_settings
from ..models import Invoice

settings = get_settings()
CURRENCY = "COP"


def integrity_signature(reference: str, amount_in_cents: int, secret: str) -> str:
    raw = f"{reference}{amount_in_cents}{CURRENCY}{secret}"
    return hashlib.sha256(raw.encode()).hexdigest()


def payment_link(invoice: Invoice) -> str | None:
    """Devuelve la URL de pago. En modo demo sin llaves, apunta al simulador del frontend."""
    amount_in_cents = invoice.amount_cop * 100
    if settings.wompi_public_key and settings.wompi_integrity_secret:
        params = {
            "public-key": settings.wompi_public_key,
            "currency": CURRENCY,
            "amount-in-cents": amount_in_cents,
            "reference": invoice.payment_reference,
            "signature:integrity": integrity_signature(
                invoice.payment_reference, amount_in_cents, settings.wompi_integrity_secret
            ),
            "redirect-url": f"{settings.frontend_url}/gracias",
        }
        return f"{settings.wompi_checkout_url}?{urlencode(params)}"
    if settings.demo_mode:
        return f"{settings.frontend_url}/pagar/{invoice.payment_reference}"
    return None


def _get_path(data: dict, dotted: str):
    value = data
    for key in dotted.split("."):
        value = value[key]
    return value


def event_checksum(event: dict, secret: str) -> str:
    props = event["signature"]["properties"]
    values = "".join(str(_get_path(event["data"], p)) for p in props)
    raw = f"{values}{event['timestamp']}{secret}"
    return hashlib.sha256(raw.encode()).hexdigest()


def verify_event(event: dict, secret: str) -> bool:
    try:
        expected = event_checksum(event, secret)
        received = str(event["signature"]["checksum"]).lower()
    except (KeyError, TypeError):
        return False
    return hmac.compare_digest(expected, received)


def build_fake_event(reference: str, amount_in_cents: int, secret: str, timestamp: int) -> dict:
    """Arma un evento con el mismo formato y firma que Wompi (usado por el simulador y los tests)."""
    event = {
        "event": "transaction.updated",
        "data": {
            "transaction": {
                "id": f"demo-{reference}",
                "status": "APPROVED",
                "reference": reference,
                "amount_in_cents": amount_in_cents,
                "currency": CURRENCY,
            }
        },
        "signature": {
            "properties": ["transaction.id", "transaction.status", "transaction.amount_in_cents"],
            "checksum": "",
        },
        "timestamp": timestamp,
    }
    event["signature"]["checksum"] = event_checksum(event, secret)
    return event
