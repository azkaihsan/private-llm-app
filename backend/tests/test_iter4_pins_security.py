# Iteration 4: pins, validation, lockout, settings/connections authz & sanitization, chat isolation, import, search, LLM memory
import os
import uuid
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL').rstrip('/')
API = f"{BASE_URL}/api"
ADMIN = {"email": "admin@openwebui.local", "password": "Admin@123"}


def uniq(prefix="t4"):
    return f"test_{prefix}_{uuid.uuid4().hex[:8]}@example.com"


def signup(email=None, password="Passw0rd!", name="TEST User"):
    email = email or uniq()
    r = requests.post(f"{API}/auth/signup", json={"name": name, "email": email, "password": password})
    assert r.status_code == 200, r.text
    d = r.json()
    return {"email": email, "password": password, "token": d["token"], "id": d["user"]["id"]}


def h(tok):
    return {"Authorization": f"Bearer {tok}"}


@pytest.fixture(scope="module")
def admin():
    r = requests.post(f"{API}/auth/login", json=ADMIN)
    assert r.status_code == 200, r.text
    d = r.json()
    return {"token": d["token"], "id": d["user"]["id"]}


@pytest.fixture(scope="module")
def users(admin):
    created = []
    yield created
    for u in created:
        requests.delete(f"{API}/admin/users/{u['id']}", headers=h(admin["token"]))


def mk_user(users):
    u = signup()
    users.append(u)
    return u


# ---------- Pins ----------
class TestPins:
    def test_pin_unpin_archive(self, users):
        a = mk_user(users)
        b = mk_user(users)
        c = requests.post(f"{API}/chats", json={"title": "TEST pin chat"}, headers=h(a["token"])).json()
        assert c["pinned"] is False
        r = requests.put(f"{API}/chats/{c['id']}/pin", headers=h(a["token"]))
        assert r.status_code == 200 and r.json() == {"status": "ok"}
        lst = requests.get(f"{API}/chats", headers=h(a["token"])).json()
        row = next(x for x in lst if x["id"] == c["id"])
        assert row["pinned"] is True and row.get("pinned_at")
        r = requests.put(f"{API}/chats/{c['id']}/unpin", headers=h(a["token"]))
        assert r.status_code == 200
        row = next(x for x in requests.get(f"{API}/chats", headers=h(a["token"])).json() if x["id"] == c["id"])
        assert row["pinned"] is False
        # other user / unknown -> 404
        assert requests.put(f"{API}/chats/{c['id']}/pin", headers=h(b["token"])).status_code == 404
        assert requests.put(f"{API}/chats/nope-{uuid.uuid4()}/pin", headers=h(a["token"])).status_code == 404
        # archive unpins
        requests.put(f"{API}/chats/{c['id']}/pin", headers=h(a["token"]))
        assert requests.put(f"{API}/chats/{c['id']}/archive", headers=h(a["token"])).status_code == 200
        arch = requests.get(f"{API}/chats/archived", headers=h(a["token"])).json()
        row = next(x for x in arch if x["id"] == c["id"])
        assert row["archived"] is True and row["pinned"] is False


