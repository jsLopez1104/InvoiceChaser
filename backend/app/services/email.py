"""Envío de correos con Resend. Sin API key, el correo se imprime en el log (modo desarrollo)."""
import html
import logging

import httpx

from ..config import get_settings

settings = get_settings()
log = logging.getLogger("invoicechaser.email")
RESEND_URL = "https://api.resend.com/emails"


def send_email(to: str, subject: str, html_body: str) -> bool:
    if not settings.resend_api_key:
        log.info("[EMAIL simulado] para=%s asunto=%s", to, subject)
        return True
    try:
        r = httpx.post(
            RESEND_URL,
            headers={"Authorization": f"Bearer {settings.resend_api_key}"},
            json={"from": settings.email_from, "to": [to], "subject": subject, "html": html_body},
            timeout=10,
        )
        r.raise_for_status()
        return True
    except httpx.HTTPError as exc:
        log.error("Error enviando correo a %s: %s", to, exc)
        return False


def format_cop(amount: int) -> str:
    return "$" + f"{amount:,}".replace(",", ".")


def reminder_email(
    *, client_name: str, business_name: str, number: str, amount_cop: int, due_date: str,
    offset_days: int, payment_link: str | None,
) -> tuple[str, str]:
    """Devuelve (asunto, html). El tono sube de amable a firme según los días de mora."""
    esc = html.escape
    amount = format_cop(amount_cop)
    if offset_days < 0:
        subject = f"Recordatorio: la factura {number} vence el {due_date}"
        intro = f"te recordamos que la factura <b>{esc(number)}</b> por <b>{amount}</b> vence el <b>{due_date}</b>."
    elif offset_days == 0:
        subject = f"Hoy vence la factura {number}"
        intro = f"hoy vence la factura <b>{esc(number)}</b> por <b>{amount}</b>."
    elif offset_days <= 7:
        subject = f"Factura {number} vencida"
        intro = (
            f"la factura <b>{esc(number)}</b> por <b>{amount}</b> venció el <b>{due_date}</b> "
            f"y aún figura como pendiente. Si ya pagaste, ignora este mensaje."
        )
    else:
        subject = f"Factura {number} con {offset_days} días de mora"
        intro = (
            f"la factura <b>{esc(number)}</b> por <b>{amount}</b> lleva <b>{offset_days} días</b> vencida. "
            f"Te agradecemos ponerte al día o responder este correo si necesitas un acuerdo de pago."
        )
    button = (
        f'<p><a href="{esc(payment_link)}" style="background:#7c3aed;color:#fff;padding:10px 18px;'
        f'border-radius:6px;text-decoration:none">Pagar {amount}</a></p>'
        if payment_link else ""
    )
    body = (
        f"<p>Hola {esc(client_name)},</p><p>{esc(business_name)} {intro}</p>{button}"
        f'<p style="color:#888;font-size:12px">Mensaje automático enviado por InvoiceChaser en nombre de '
        f"{esc(business_name)}. Para dejar de recibir estos mensajes o ejercer tus derechos sobre tus datos "
        f"personales (Ley 1581 de 2012), responde a este correo.</p>"
    )
    return subject, body
