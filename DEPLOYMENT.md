# Deployment Guide — Open WebUI Clone

This guide covers running the app locally, and deploying it to a staging or production
environment outside of the Emergent preview sandbox. The stack is:

- **Frontend**: React 19 (Create React App + CRACO), served on port `3000` in dev, built to static files for production
- **Backend**: FastAPI (Python), served by Uvicorn on port `8001`, all routes prefixed with `/api`
- **Database**: MongoDB (no ORM — Motor async driver, indexes created automatically on startup)

> **Fastest path**: if you're already on the Emergent platform, use the **Deploy** button in
> the chat input to publish this app — it provisions the frontend, backend and MongoDB for you
> and wires up HTTPS automatically. The steps below are for deploying this codebase to your
> **own** infrastructure (a VM, container host, or platforms like Railway/Render/Fly.io).

---

## 1. Prerequisites

| Requirement | Version used by this project | Notes |
|---|---|---|
| Node.js | 20.x | Required to build/run the React frontend |
| Yarn | 1.22.x (classic) | **Always use Yarn, not npm** — the lockfile is `yarn.lock` and npm can produce incompatible dependency trees |
| Python | 3.11.x | Backend runtime |
| pip | latest | Installs `backend/requirements.txt` |
| MongoDB | 7.x | Can be self-hosted, Docker, or a managed service (MongoDB Atlas) |
| Docker + docker-compose (optional) | 24.x+ | Only needed if you choose containerized deployment |

Confirm versions before you start:
```bash
node --version    # v20.x
yarn --version    # 1.22.x
python3 --version # 3.11.x
mongod --version  # v7.x (skip if using a managed/remote MongoDB)
```

No separate database migration tool is used — MongoDB is schemaless, and the backend creates
all required indexes and seeds the default admin user automatically on startup (see §4).

---

## 2. Environment Variables

Copy the example files and fill in real values. **Never commit the actual `.env` files.**

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

### Backend (`backend/.env`)

| Variable | Required | Description |
|---|---|---|
| `MONGO_URL` | Yes | MongoDB connection string, e.g. `mongodb://localhost:27017` or an Atlas SRV URI |
| `DB_NAME` | Yes | Database name the app will use/create |
| `CORS_ORIGINS` | Yes | Comma-separated list of allowed origins, e.g. `https://app.example.com`. Use `*` only for local dev |
| `EMERGENT_LLM_KEY` | Yes (for built-in providers) | Universal key for OpenAI/Anthropic/Gemini via `emergentintegrations`. Get/top up from your Emergent profile → **Manage Plan → Universal Key** |
| `JWT_SECRET` | Yes | Long random secret used to sign auth tokens. Generate with `openssl rand -hex 32`. There is **no fallback** — the server fails to start without it (by design) |
| `ADMIN_EMAIL` | Yes | Email for the default admin account, seeded idempotently on every startup |
| `ADMIN_PASSWORD` | Yes | Password for the default admin account (min 6 chars). Change this to a strong value before any non-local deployment |

### Frontend (`frontend/.env`)

| Variable | Required | Description |
|---|---|---|
| `REACT_APP_BACKEND_URL` | Yes | Public base URL of the backend (must be reachable from the browser), e.g. `https://api.example.com`. All frontend API calls are built as `${REACT_APP_BACKEND_URL}/api/...` |
| `WDS_SOCKET_PORT` | No | Webpack dev server hot-reload socket port (dev only, irrelevant to a production build) |
| `ENABLE_HEALTH_CHECK` | No | Set `true` only inside the Emergent sandbox; leave `false`/unset for self-hosted deployments |

> Bring-your-own-key providers (DeepSeek, Qwen, Grok, Perplexity, Amazon Bedrock, any
> OpenAI-compatible endpoint) do **not** need backend `.env` entries — their API keys/base URLs
> are entered by an admin at runtime in **Settings → Connections** and stored in MongoDB.