# ---------- Validation ----------
class TestValidation:
    @pytest.mark.parametrize("payload", [
        {"name": "", "email": "x1@example.com", "password": "Passw0rd"},
        {"name": "   ", "email": "x2@example.com", "password": "Passw0rd"},
        {"name": "a" * 61, "email": "x3@example.com", "password": "Passw0rd"},
        {"name": "Ok", "email": "noatsign.com", "password": "Passw0rd"},
        {"name": "Ok", "email": "x4@example.com", "password": "12345"},
    ])
    def test_signup_rejects(self, payload):
        assert requests.post(f"{API}/auth/signup", json=payload).status_code == 422

    def test_signup_lowercases_email(self, users):
        email = f"TEST_Upper_{uuid.uuid4().hex[:6]}@Example.COM"
        r = requests.post(f"{API}/auth/signup", json={"name": "TEST up", "email": email, "password": "Passw0rd"})
        assert r.status_code == 200
        d = r.json()
        users.append({"id": d["user"]["id"]})
        assert d["user"]["email"] == email.lower()

    def test_admin_create_rules(self, admin, users):
        t = h(admin["token"])
        base = {"name": "TEST a", "email": uniq("ac"), "password": "Passw0rd", "role": "user"}
        for bad in [{"name": "  "}, {"name": "b" * 61}, {"email": "bad"}, {"password": "123"}, {"role": "superuser"}]:
            assert requests.post(f"{API}/admin/users", json={**base, **bad}, headers=t).status_code == 422, bad
        r = requests.post(f"{API}/admin/users", json=base, headers=t)
        assert r.status_code == 200
        users.append({"id": r.json()["id"]})

    def test_admin_update_rules(self, admin, users):
        t = h(admin["token"])
        u = mk_user(users)
        r = requests.put(f"{API}/admin/users/{admin['id']}", json={"role": "user"}, headers=t)
        assert r.status_code == 400 and "own role" in r.json()["detail"]
        r = requests.put(f"{API}/admin/users/{u['id']}", json={"email": ADMIN["email"]}, headers=t)
        assert r.status_code == 400
        assert requests.put(f"{API}/admin/users/unknown-{uuid.uuid4()}", json={"name": "x"}, headers=t).status_code == 404
        assert requests.put(f"{API}/admin/users/{u['id']}", json={}, headers=t).status_code == 400
        me = requests.get(f"{API}/auth/me", headers=t).json()
        assert me["role"] == "admin"


# ---------- Lockout ----------
class TestLockout:
    def test_lockout_after_5(self, users):
        u = mk_user(users)
        for i in range(5):
            r = requests.post(f"{API}/auth/login", json={"email": u["email"], "password": "wrong!!"})
            assert r.status_code == 401, (i, r.status_code)
        r = requests.post(f"{API}/auth/login", json={"email": u["email"], "password": "wrong!!"})
        assert r.status_code == 429 and "Too many failed attempts" in r.json()["detail"]
        # correct password also blocked while locked
        r = requests.post(f"{API}/auth/login", json={"email": u["email"], "password": u["password"]})
        assert r.status_code == 429

    def test_success_clears_counter(self, users):
        u = mk_user(users)
        for _ in range(3):
            assert requests.post(f"{API}/auth/login", json={"email": u["email"], "password": "bad!!!"}).status_code == 401
        assert requests.post(f"{API}/auth/login", json={"email": u["email"], "password": u["password"]}).status_code == 200
        for _ in range(3):
            assert requests.post(f"{API}/auth/login", json={"email": u["email"], "password": "bad!!!"}).status_code == 401


# ---------- Settings ----------
class TestSettings:
    def test_settings_authz_and_sanitize(self, admin, users):
        u = mk_user(users)
        orig = requests.get(f"{API}/settings").json()
        assert requests.put(f"{API}/settings", json={"appName": "X"}).status_code == 401
        assert requests.put(f"{API}/settings", json={"appName": "X"}, headers=h(u["token"])).status_code == 403
        t = h(admin["token"])
        app_name = orig.get("appName", "Open WebUI")
        r = requests.put(f"{API}/settings", json={"$where": "1", "a.b": 1, "_id": "evil", "unknownKey": 1, "appName": app_name}, headers=t)
        assert r.status_code == 200
        g = requests.get(f"{API}/settings").json()
        for k in ("$where", "a.b", "unknownKey", "_id"):
            assert k not in g
        assert requests.put(f"{API}/settings", json={"fontSize": "abc"}, headers=t).status_code == 400
        old_fs = orig.get("fontSize", 15)
        assert requests.put(f"{API}/settings", json={"fontSize": 99}, headers=t).status_code == 200
        assert requests.get(f"{API}/settings").json()["fontSize"] == 24
        requests.put(f"{API}/settings", json={"fontSize": old_fs}, headers=t)

    def test_legacy_status_removed(self):
        assert requests.get(f"{API}/status").status_code in (404, 405)
        assert requests.post(f"{API}/status", json={"client_name": "x"}).status_code in (404, 405)


