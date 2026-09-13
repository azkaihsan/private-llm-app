"""Tests for new features: profile update, password change, chat search."""
import os
import time
import uuid
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'http://localhost:8001').rstrip('/')
API = f"{BASE_URL}/api"

ADMIN_EMAIL = "admin@openwebui.local"
ADMIN_PASSWORD = "Admin@123"

UNIQUE = f"zebrafish{int(time.time())}"


@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(f"{API}/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    assert r.status_code == 200, r.text
    return r.json()["token"]


@pytest.fixture(scope="module")
def test_user():
    """Signup a fresh regular test user for isolation."""
    email = f"test_new_{int(time.time())}_{uuid.uuid4().hex[:6]}@example.com"
    password = "Initial@123"
    r = requests.post(f"{API}/auth/signup", json={"name": "Feature Tester", "email": email, "password": password})
    assert r.status_code == 200, r.text
    data = r.json()
    yield {"email": email, "password": password, "token": data["token"], "id": data["user"]["id"]}
    # cleanup via admin
    ad = requests.post(f"{API}/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}).json()["token"]
    requests.delete(f"{API}/admin/users/{data['user']['id']}", headers={"Authorization": f"Bearer {ad}"})


# ============ Profile update ============
class TestProfile:
    def test_update_profile_no_token(self):
        r = requests.put(f"{API}/auth/profile", json={"name": "X"})
        assert r.status_code == 401

    def test_update_profile_empty(self, test_user):
        h = {"Authorization": f"Bearer {test_user['token']}"}
        r = requests.put(f"{API}/auth/profile", json={"name": "   "}, headers=h)
        assert r.status_code == 400

    def test_update_profile_success(self, test_user):
        h = {"Authorization": f"Bearer {test_user['token']}"}
        r = requests.put(f"{API}/auth/profile", json={"name": "Renamed User"}, headers=h)
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == "Renamed User"
        assert "password_hash" not in data
        # Verify persisted
        me = requests.get(f"{API}/auth/me", headers=h).json()
        assert me["name"] == "Renamed User"


# ============ Password change ============
class TestPassword:
    def test_wrong_current(self, test_user):
        h = {"Authorization": f"Bearer {test_user['token']}"}
        r = requests.put(f"{API}/auth/password", json={"current_password": "WRONG", "new_password": "NewPass@123"}, headers=h)
        assert r.status_code == 400
        assert "incorrect" in r.json()["detail"].lower()

    def test_short_new(self, test_user):
        h = {"Authorization": f"Bearer {test_user['token']}"}
        r = requests.put(f"{API}/auth/password", json={"current_password": test_user["password"], "new_password": "abc"}, headers=h)
        assert r.status_code == 400

    def test_change_and_relogin(self, test_user):
        h = {"Authorization": f"Bearer {test_user['token']}"}
        new_pw = "NewPass@123"
        r = requests.put(f"{API}/auth/password", json={"current_password": test_user["password"], "new_password": new_pw}, headers=h)
        assert r.status_code == 200
        assert r.json()["success"] is True
        # login with new
        r2 = requests.post(f"{API}/auth/login", json={"email": test_user["email"], "password": new_pw})
        assert r2.status_code == 200
        # revert
        h2 = {"Authorization": f"Bearer {r2.json()['token']}"}
        r3 = requests.put(f"{API}/auth/password", json={"current_password": new_pw, "new_password": test_user["password"]}, headers=h2)
        assert r3.status_code == 200


# ============ Chat search ============
class TestChatSearch:
    @pytest.fixture(scope="class")
    def seeded(self, admin_token):
        h = {"Authorization": f"Bearer {admin_token}"}
        # Import a chat containing UNIQUE word in messages but not title
        payload = {
            "version": "1.0",
            "chat": {"title": "Plain Title", "model": "gpt-4o"},
            "messages": [
                {"role": "user", "content": f"Hello, tell me about a {UNIQUE} in the ocean"},
                {"role": "assistant", "content": f"A {UNIQUE} is a small striped fish."},
            ],
        }
        r = requests.post(f"{API}/chats/import", json=payload, headers=h)
        assert r.status_code == 200
        cid = r.json()["chat_id"]
        # Also import an archived chat with UNIQUE, to verify exclusion
        arch = requests.post(f"{API}/chats/import", json={
            "version": "1.0",
            "chat": {"title": "Arch", "model": "gpt-4o"},
            "messages": [{"role": "user", "content": f"archived {UNIQUE} mention"}],
        }, headers=h).json()["chat_id"]
        requests.put(f"{API}/chats/{arch}/archive", headers=h)
        yield {"chat_id": cid, "archived_id": arch}
        requests.delete(f"{API}/chats/{cid}", headers=h)
        requests.put(f"{API}/chats/{arch}/unarchive", headers=h)
        requests.delete(f"{API}/chats/{arch}", headers=h)

    def test_short_query_returns_empty(self, admin_token):
        h = {"Authorization": f"Bearer {admin_token}"}
        r = requests.get(f"{API}/chats/search", params={"q": "a"}, headers=h)
        assert r.status_code == 200
        assert r.json() == []

    def test_no_auth(self):
        r = requests.get(f"{API}/chats/search", params={"q": UNIQUE})
        assert r.status_code == 401

    def test_search_finds_and_excludes_archived(self, admin_token, seeded):
        h = {"Authorization": f"Bearer {admin_token}"}
        r = requests.get(f"{API}/chats/search", params={"q": UNIQUE}, headers=h)
        assert r.status_code == 200
        results = r.json()
        chat_ids = [x["chat_id"] for x in results]
        assert seeded["chat_id"] in chat_ids
        assert seeded["archived_id"] not in chat_ids
        # snippet, role, count present
        entry = next(x for x in results if x["chat_id"] == seeded["chat_id"])
        assert UNIQUE.lower() in entry["snippet"].lower()
        assert entry["role"] in ("user", "assistant")
        assert entry["count"] >= 2

    def test_case_insensitive(self, admin_token, seeded):
        h = {"Authorization": f"Bearer {admin_token}"}
        r = requests.get(f"{API}/chats/search", params={"q": UNIQUE.upper()}, headers=h)
        assert r.status_code == 200
        assert any(x["chat_id"] == seeded["chat_id"] for x in r.json())

    def test_other_user_isolation(self, admin_token, seeded, test_user):
        h = {"Authorization": f"Bearer {test_user['token']}"}
        r = requests.get(f"{API}/chats/search", params={"q": UNIQUE}, headers=h)
        assert r.status_code == 200
        assert all(x["chat_id"] != seeded["chat_id"] for x in r.json())
