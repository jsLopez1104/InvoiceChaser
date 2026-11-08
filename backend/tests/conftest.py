import os
import tempfile

_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
os.environ["DATABASE_URL"] = f"sqlite:///{_db.name}"
os.environ["ENVIRONMENT"] = "test"
os.environ["DEMO_MODE"] = "true"
os.environ["RESEND_API_KEY"] = ""
os.environ["WOMPI_PUBLIC_KEY"] = ""

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlmodel import Session, SQLModel  # noqa: E402

from app.db import engine  # noqa: E402
from app.limiter import limiter  # noqa: E402
from app.main import app  # noqa: E402

limiter.enabled = False


@pytest.fixture
def client():
    SQLModel.metadata.drop_all(engine)
    with TestClient(app) as c:  # el lifespan crea tablas y el usuario demo
        yield c


@pytest.fixture
def session():
    with Session(engine) as s:
        yield s


def register_and_login(c: TestClient, email="ana@example.com", password="secreto123") -> dict:
    r = c.post("/auth/register", json={
        "email": email, "password": password, "full_name": "Ana Pérez",
        "business_name": "Ana Fletes", "accept_privacy_policy": True,
    })
    assert r.status_code == 201, r.text
    r = c.post("/auth/login", data={"username": email, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture
def auth(client):
    return register_and_login(client)