# ---------- Chat validation / isolation / import / search ----------
class TestChats:
    def test_validation_isolation(self, users):
        a = mk_user(users)
        b = mk_user(users)
        imp = requests.post(f"{API}/chats/import", json={"chat": {"title": "TEST imp"}, "messages": [
            {"role": "user", "content": "hello (.* literal"}, {"role": "assistant", "content": "hi"}]}, headers=h(a["token"]))
        assert imp.status_code == 200
        cid = imp.json()["chat_id"]
        assert imp.json()["chat"]["pinned"] is False
        for body in [{"content": ""}, {"content": "   "}, {"content": "x", "temperature": 3}]:
            assert requests.post(f"{API}/chats/{cid}/messages", json=body, headers=h(a["token"])).status_code == 422
        assert requests.put(f"{API}/chats/{cid}", json={"title": "   "}, headers=h(a["token"])).status_code == 422
        assert requests.delete(f"{API}/chats/{cid}", headers=h(b["token"])).status_code == 404
        g = requests.get(f"{API}/chats/{cid}", headers=h(a["token"])).json()
        assert len(g["messages"]) == 2
        # import rules
        assert requests.post(f"{API}/chats/import", json={"chat": {}, "messages": [{"role": "system", "content": "x"}]}, headers=h(a["token"])).status_code == 422
        many = [{"role": "user", "content": "m"}] * 2001
        assert requests.post(f"{API}/chats/import", json={"chat": {}, "messages": many}, headers=h(a["token"])).status_code == 422
        # search
        assert requests.get(f"{API}/chats/search", params={"q": "a"}, headers=h(a["token"])).json() == []
        r = requests.get(f"{API}/chats/search", params={"q": "z" * 300}, headers=h(a["token"]))
        assert r.status_code == 200
        r = requests.get(f"{API}/chats/search", params={"q": "(.*"}, headers=h(a["token"]))
        assert r.status_code == 200
        res = r.json()
        assert len(res) == 1 and res[0]["chat_id"] == cid


# ---------- Connections ----------
class TestConnections:
    def test_connections(self, admin):
        t = h(admin["token"])
        backup = requests.get(f"{API}/connections", headers=t).json()
        try:
            r = requests.post(f"{API}/connections/test", json={"provider": "openai", "apiKey": "emergent"}, headers=t, timeout=60)
            assert r.status_code == 200 and r.json()["status"] == "ok", r.text
            assert requests.post(f"{API}/connections/test", json={"provider": "unknown"}, headers=t).status_code == 400
            provs = dict(backup.get("providers", {}))
            provs["evilProvider"] = {"x": 1}
            r = requests.put(f"{API}/connections", json={"$bad": 1, "providers": provs}, headers=t)
            assert r.status_code == 200
            g = requests.get(f"{API}/connections", headers=t).json()
            assert "$bad" not in g and "evilProvider" not in g["providers"]
        finally:
            requests.put(f"{API}/connections", json={k: v for k, v in backup.items() if k in ("providers", "defaultModel", "modelParams", "disabledModels")}, headers=t)


# ---------- LLM memory ----------
class TestMemory:
    def test_history_passed(self, admin):
        t = h(admin["token"])
        c = requests.post(f"{API}/chats", json={"title": "TEST memory", "model": "gpt-4o"}, headers=t).json()
        try:
            r1 = requests.post(f"{API}/chats/{c['id']}/messages", json={"content": "My favourite colour is teal. Reply only OK."}, headers=t, timeout=90)
            assert r1.status_code == 200
            r2 = requests.post(f"{API}/chats/{c['id']}/messages", json={"content": "What is my favourite colour? Answer in one word."}, headers=t, timeout=90)
            assert r2.status_code == 200
            ans = r2.json()["assistant_message"]["content"]
            print("ASSISTANT:", ans)
            assert "teal" in ans.lower()
        finally:
            requests.delete(f"{API}/chats/{c['id']}", headers=t)
