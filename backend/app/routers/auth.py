from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, delete, select

from ..config import get_settings
from ..db import get_session
from ..limiter import limiter
from ..models import Client, Invoice, ReminderLog, User
from ..schemas import RegisterIn, TokenOut, UserOut
from ..security import create_access_token, get_current_user, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()


def to_out(u: User) -> UserOut:
    return UserOut(id=u.id, email=u.email, full_name=u.full_name, business_name=u.business_name,
                   accepted_policy_version=u.accepted_policy_version, accepted_policy_at=u.accepted_policy_at)


@router.post("/register", response_model=UserOut, status_code=201)
@limiter.limit("5/minute")
def register(request: Request, data: RegisterIn, session: Session = Depends(get_session)):
    email = data.email.lower()
    if session.exec(select(User).where(User.email == email)).first():
        raise HTTPException(status_code=409, detail="Ese correo ya está registrado")
    user = User(
        email=email, full_name=data.full_name.strip(), business_name=data.business_name.strip(),
        password_hash=hash_password(data.password),
        accepted_policy_version=settings.privacy_policy_version,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return to_out(user)


@router.post("/login", response_model=TokenOut)
@limiter.limit("10/minute")
def login(request: Request, form: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.email == form.username.lower())).first()
    if not user or not verify_password(form.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Correo o contraseña incorrectos")
    return TokenOut(access_token=create_access_token(user.id))


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return to_out(user)


@router.delete("/me", status_code=204)
def delete_account(user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    """Derecho de supresión (Ley 1581): borra la cuenta y todos sus datos."""
    invoice_ids = session.exec(select(Invoice.id).where(Invoice.owner_id == user.id)).all()
    if invoice_ids:
        session.exec(delete(ReminderLog).where(ReminderLog.invoice_id.in_(invoice_ids)))
    session.exec(delete(Invoice).where(Invoice.owner_id == user.id))
    session.exec(delete(Client).where(Client.owner_id == user.id))
    session.delete(user)
    session.commit()
