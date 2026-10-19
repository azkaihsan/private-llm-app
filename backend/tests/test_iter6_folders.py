# Iteration 6: Chat Folders API tests (CRUD, validation, isolation, chat move, delete-unfile)
import os
import uuid
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL').rstrip('/')
API = f"{BASE_URL}/api"


def _signup():
    email = f"test_fold_{uuid.uuid4().hex[:8]}@example.com"
    r = requests.post(f"{API}/auth/signup", json={"name": "TEST Folder", "email": email, "password": "Passw0rd!x"})
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


def _chat(s, title="TEST_chat"):
    r = s.post(f"{API}/chats", json={"title": title, "model": "gpt-4o"})
    assert r.status_code == 200, r.text
    assert r.json()["folder_id"] is None
    return r.json()["id"]


# Folder CRUD + validation
class TestFolderCRUD:
    def test_unauth(self):
        assert requests.get(f"{API}/folders").status_code in (401, 403)

    def test_create_list(self, u1):
        r = u1.post(f"{API}/folders", json={"name": "  Proj   Alpha  "})
        assert r.status_code == 200
        f = r.json()
        assert f["name"] == "Proj Alpha" and "_id" not in f and "user_id" in f
        lst = u1.get(f"{API}/folders").json()
        assert any(x["id"] == f["id"] and x["name"] == "Proj Alpha" for x in lst)

    def test_duplicate_case_insensitive(self, u1):
        u1.post(f"{API}/folders", json={"name": "DupName"})
        r = u1.post(f"{API}/folders", json={"name": "  dupname "})
        assert r.status_code == 409

    @pytest.mark.parametrize("name", ["", "   ", "x" * 61])
    def test_invalid_names(self, u1, name):
        assert u1.post(f"{API}/folders", json={"name": name}).status_code == 422

    def test_60_chars_ok(self, u1):
        assert u1.post(f"{API}/folders", json={"name": "y" * 60}).status_code == 200

    def test_regex_special_chars(self, u1):
        r = u1.post(f"{API}/folders", json={"name": "a.*(b"})
        assert r.status_code == 200
        r2 = u1.post(f"{API}/folders", json={"name": "aXXXb"})
        assert r2.status_code == 200

    def test_rename(self, u1):
        fid = u1.post(f"{API}/folders", json={"name": "ToRename"}).json()["id"]
        r = u1.put(f"{API}/folders/{fid}", json={"name": " Renamed   X "})
        assert r.status_code == 200
        names = {x["id"]: x["name"] for x in u1.get(f"{API}/folders").json()}
        assert names[fid] == "Renamed X"
        # rename to own name with different case allowed (exclude self)
        assert u1.put(f"{API}/folders/{fid}", json={"name": "renamed x"}).status_code == 200
        # rename to another existing name -> 409
        assert u1.put(f"{API}/folders/{fid}", json={"name": "dupname"}).status_code == 409

    def test_rename_delete_unknown(self, u1):
        assert u1.put(f"{API}/folders/nope", json={"name": "Zzz"}).status_code == 404
        assert u1.delete(f"{API}/folders/nope").status_code == 404


# Chat move + isolation
class TestFolderMoveIsolation:
    def test_move_and_unmove(self, u1):
        fid = u1.post(f"{API}/folders", json={"name": "MoveF"}).json()["id"]
        cid = _chat(u1)
        assert u1.put(f"{API}/chats/{cid}/folder", json={"folder_id": fid}).status_code == 200
        c = next(x for x in u1.get(f"{API}/chats").json() if x["id"] == cid)
        assert c["folder_id"] == fid
        assert u1.put(f"{API}/chats/{cid}/folder", json={"folder_id": None}).status_code == 200
        c = next(x for x in u1.get(f"{API}/chats").json() if x["id"] == cid)
        assert c["folder_id"] is None
        # empty body -> null
        assert u1.put(f"{API}/chats/{cid}/folder", json={}).status_code == 200

    def test_move_unknown_folder(self, u1):
        cid = _chat(u1)
        assert u1.put(f"{API}/chats/{cid}/folder", json={"folder_id": "nope"}).status_code == 404

    def test_move_unknown_chat(self, u1):
        assert u1.put(f"{API}/chats/nope/folder", json={"folder_id": None}).status_code == 404

    def test_isolation(self, u1, u2):
        fid = u1.post(f"{API}/folders", json={"name": "Private"}).json()["id"]
        cid1 = _chat(u1)
        cid2 = _chat(u2)
        assert all(f["id"] != fid for f in u2.get(f"{API}/folders").json())
        assert u2.put(f"{API}/folders/{fid}", json={"name": "Hacked"}).status_code == 404
        assert u2.delete(f"{API}/folders/{fid}").status_code == 404
        assert u2.put(f"{API}/chats/{cid2}/folder", json={"folder_id": fid}).status_code == 404
        assert u2.put(f"{API}/chats/{cid1}/folder", json={"folder_id": None}).status_code == 404
        # same name allowed for different user
        assert u2.post(f"{API}/folders", json={"name": "Private"}).status_code == 200
        names = [f["name"] for f in u1.get(f"{API}/folders").json()]
        assert "Private" in names and "Hacked" not in names

    def test_delete_folder_unfiles_chats(self, u1):
        fid = u1.post(f"{API}/folders", json={"name": "DelMe"}).json()["id"]
        a, b = _chat(u1), _chat(u1)
        for c in (a, b):
            u1.put(f"{API}/chats/{c}/folder", json={"folder_id": fid})
        u1.put(f"{API}/chats/{b}/archive")
        r = u1.delete(f"{API}/folders/{fid}")
        assert r.status_code == 200
        assert r.json()["moved_chats"] == 2
        assert all(f["id"] != fid for f in u1.get(f"{API}/folders").json())
        ca = next(x for x in u1.get(f"{API}/chats").json() if x["id"] == a)
        assert ca["folder_id"] is None
        cb = next(x for x in u1.get(f"{API}/chats/archived").json() if x["id"] == b)
        assert cb.get("folder_id") is None

    def test_pin_keeps_folder(self, u1):
        fid = u1.post(f"{API}/folders", json={"name": "PinF"}).json()["id"]
        cid = _chat(u1)
        u1.put(f"{API}/chats/{cid}/folder", json={"folder_id": fid})
        u1.put(f"{API}/chats/{cid}/pin")
        c = next(x for x in u1.get(f"{API}/chats").json() if x["id"] == cid)
        assert c["pinned"] is True and c["folder_id"] == fid
