# Open WebUI Clone

A full-stack, multi-user AI chat application inspired by [Open WebUI](https://github.com/open-webui/open-webui). Built with React, FastAPI and MongoDB, with JWT authentication, admin/user roles and support for 9 LLM providers.

---

## Features

### Chat Interface
- Real-time AI conversations with markdown-rendered responses
- Syntax-highlighted code blocks with one-click copy
- Auto-resizing input (Enter to send, Shift+Enter for newline)
- Typing indicator while the AI generates a response
- Message actions: copy, thumbs up/down, regenerate, edit

### Multi-Provider LLM Support
- **Built-in via Emergent key**: OpenAI (GPT-4o, GPT-4.1 mini, GPT-5.1, GPT-5 mini), Anthropic (Claude Sonnet 4.5, Claude 4 Sonnet), Google (Gemini 2.5 Flash / Pro)
- **Bring your own key**: DeepSeek, Qwen, Grok (xAI), Perplexity, Amazon Bedrock, any OpenAI-compatible endpoint
- Admin-managed connections (API keys, base URLs, test connection) and per-model enable/disable
- Searchable model selector, default model, model remembered per chat

### Authentication & Roles
- Email/password sign up & sign in (bcrypt + JWT, 72h tokens)
- Two roles: **admin** and **user**. The first account ever created becomes admin; a default admin is also seeded from `.env`
- Every user sees only their own chats
- **Admin Panel → User Management**: list, search, create, edit (name / email / role / password) and delete users
- **Connections**, **Models**, **General** and **System Prompt** settings are admin-only; non-admins get a device-local **Theme** and the **Account** tab
- **Account** tab: change display name and password
- Login brute-force lockout (5 failures → 15 min), strict input validation, NoSQL key sanitization

### Search
- **Ctrl/Cmd + K command palette** — from anywhere: jump to a chat by title, jump to a message match (opens the chat and highlights the term), or run quick actions (New Chat, Settings, Archived Chats, Admin Panel)
- **In-chat search** (Ctrl/Cmd + F or the search icon in the chat header) — highlights every match, `n/m` counter, prev/next navigation
- **Sidebar search** matches chat titles *and* message content, showing a snippet under the chat

### Chat Management
- **Pin** favourite chats to a "Pinned" section at the top of the sidebar (hover pin icon or ⋯ menu)
- Export (JSON), Import, Archive / Unarchive, Rename, Delete
- Archived Chats panel with restore, delete and delete-all
- Auto-titling from the first message

### Settings & Customization
- **General**: app name, logo (text or image upload), logo colors
- **Theme**: 6 presets (Dark, Midnight Blue, Forest, Rosé, OLED Dark, Light) + custom color pickers for main background, sidebar, input, accent and user bubble
- **Font size** 12–20px, **System Prompt**
- Settings persist to MongoDB (localStorage used as an instant cache)

---

## Tech Stack

| Layer | Technology |
|------------|---------------------------------------------|
| Frontend | React 19, Tailwind CSS, shadcn/ui, Lucide Icons, Axios |
| Backend | FastAPI, Pydantic v2, Motor (async MongoDB), PyJWT, bcrypt |
| Database | MongoDB |
| LLM | emergentintegrations (OpenAI, Anthropic, Gemini) + litellm (DeepSeek, Qwen, Grok, Perplexity, Bedrock, OpenAI-compatible) |
| Markdown | react-markdown, remark-gfm, react-syntax-highlighter |

---

## Project Structure

```
/app
├── backend/
│   ├── server.py                  # FastAPI app: auth, users, chats, search, connections, settings
│   ├── requirements.txt
│   └── .env                       # MONGO_URL, DB_NAME, EMERGENT_LLM_KEY, JWT_SECRET, ADMIN_EMAIL, ADMIN_PASSWORD
├── frontend/
│   ├── src/
│   │   ├── App.js                 # Auth gate, chat state, in-chat search, command palette
│   │   ├── components/
│   │   │   ├── AuthPage.jsx       # Sign in / Sign up
│   │   │   ├── Sidebar.jsx        # Chat list, title+content search, user menu, archived view
│   │   │   ├── ChatArea.jsx       # Messages with markdown + match highlighting
│   │   │   ├── ChatSearchBar.jsx  # In-chat search bar (Ctrl+F)
│   │   │   ├── CommandPalette.jsx # Ctrl+K palette (chats, messages, actions)
│   │   │   ├── ChatInput.jsx
│   │   │   ├── WelcomeScreen.jsx
│   │   │   ├── SettingsModal.jsx  # Connections*, Models*, General, Theme, System Prompt, Account (*admin only)
│   │   │   ├── AccountTab.jsx     # Display name + password change
│   │   │   ├── UserManagement.jsx # Admin user CRUD modal
│   │   │   └── ui/                # shadcn/ui primitives
│   │   ├── context/
│   │   │   ├── AuthContext.jsx    # JWT storage, axios auth header, 401 auto-logout
│   │   │   └── SettingsContext.jsx
│   │   └── data/mockData.js       # Suggestion cards
│   └── .env                       # REACT_APP_BACKEND_URL
├── memory/
│   ├── PRD.md                     # Product requirements & changelog
│   └── test_credentials.md        # Seeded admin credentials for testing
├── contracts.md                   # API contracts
└── README.md
```

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl/⌘ + K` | Open command palette (search chats, messages, actions) |
| `Ctrl/⌘ + F` | Search inside the open chat |
| `↑ / ↓`, `Enter`, `Esc` | Navigate / open / close in palette and search bar |
| `Enter` / `Shift+Enter` | Send message / new line |

---

## API Reference

All routes are prefixed with `/api`. Authenticated routes expect `Authorization: Bearer <token>`.

### Auth
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/auth/signup` | — | Register `{name, email, password}` → `{token, user}`. First user becomes admin |
| POST | `/auth/login` | — | Login `{email, password}` → `{token, user}` |
| GET | `/auth/me` | user | Current user |
| PUT | `/auth/profile` | user | Update display name `{name}` |
| PUT | `/auth/password` | user | Change password `{current_password, new_password}` |

### Admin — Users
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/admin/users` | admin | List users |
| POST | `/admin/users` | admin | Create user `{name, email, password, role}` |
| PUT | `/admin/users/:id` | admin | Update name / email / role / password |
| DELETE | `/admin/users/:id` | admin | Delete user and their chats (cannot delete self) |

### Connections & Models
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/models` | — | Available models (respects enabled flags) |
| GET | `/connections` | admin | Provider settings (keys masked) |
| PUT | `/connections` | admin | Save provider settings / default model / enabled models |
| POST | `/connections/test` | admin | Test a provider connection |

### Chats & Messages
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/chats` | user | List the caller's active chats |
| POST | `/chats` | user | Create chat `{title, model}` |
| GET | `/chats/search?q=` | user | Search message content across the caller's chats → `[{chat_id, snippet, role, count}]` |
| GET | `/chats/:id` | user | Chat with messages |
| PUT | `/chats/:id` | user | Rename |
| DELETE | `/chats/:id` | user | Delete chat + messages |
| POST | `/chats/:id/messages` | user | Send message, receive AI reply |
| GET | `/chats/archived` | user | Archived chats |
| PUT | `/chats/:id/pin` · `/unpin` | user | Pin / unpin (archiving also unpins) |
| PUT | `/chats/:id/archive` · `/unarchive` | user | Archive / restore |
| DELETE | `/chats/archived/all` | user | Delete all archived |
| GET | `/chats/:id/export` | user | Export as JSON |
| POST | `/chats/import` | user | Import from JSON |

### Settings
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/settings` | — | Global appearance settings |
| PUT | `/settings` | admin | Save appearance settings |

---

## Environment Variables

### Backend (`/app/backend/.env`)
| Variable | Description |
|----------|-------------|
| `MONGO_URL` | MongoDB connection string |
| `DB_NAME` | Database name |
| `EMERGENT_LLM_KEY` | Universal key for OpenAI / Anthropic / Gemini |
| `CORS_ORIGINS` | Allowed CORS origins |
| `JWT_SECRET` | Secret used to sign JWTs |
| `ADMIN_EMAIL` / `ADMIN_PASSWORD` | Default admin seeded (idempotently) on startup |

### Frontend (`/app/frontend/.env`)
| Variable | Description |
|----------|-------------|
| `REACT_APP_BACKEND_URL` | Backend base URL |

---

## MongoDB Collections

| Collection | Purpose |
|------------|----------|
| `users` | `{id, name, email, password_hash, role, created_at}` — unique index on `email` |
| `chats` | `{id, title, model, user_id, archived, pinned, created_at}` |
| `login_attempts` | `{identifier, count, locked_until}` — brute-force lockout |
| `messages` | `{id, chat_id, role, content, timestamp}` |
| `connections` | Provider API keys / base URLs, default model, enabled models |
| `app_settings` | Theme, logo, font size, system prompt |

---

## Running Locally

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn server:app --host 0.0.0.0 --port 8001

# Frontend
cd frontend
yarn install
yarn start
```

Sign in with the seeded admin (`ADMIN_EMAIL` / `ADMIN_PASSWORD` from `backend/.env`) or create an account — the first account created becomes admin.

---

## License

MIT
