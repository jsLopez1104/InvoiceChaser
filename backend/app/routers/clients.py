from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from ..db import get_session
from ..models import Client, Invoice, User
from ..schemas import ClientIn, ClientOut
from ..security import get_current_user

router = APIRouter(prefix="/clients", tags=["clients"])


def get_owned_client(client_id: int, user: User, session: Session) -> Client:
    client = session.get(Client, client_id)
    # Siempre filtrar por dueño: un usuario nunca ve clientes de otro.
    if client is None or client.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return client


def to_out(c: Client) -> ClientOut:
    return ClientOut(id=c.id, name=c.name, email=c.email, phone=c.phone, created_at=c.created_at)


@router.get("", response_model=list[ClientOut])
def list_clients(user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    rows = session.exec(select(Client).where(Client.owner_id == user.id).order_by(Client.name)).all()
    return [to_out(c) for c in rows]


@router.post("", response_model=ClientOut, status_code=201)
def create_client(data: ClientIn, user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    client = Client(owner_id=user.id, name=data.name.strip(), email=data.email.lower(), phone=data.phone)
    session.add(client)
    session.commit()
    session.refresh(client)
    return to_out(client)


@router.put("/{client_id}", response_model=ClientOut)
def update_client(client_id: int, data: ClientIn, user: User = Depends(get_current_user),
                  session: Session = Depends(get_session)):
    client = get_owned_client(client_id, user, session)
    client.name, client.email, client.phone = data.name.strip(), data.email.lower(), data.phone
    session.add(client)
    session.commit()
    session.refresh(client)
    return to_out(client)


@router.delete("/{client_id}", status_code=204)
def delete_client(client_id: int, user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    client = get_owned_client(client_id, user, session)
    if session.exec(select(Invoice).where(Invoice.client_id == client.id)).first():
        raise HTTPException(status_code=409, detail="El cliente tiene facturas; bórralas primero")
    session.delete(client)
    session.commit()
