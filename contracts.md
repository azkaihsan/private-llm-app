# API Contracts

All routes are under `/api`. Authenticated routes require `Authorization: Bearer <jwt>`.
Roles: `admin` (everything) and `user`. Errors: `401` not authenticated, `403` admin required, `404` not found / not owned, `400` validation.

## Auth
- `POST /auth/signup` `{name, email, password}` → `{token, user}` — first user ever becomes `admin`, others `user`; duplicate email → 400
- `POST /auth/login` `{email, password}` → `{token, user}`; bad credentials → 401
- `GET /auth/me` → `{id, name, email, role, created_at}`
- `PUT /auth/profile` `{name}` → updated user; empty name → 400
- `PUT /auth/password` `{current_password, new_password}` → `{success: true}`; wrong current or new < 6 chars → 400

## Admin — Users (admin only)
- `GET /admin/users` → `[user]`
- `POST /admin/users` `{name, email, password, role}` → user
- `PUT /admin/users/{id}` `{name?, email?, role?, password?}` → user
- `DELETE /admin/users/{id}` → `{status: "ok"}`; deletes the user's chats/messages; self-delete → 400

## Connections & Models
- `GET /models` → `[{id, name, provider, enabled}]`
- `GET /connections` (admin) → provider config with masked keys, `defaultModel`, `enabledModels`
- `PUT /connections` (admin) `{<provider>: {apiKey, baseUrl, ...}, defaultModel, enabledModels}` → saved config
- `POST /connections/test` (admin) `{provider, apiKey?, baseUrl?, model?}` → `{success, message}`

## Chats (scoped to the caller's `user_id`)
- `GET /chats` → active chats, newest first
- `POST /chats` `{title, model}` → chat
- `GET /chats/search?q=` → `[{chat_id, snippet, role, count}]` (case-insensitive, `q` ≥ 2 chars, excludes archived)
- `GET /chats/archived` → archived chats
- `GET /chats/{id}` → `{...chat, messages: [...]}`
- `PUT /chats/{id}` `{title}` → `{status}`
- `DELETE /chats/{id}` → `{status}`
- `POST /chats/{id}/messages` `{content, temperature?, max_tokens?}` → `{user_message, assistant_message}`
- `PUT /chats/{id}/archive` · `PUT /chats/{id}/unarchive`
- `DELETE /chats/archived/all`
- `GET /chats/{id}/export` → `{version, chat, messages}`
- `POST /chats/import` `{version, chat: {title, model}, messages: [{role, content}]}` → `{status, chat_id, chat}`

## Settings (global appearance, public)
- `GET /settings` · `PUT /settings` `{appName, logo*, theme, colors..., fontSize, systemPrompt}`

## Frontend integration notes
- `AuthContext` stores the token in `localStorage.openwebui_token`, sets `axios.defaults.headers.common.Authorization` synchronously on login, and auto-logs out on any 401.
- `App.js` gates rendering: loading → `AuthPage` (no user) → `AppContent`.
- Admin-only UI: Settings tabs *Connections* / *Models*, sidebar *Admin Panel*, palette *Admin Panel* action.
- Search: `Sidebar` and `CommandPalette` debounce calls to `/chats/search`; palette message results call `jumpToMessage(chatId, term)` which opens the chat with the in-chat search bar pre-filled.
