from datetime import date, timedelta

from tests.conftest import register_and_login


def make_client(c, auth, **kw):
    data = {"name": "Cliente Uno", "email": "uno@example.com", **kw}
    r = c.post("/clients", json=data, headers=auth)
    assert r.status_code == 201, r.text
    return r.json()


def make_invoice(c, auth, client_id, days_from_due=0, amount=500_000, number="F-1"):
    due = date.today() - timedelta(days=days_from_due)
    r = c.post("/invoices", headers=auth, json={
        "client_id": client_id, "number": number, "amount_cop": amount,
        "issue_date": (due - timedelta(days=30)).isoformat(), "due_date": due.isoformat(),
    })
    assert r.status_code == 201, r.text
    return r.json()


def test_health_and_security_headers(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.headers["x-content-type-options"] == "nosniff"
    assert r.headers["x-frame-options"] == "DENY"


def test_register_requires_policy_acceptance(client):
    r = client.post("/auth/register", json={
        "email": "x@example.com", "password": "secreto123", "full_name": "X Y",
        "business_name": "XY", "accept_privacy_policy": False,
    })
    assert r.status_code == 422


def test_register_stores_policy_evidence(client, auth):
    me = client.get("/auth/me", headers=auth).json()
    assert me["accepted_policy_version"]
    assert me["accepted_policy_at"]


def test_duplicate_email_and_bad_login(client, auth):
    r = client.post("/auth/register", json={
        "email": "ana@example.com", "password": "secreto123", "full_name": "Ana",
        "business_name": "Ana", "accept_privacy_policy": True,
    })
    assert r.status_code == 409
    r = client.post("/auth/login", data={"username": "ana@example.com", "password": "malamala"})
    assert r.status_code == 401


def test_endpoints_require_auth(client):
    for path in ("/clients", "/invoices", "/dashboard", "/auth/me"):
        assert client.get(path).status_code == 401


def test_users_cannot_see_each_other(client, auth):
    cl = make_client(client, auth)
    inv = make_invoice(client, auth, cl["id"])
    other = register_and_login(client, email="otro@example.com")
    assert client.get("/clients", headers=other).json() == []
    assert client.get(f"/invoices/{inv['id']}", headers=other).status_code == 404
    # Tampoco puede facturarle a un cliente ajeno
    r = client.post("/invoices", headers=other, json={
        "client_id": cl["id"], "number": "X", "amount_cop": 1000,
        "issue_date": "2026-01-01", "due_date": "2026-01-31",
    })
    assert r.status_code == 404


def test_invoice_validation(client, auth):
    cl = make_client(client, auth)
    r = client.post("/invoices", headers=auth, json={
        "client_id": cl["id"], "number": "F", "amount_cop": -5,
        "issue_date": "2026-02-01", "due_date": "2026-01-01",
    })
    assert r.status_code == 422


def test_invoice_flow_and_dashboard(client, auth):
    cl = make_client(client, auth)
    inv = make_invoice(client, auth, cl["id"], days_from_due=5, amount=1_000_000)
    assert inv["is_overdue"] and inv["days_overdue"] == 5
    assert inv["payment_link"]
    d = client.get("/dashboard", headers=auth).json()
    assert d["total_overdue_cop"] == 1_000_000 and d["count_overdue"] == 1
    r = client.post(f"/invoices/{inv['id']}/mark-paid", headers=auth)
    assert r.json()["status"] == "paid" and r.json()["payment_link"] is None
    d = client.get("/dashboard", headers=auth).json()
    assert d["total_paid_cop"] == 1_000_000 and d["count_pending"] == 0


def test_delete_account_removes_everything(client, auth):
    cl = make_client(client, auth)
    make_invoice(client, auth, cl["id"])
    assert client.delete("/auth/me", headers=auth).status_code == 204
    assert client.get("/auth/me", headers=auth).status_code == 401


def test_demo_user_seeded(client):
    r = client.post("/auth/login", data={"username": "demo@invoicechaser.dev", "password": "demo12345"})
    assert r.status_code == 200
    h = {"Authorization": f"Bearer {r.json()['access_token']}"}
    d = client.get("/dashboard", headers=h).json()
    assert d["count_pending"] == 4 and d["count_paid"] == 2 and d["reminders_sent"] > 0
