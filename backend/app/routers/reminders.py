from datetime import datetime

from fastapi import APIRouter, Depends
from sqlmodel import Session

from ..config import get_settings
from ..db import get_session
from ..models import User
from ..security import get_current_user
from ..services.reminders import TZ, is_allowed_contact_time, process_reminders

router = APIRouter(prefix="/reminders", tags=["reminders"])
settings = get_settings()


@router.get("/rules")
def rules():
    now = datetime.now(TZ)
    return {
        "offsets": settings.reminder_offset_list,
        "min_days_between_overdue": settings.min_days_between_overdue,
        "allowed_hours": "Lun-Vie 7:00-19:00, Sáb 8:00-15:00 (hora Colombia). Domingos y festivos no.",
        "now_local": now.isoformat(),
        "allowed_now": is_allowed_contact_time(now),
    }


@router.post("/run")
def run_now(user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    """Ejecuta el motor ya mismo para las facturas del usuario (respeta horario y reglas)."""
    now = datetime.now(TZ)
    sent = process_reminders(session, now=now, owner_id=user.id)
    return {"sent": sent, "allowed_now": is_allowed_contact_time(now)}
