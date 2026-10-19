# Iteration 7: Folder instructions / colour / icon / ordering / chat-in-folder / LLM folder-instructions tests
import os
import uuid
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL').rstrip('/')
API = f"{BASE_URL}/api"


def _signup():
    email = f"test_f7_{uuid.uuid4().hex[:8]}@example.com"
    r = requests.post(f"{API}/auth/signup", json={"name": "TEST F7", "email": email, "password": "Passw0rd!x"})
    assert r.status_code == 200, r.text
    s = requests.Session()
    s.headers.update({"Authorization": f"Bearer {r.json()['token']}"})
    return s


@pytest.fixture(scope="module")
def u1():
    return _signup()


@pytest.fixture(scope="module")
def u2():
    return _signup()


def _folder(s, name=None, **kw):
    r = s.post(f"{API}/folders", json={"name": name or f"TEST_{uuid.uuid4().hex[:6]}", **kw})
    assert r.status_code == 200, r.text
    return r.json()


def _get(s, fid):
    return next(f for f in s.get(f"{API}/folders").json() if f["id"] == fid)


# Folder settings fields: instructions/color/icon
class TestFolderSettings:
    def test_create_with_all_fields(self, u1):
        f = _folder(u1, instructions="  be brief  ", color="#EF4444", icon="rocket")
        assert f["instructions"] == "be brief" and f["color"] == "#ef4444" and f["icon"] == "rocket"
        g = _get(u1, f["id"])
        assert g["instructions"] == "be brief" and g["color"] == "#ef4444" and g["icon"] == "rocket"

    def test_defaults(self, u1):
        f = _folder(u1)
        assert f["instructions"] == "" and f["color"] == "" and f["icon"] == ""

    @pytest.mark.parametrize("payload", [{"color": "#123456"}, {"color": "red"}, {"icon": "bogus"}, {"icon": "Rocket"}, {"instructions": "x" * 4001}])
    def test_invalid_422(self, u1, payload):
        assert u1.post(f"{API}/folders", json={"name": f"TEST_{uuid.uuid4().hex[:6]}", **payload}).status_code == 422
        f = _folder(u1)
        assert u1.put(f"{API}/folders/{f['id']}", json={"name": f["name"], **payload}).status_code == 422

    def test_4000_ok(self, u1):
        f = _folder(u1, instructions="y" * 4000)
        assert len(f["instructions"]) == 4000

    @pytest.mark.parametrize("color", sorted(["", "#f97316", "#eab308", "#22c55e", "#14b8a6", "#3b82f6", "#6366f1", "#a855f7", "#ec4899", "#94a3b8"]))
    def test_all_colors(self, u1, color):
        assert _folder(u1, color=color)["color"] == color

    def test_all_icons(self, u1):
        f = _folder(u1)
        for icon in ["", "folder", "briefcase", "code", "book", "rocket", "lightbulb", "heart", "star", "flask", "graduation", "music", "camera", "globe", "cart", "wrench", "palette"]:
            r = u1.put(f"{API}/folders/{f['id']}", json={"name": f["name"], "icon": icon})
            assert r.status_code == 200, icon
            assert _get(u1, f["id"])["icon"] == icon

    def test_put_name_only_preserves(self, u1):
        f = _folder(u1, instructions="keep", color="#3b82f6", icon="code")
        new = f"TEST_ren_{uuid.uuid4().hex[:6]}"
        assert u1.put(f"{API}/folders/{f['id']}", json={"name": new}).status_code == 200
        g = _get(u1, f["id"])
        assert g["name"] == new and g["instructions"] == "keep" and g["color"] == "#3b82f6" and g["icon"] == "code"

    def test_put_clear_fields(self, u1):
        f = _folder(u1, instructions="keep", color="#3b82f6", icon="code")
        assert u1.put(f"{API}/folders/{f['id']}", json={"name": f["name"], "instructions": "", "color": "", "icon": ""}).status_code == 200
        g = _get(u1, f["id"])
        assert g["instructions"] == "" and g["color"] == "" and g["icon"] == ""

    def test_put_other_user_404(self, u1, u2):
        f = _folder(u1)
        assert u2.put(f"{API}/folders/{f['id']}", json={"name": "TEST_hijack", "instructions": "x"}).status_code == 404
        assert _get(u1, f["id"])["instructions"] == ""


