# Iteration 5: email-keyed login lockout retest + quick authz regression
import os
import uuid
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL').rstrip('/')
API = f"{BASE_URL}/api"
ADMIN = {"email": "admin@openwebui.local", "password": "Admin@123"}


def h(tok):
    return {"Authorization": f"Bearer {tok}"}


def signup():
    email = f"test_t5_{uuid.uuid4().hex[:8]}@example.com"
    r = requests.post(f"{API}/auth/signup", json={"name": "TEST t5", "email": email, "password": "Passw0rd!"})
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["user"]["role"] == "user"
    return {"email": email, "password": "Passw0rd!", "token": d["token"], "id": d["user"]["id"]}


@pytest.fixture(scope="module")
def admin():
    r = requests.post(f"{API}/auth/login", json=ADMIN)
    assert r.status_code == 200, r.text
    return r.json()["token"]


@pytest.fixture(scope="module")
def created(admin):
    lst = []
    yield lst
    for u in lst:
        requests.delete(f"{API}/admin/users/{u['id']}", headers=h(admin))


# Lockout keyed by email (independent of rotating ingress IPs)
class TestLockout:
    def test_5_fails_then_429_even_with_correct_password(self, created):
        u = signup(); created.append(u)
        for i in range(5):
            r = requests.post(f"{API}/auth/login", json={"email": u["email"], "password": "wrong!!"})
            assert r.status_code == 401, (i, r.status_code, r.text)
        r = requests.post(f"{API}/auth/login", json={"email": u["email"], "password": u["password"]})
        assert r.status_code == 429, r.text
        assert "Too many failed attempts" in r.json()["detail"]
        # uppercase email variant also locked (normalized)
        r = requests.post(f"{API}/auth/login", json={"email": u["email"].upper(), "password": u["password"]})
        assert r.status_code == 429

    def test_success_clears_counter(self, created):
        u = signup(); created.append(u)
        for _ in range(3):
            assert requests.post(f"{API}/auth/login", json={"email": u["email"], "password": "bad!!!"}).status_code == 401
        r = requests.post(f"{API}/auth/login", json={"email": u["email"], "password": u["password"]})
        assert r.status_code == 200 and r.json()["user"]["email"] == u["email"]
        for _ in range(3):
            r = requests.post(f"{API}/auth/login", json={"email": u["email"], "password": "bad!!!"})
            assert r.status_code == 401, r.status_code

    def test_lockout_does_not_affect_other_user(self, created):
        u = signup(); created.append(u)
        r = requests.post(f"{API}/auth/login", json={"email": u["email"], "password": u["password"]})
        assert r.status_code == 200


# Quick regression
class TestRegression:
    def test_admin_get_chats(self, admin):
        r = requests.get(f"{API}/chats", headers=h(admin))
        assert r.status_code == 200 and isinstance(r.json(), list)

    def test_user_put_settings_forbidden(self, created):
        u = signup(); created.append(u)
        r = requests.put(f"{API}/settings", json={"appName": "X"}, headers=h(u["token"]))
        assert r.status_code == 403