---

## 3. Local Deployment

```bash
# 1. MongoDB (skip if you already have one running / are using Atlas)
mongod --dbpath /path/to/data --port 27017 &

# 2. Backend
cd backend
pip install -r requirements.txt
cp .env.example .env   # then fill in real values
uvicorn server:app --host 0.0.0.0 --port 8001 --reload

# 3. Frontend (separate terminal)
cd frontend
yarn install
cp .env.example .env   # set REACT_APP_BACKEND_URL=http://localhost:8001
yarn start
```

Open `http://localhost:3000`. Sign in with `ADMIN_EMAIL` / `ADMIN_PASSWORD`, or sign up — the
first account ever created becomes admin.

**Health check**: `curl http://localhost:8001/api/` should return `{"message": "Open WebUI Clone API"}`.

---

## 4. Build, "Migration" and Startup Commands

### Build
```bash
# Frontend production build → static files in frontend/build/
cd frontend
yarn install --frozen-lockfile
yarn build

# Backend has no build step (interpreted Python); just install deps
cd backend
pip install -r requirements.txt
```

### "Migrations"
There is no schema-migration framework. On every backend startup (FastAPI `lifespan`), the app:
1. Creates MongoDB indexes if missing: unique index on `users.email` and `users.id`,
   compound index on `chats(user_id, archived, created_at)`, unique `chats.id`,
   `messages(chat_id, timestamp)`, unique `login_attempts.identifier`, unique `folders.id`,
   and `folders(user_id, created_at)`.
2. Seeds the default admin from `ADMIN_EMAIL` / `ADMIN_PASSWORD` if that email doesn't exist
   yet, or re-syncs its password/role if it does (idempotent — safe to run on every deploy).

No manual migration command is required when moving to a new environment; just point
`MONGO_URL`/`DB_NAME` at the target database and start the backend once.

### Startup (production-style, no hot reload)
```bash
# Backend — drop --reload, size workers to your CPU count
cd backend
uvicorn server:app --host 0.0.0.0 --port 8001 --workers 2

# Frontend — serve the static build (any static file server works)
cd frontend
npx serve -s build -l 3000
# or put frontend/build/ behind nginx/Caddy and reverse-proxy /api/* to the backend
```

### Process management
Use a supervisor (systemd, pm2, supervisord, or your container orchestrator) to keep both
processes running and auto-restart on crash. Example `systemd` unit for the backend:

