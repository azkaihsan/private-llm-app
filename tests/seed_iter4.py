import os, requests, json, sys
API = os.environ['REACT_APP_BACKEND_URL'].rstrip('/') + '/api'
t = requests.post(f"{API}/auth/login", json={"email": "admin@openwebui.local", "password": "Admin@123"}).json()["token"]
H = {"Authorization": f"Bearer {t}"}
if len(sys.argv) > 1 and sys.argv[1] == 'clean':
    for c in requests.get(f"{API}/chats", headers=H).json() + requests.get(f"{API}/chats/archived", headers=H).json():
        if c["title"].startswith("TEST4"):
            requests.delete(f"{API}/chats/{c['id']}", headers=H); print("deleted", c["id"])
    sys.exit()
ids = []
for title, msg in [("TEST4 Alpha chat", "alpha message about penguins"), ("TEST4 Beta chat", "beta message about otters")]:
    r = requests.post(f"{API}/chats/import", json={"chat": {"title": title}, "messages": [{"role": "user", "content": msg}, {"role": "assistant", "content": "Reply " + msg}]}, headers=H)
    ids.append(r.json()["chat_id"])
print(json.dumps(ids))