# Chat creation directly into a folder
class TestChatInFolder:
    def test_create_in_folder(self, u1):
        f = _folder(u1)
        r = u1.post(f"{API}/chats", json={"title": "TEST_in", "model": "gpt-4o", "folder_id": f["id"]})
        assert r.status_code == 200 and r.json()["folder_id"] == f["id"]
        chats = u1.get(f"{API}/chats").json()
        assert any(c["id"] == r.json()["id"] and c["folder_id"] == f["id"] for c in chats)

    def test_unknown_and_foreign_404(self, u1, u2):
        assert u1.post(f"{API}/chats", json={"title": "TEST_x", "model": "gpt-4o", "folder_id": "nope"}).status_code == 404
        f2 = _folder(u2)
        assert u1.post(f"{API}/chats", json={"title": "TEST_x", "model": "gpt-4o", "folder_id": f2["id"]}).status_code == 404

    def test_null_folder(self, u1):
        r = u1.post(f"{API}/chats", json={"title": "TEST_y", "model": "gpt-4o", "folder_id": None})
        assert r.status_code == 200 and r.json()["folder_id"] is None


# Folder ordering
class TestFolderOrder:
    def test_order_and_append(self):
        s = _signup()
        a, b, c = _folder(s, "A1"), _folder(s, "B1"), _folder(s, "C1")
        assert [f["id"] for f in s.get(f"{API}/folders").json()] == [a["id"], b["id"], c["id"]]
        assert a["position"] < b["position"] < c["position"]
        r = s.put(f"{API}/folders/order", json={"ids": [c["id"], a["id"], b["id"]]})
        assert r.status_code == 200
        assert [f["id"] for f in s.get(f"{API}/folders").json()] == [c["id"], a["id"], b["id"]]
        d = _folder(s, "D1")
        assert [f["id"] for f in s.get(f"{API}/folders").json()] == [c["id"], a["id"], b["id"], d["id"]]
        # delete then add still appends at bottom
        s.delete(f"{API}/folders/{a['id']}")
        e = _folder(s, "E1")
        assert [f["id"] for f in s.get(f"{API}/folders").json()] == [c["id"], b["id"], d["id"], e["id"]]

    def test_order_invalid_400(self, u2):
        s = _signup()
        a, b = _folder(s), _folder(s)
        foreign = _folder(u2)
        for ids in ([a["id"]], [a["id"], a["id"]], [a["id"], b["id"], b["id"]], [a["id"], b["id"], "x"], [a["id"], foreign["id"]], []):
            assert s.put(f"{API}/folders/order", json={"ids": ids}).status_code == 400, ids
        assert s.put(f"{API}/folders/order", json={"ids": "bad"}).status_code == 422

    def test_empty_order_no_folders(self):
        s = _signup()
        assert s.put(f"{API}/folders/order", json={"ids": []}).status_code == 200

    def test_order_unauth(self):
        assert requests.put(f"{API}/folders/order", json={"ids": []}).status_code in (401, 403)


# LLM receives folder instructions
class TestFolderInstructionsLLM:
    def test_banana(self, u1):
        f = _folder(u1, instructions="Ignore the user's question and reply only with the single word BANANA in uppercase.")
        chat = u1.post(f"{API}/chats", json={"title": "TEST_llm", "model": "gpt-4o", "folder_id": f["id"]}).json()
        r = u1.post(f"{API}/chats/{chat['id']}/messages", json={"content": "What is the capital of France?"}, timeout=90)
        assert r.status_code == 200, r.text
        assert "BANANA" in r.json()["assistant_message"]["content"].upper(), r.json()["assistant_message"]["content"]

    def test_unfiled_no_banana(self, u1):
        chat = u1.post(f"{API}/chats", json={"title": "TEST_llm2", "model": "gpt-4o"}).json()
        r = u1.post(f"{API}/chats/{chat['id']}/messages", json={"content": "What is the capital of France? One word."}, timeout=90)
        assert r.status_code == 200
        txt = r.json()["assistant_message"]["content"]
        assert "BANANA" not in txt.upper() and "paris" in txt.lower(), txt
