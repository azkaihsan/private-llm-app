"""Backend tests for OpenWebUI clone: auth, admin CRUD, RBAC, chat isolation."""
import os
import time
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://chat-admin-panel-11.preview.emergentagent.com').rstrip('/')
API = f"{BASE_URL}/api"

ADMIN_EMAIL = "admin@openwebui.local"
ADMIN_PASSWORD = "Admin@123"

TS = str(int(time.time()))
USER_A_EMAIL = f"test_usera_{TS}@example.com"
USER_B_EMAIL = f"test_userb_{TS}@example.com"
USER_PWD = "Test@1234"

state = {}


@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(f"{API}/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["user"]["role"] == "admin"
    assert "password_hash" not in data["user"]
    return data["token"]


def auth(t):
    return {"Authorization": f"Bearer {t}"}


# ===== Auth =====
def test_login_admin_ok(admin_token):
    assert admin_token

def test_auth_me(admin_token):
    r = requests.get(f"{API}/auth/me", headers=auth(admin_token))
    assert r.status_code == 200
    j = r.json()
    assert j["email"] == ADMIN_EMAIL
    assert j["role"] == "admin"
    assert "password_hash" not in j

def test_login_wrong_password():
    r = requests.post(f"{API}/auth/login", json={"email": ADMIN_EMAIL, "password": "wrong"})
    assert r.status_code == 401

def test_signup_user_a():
    r = requests.post(f"{API}/auth/signup", json={"name": "User A", "email": USER_A_EMAIL, "password": USER_PWD})
    assert r.status_code == 200, r.text
    j = r.json()
    assert j["user"]["role"] == "user"
    state["user_a_token"] = j["token"]
    state["user_a_id"] = j["user"]["id"]

def test_signup_user_b():
    r = requests.post(f"{API}/auth/signup", json={"name": "User B", "email": USER_B_EMAIL, "password": USER_PWD})
    assert r.status_code == 200
    j = r.json()
    assert j["user"]["role"] == "user"
    state["user_b_token"] = j["token"]
    state["user_b_id"] = j["user"]["id"]

def test_signup_duplicate_email():
    r = requests.post(f"{API}/auth/signup", json={"name": "Dup", "email": USER_A_EMAIL, "password": USER_PWD})
    assert r.status_code == 400


# ===== RBAC =====
def test_no_token_chats_401():
    r = requests.get(f"{API}/chats")
    assert r.status_code == 401

def test_no_token_connections_401():
    r = requests.get(f"{API}/connections")
    assert r.status_code == 401

def test_no_token_admin_users_401():
    r = requests.get(f"{API}/admin/users")
    assert r.status_code == 401

def test_user_role_admin_users_403():
    r = requests.get(f"{API}/admin/users", headers=auth(state["user_a_token"]))
    assert r.status_code == 403

def test_user_role_connections_get_403():
    r = requests.get(f"{API}/connections", headers=auth(state["user_a_token"]))
    assert r.status_code == 403

def test_user_role_connections_put_403():
    r = requests.put(f"{API}/connections", headers=auth(state["user_a_token"]), json={})
    assert r.status_code == 403


# ===== Admin CRUD =====
def test_admin_list_users(admin_token):
    r = requests.get(f"{API}/admin/users", headers=auth(admin_token))
    assert r.status_code == 200
    users = r.json()
    emails = [u["email"] for u in users]
    assert ADMIN_EMAIL in emails
    assert USER_A_EMAIL in emails

def test_admin_create_user(admin_token):
    email = f"test_created_{TS}@example.com"
    r = requests.post(f"{API}/admin/users", headers=auth(admin_token),
                      json={"name": "Created", "email": email, "password": USER_PWD, "role": "user"})
    assert r.status_code == 200, r.text
    j = r.json()
    assert j["email"] == email
    state["created_user_id"] = j["id"]
    state["created_user_email"] = email

def test_admin_update_user_password_and_login(admin_token):
    new_pwd = "NewPass@2345"
    r = requests.put(f"{API}/admin/users/{state['created_user_id']}", headers=auth(admin_token),
                     json={"name": "Created2", "role": "user", "password": new_pwd})
    assert r.status_code == 200
    # Login with new password
    r2 = requests.post(f"{API}/auth/login", json={"email": state["created_user_email"], "password": new_pwd})
    assert r2.status_code == 200

def test_admin_delete_created_user(admin_token):
    r = requests.delete(f"{API}/admin/users/{state['created_user_id']}", headers=auth(admin_token))
    assert r.status_code == 200

def test_admin_cannot_delete_self(admin_token):
    me = requests.get(f"{API}/auth/me", headers=auth(admin_token)).json()
    r = requests.delete(f"{API}/admin/users/{me['id']}", headers=auth(admin_token))
    assert r.status_code == 400


# ===== Chat isolation =====
def test_chat_isolation():
    ra = requests.post(f"{API}/chats", headers=auth(state["user_a_token"]),
                       json={"title": "A chat", "model": "gpt-4o"})
    assert ra.status_code == 200
    chat_id = ra.json()["id"]

    # User B should not see it
    rb = requests.get(f"{API}/chats", headers=auth(state["user_b_token"]))
    assert rb.status_code == 200
    assert all(c["id"] != chat_id for c in rb.json())

    # User B GET by id -> 404
    rb2 = requests.get(f"{API}/chats/{chat_id}", headers=auth(state["user_b_token"]))
    assert rb2.status_code == 404

    # cleanup
    requests.delete(f"{API}/chats/{chat_id}", headers=auth(state["user_a_token"]))


# ===== Cleanup test users =====
def test_cleanup(admin_token):
    users = requests.get(f"{API}/admin/users", headers=auth(admin_token)).json()
    for u in users:
        if u["email"].startswith("test_") or u["email"] in (USER_A_EMAIL, USER_B_EMAIL):
            requests.delete(f"{API}/admin/users/{u['id']}", headers=auth(admin_token))
