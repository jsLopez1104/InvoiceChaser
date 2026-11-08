import copy
import time

from app.routers.webhooks import DEMO_EVENTS_SECRET
from app.services.payments import build_fake_event, integrity_signature
from tests.test_api import make_client, make_invoice


def test_integrity_signature_matches_wompi_formula():
    # SHA256("sk8-438k4-xmxm392-sn2m" + "2490000" + "COP" + "test_integrity_secret")
    import hashlib
    expected = hashlib.sha256(b"sk8-438k4-xmxm392-sn2m2490000COPtest_integrity_secret").hexdigest()
    assert integrity_signature("sk8-438k4-xmxm392-sn2m", 2490000, "test_integrity_secret") == expected


def test_webhook_marks_invoice_paid(client, auth):
    cl = make_client(client, auth)
    inv = make_invoice(client, auth, cl["id"], amount=250_000)
    event = build_fake_event(inv["payment_reference"], 25_000_000, DEMO_EVENTS_SECRET, int(time.time()))
    r = client.post("/webhooks/wompi", json=event)
    assert r.status_code == 200, r.text
    assert client.get(f"/invoices/{inv['id']}", headers=auth).json()["status"] == "paid"
    # Idempotente
    assert client.post("/webhooks/wompi", json=event).status_code == 200


def test_webhook_rejects_bad_signature(client, auth):
    cl = make_client(client, auth)
    inv = make_invoice(client, auth, cl["id"], amount=250_000)
    event = build_fake_event(inv["payment_reference"], 25_000_000, "otro-secreto", int(time.time()))
    assert client.post("/webhooks/wompi", json=event).status_code == 401
    assert client.get(f"/invoices/{inv['id']}", headers=auth).json()["status"] == "pending"


def test_webhook_rejects_tampered_amount(client, auth):
    cl = make_client(client, auth)
    inv = make_invoice(client, auth, cl["id"], amount=250_000)
    event = build_fake_event(inv["payment_reference"], 25_000_000, DEMO_EVENTS_SECRET, int(time.time()))
    tampered = copy.deepcopy(event)
    tampered["data"]["transaction"]["amount_in_cents"] = 100
    assert client.post("/webhooks/wompi", json=tampered).status_code == 401


def test_webhook_rejects_wrong_amount_even_if_signed(client, auth):
    cl = make_client(client, auth)
    inv = make_invoice(client, auth, cl["id"], amount=250_000)
    event = build_fake_event(inv["payment_reference"], 100, DEMO_EVENTS_SECRET, int(time.time()))
    assert client.post("/webhooks/wompi", json=event).status_code == 400


def test_demo_pay(client, auth):
    cl = make_client(client, auth)
    inv = make_invoice(client, auth, cl["id"])
    ref = inv["payment_reference"]
    assert client.get(f"/webhooks/demo/invoice/{ref}").json()["status"] == "pending"
    assert client.post(f"/webhooks/demo/pay/{ref}").status_code == 200
    assert client.get(f"/invoices/{inv['id']}", headers=auth).json()["status"] == "paid"