```ini
[Unit]
Description=openwebui-clone-backend
After=network.target mongod.service

[Service]
WorkingDirectory=/opt/openwebui-clone/backend
EnvironmentFile=/opt/openwebui-clone/backend/.env
ExecStart=/opt/openwebui-clone/backend/venv/bin/uvicorn server:app --host 0.0.0.0 --port 8001 --workers 2
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### Docker (optional)
If you prefer containers, build two images (backend: `python:3.11-slim` + `pip install -r
requirements.txt` + `uvicorn` as the entrypoint; frontend: multi-stage `node:20` build →
`nginx:alpine` serving `frontend/build`) and run MongoDB as a third container or a managed
service. Pass all variables from §2 as container environment variables — do not bake secrets
into the image.

---

## 5. Staging vs. Production Checklist

| Item | Staging | Production |
|---|---|---|
| `MONGO_URL` | Dedicated staging DB/cluster | Dedicated prod cluster, backups enabled |
| `CORS_ORIGINS` | Staging frontend URL only | Exact production domain(s) only — never `*` |
| `JWT_SECRET` | Unique random value | **Different** unique random value from staging |
| `ADMIN_PASSWORD` | Strong, but can be shared with team | Strong, rotated, not reused from staging |
| `REACT_APP_BACKEND_URL` | Points at staging backend | Points at production backend, served over HTTPS |
| TLS | Optional (self-signed ok) | Required — terminate TLS at a reverse proxy/load balancer |
| Backend workers | 1 | 2+ depending on load, behind a process manager |
| Logs | stdout is fine | Ship `backend` stdout/stderr to centralized logging |

Both environments should run the **same** build artifacts/commands — only the `.env` values
and the reverse-proxy/TLS layer differ.

---

## 6. Health Check Verification

After deploying, verify in this order:

1. **MongoDB reachable**
   ```bash
   mongosh "$MONGO_URL" --eval "db.runCommand({ping:1})"
   ```
2. **Backend up and routed correctly**
   ```bash
   curl -s https://<your-backend-domain>/api/        # → {"message":"Open WebUI Clone API"}
   curl -s https://<your-backend-domain>/api/models   # → [...] list of models
   ```
3. **Admin login works**
   ```bash
   curl -s -X POST https://<your-backend-domain>/api/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email":"<ADMIN_EMAIL>","password":"<ADMIN_PASSWORD>"}'
   # → {"token": "...", "user": {...}}
   ```
4. **Frontend loads and talks to the backend** — open the frontend URL in a browser, sign in,
   and confirm the sidebar loads chats without a console error pointing at the wrong backend URL.
5. **LLM call succeeds** — send a message in a new chat; a response (not the
   "Sorry, I encountered an error..." fallback) confirms `EMERGENT_LLM_KEY` (or the
   configured provider key under Settings → Connections) is valid.

---

## 7. Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Backend fails to start, `KeyError: 'MONGO_URL'` / `'JWT_SECRET'` / `'ADMIN_EMAIL'` / `'ADMIN_PASSWORD'` | Required env var missing | These have no fallback by design — set them in `backend/.env` |
| Frontend loads but every API call fails / CORS error in browser console | `REACT_APP_BACKEND_URL` wrong, or backend's `CORS_ORIGINS` doesn't include the frontend's origin | Fix `REACT_APP_BACKEND_URL` and ensure `CORS_ORIGINS` lists the exact frontend origin (scheme + host, no trailing slash) |
| 401 immediately after login / "auto logged out" | Token not attached on first request after login, or `JWT_SECRET` changed between deploys (invalidates all existing tokens) | Re-login; if it persists across all users, confirm `JWT_SECRET` is stable across backend restarts |
| `429 Too many failed attempts` on login | Brute-force lockout (5 failed attempts per email → 15 min) | Wait 15 minutes, or clear the `login_attempts` collection for that identifier in MongoDB |
| Chat sends but reply is "Sorry, I encountered an error while generating a response" | LLM provider call failed (bad/empty `EMERGENT_LLM_KEY`, Universal Key balance exhausted, or a bring-your-own-key provider misconfigured in Settings → Connections) | Check backend logs for the real exception (admins also see a short error hint appended to the chat reply); top up the Universal Key under Profile → Manage Plan, or re-check provider keys in Connections |
| Admin-only tabs/routes return `403 Admin access required` | Logged in as a non-admin user | Sign in with the seeded admin account, or have an admin promote the user via Admin Panel → User Management |
| Mongo index/duplicate-key errors on startup | Pre-existing data violates a unique index (e.g. duplicate `users.email`) | Clean up the offending documents in that collection before restarting |
| Frontend build fails with dependency errors | Used `npm install` instead of `yarn install` | Delete `node_modules` and `package-lock.json` if present, then run `yarn install` |
| Backend process keeps restarting | Check logs — in the Emergent sandbox: `tail -n 100 /var/log/supervisor/backend.err.log`; self-hosted: your process manager's log output | Fix the error shown (usually a missing dependency or bad env var) |

---

## 8. Rollback

- **On the Emergent platform**: use the **Rollback** option in the chat UI to restore the app
  to any previous checkpoint — this is free and does not require a manual `git reset`.
- **Self-hosted**: keep each deploy as a tagged release (container image tag or git tag) so you
  can redeploy the previous tag; MongoDB data is independent of the app version, so only the
  app process needs to roll back in most cases.
