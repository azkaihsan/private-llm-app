# API Contracts

All routes are under `/api`. Authenticated routes require `Authorization: Bearer <jwt>`.
Roles: `admin` (everything) and `user`. Errors: `401` not authenticated, `403` admin required, `404` not found / not owned, `400` validation.

## Auth
- `POST /auth/signup` `{name, email, password}` → `{token, user}` — first user ever becomes `admin`, others `user`; duplicate email → 400
- `POST /auth/login` `{email, password}` → `{token, user}`; bad credentials → 401; 5 failures per email → 429 for 15 min
- `GET /auth/me` → `{id, name, email, role, created_at}`
- `PUT /auth/profile` `{name}` → updated user; empty name → 400
- `PUT /auth/password` `{current_password, new_password}` → `{success: true}`; wrong current or new < 6 chars → 400

## Admin — Users (admin only)
- `GET /admin/users` → `[user]`
- `POST /admin/users` `{name, email, password, role}` → user
- `PUT /admin/users/{id}` `{name?, email?, role?, password?}` → `{status}`; own-role change → 400
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
- `PUT /chats/{id}/pin` · `PUT /chats/{id}/unpin` → `{status}` (archive also sets `pinned: false`)
- `PUT /chats/{id}/archive` · `PUT /chats/{id}/unarchive`
- `PUT /chats/{id}/folder` `{folder_id: string|null}` → `{status}`; folder must belong to caller → 404 otherwise
- `DELETE /chats/archived/all`
- `GET /chats/{id}/export` → `{version, chat, messages}`
- `POST /chats/import` `{version, chat: {title, model}, messages: [{role, content}]}` → `{status, chat_id, chat}`

## Folders (scoped to the caller's `user_id`)
- `GET /folders` → folders ordered by `position` then `created_at`
- `POST /folders` `{name, instructions?, color?, icon?}` → folder; name 1-60 chars (whitespace-normalized, case-insensitive unique) → 409 on duplicate; 200/user cap → 400; `color` must be one of the 10 whitelisted hex values (or empty), `icon` one of 16 keys (or empty) → 422 otherwise; `instructions` ≤ 4000 chars
- `PUT /folders/{id}` `{name, instructions?, color?, icon?}` → `{status}`; same validation as create; 404 if not owned
- `DELETE /folders/{id}` → `{status, moved_chats}`; the folder's chats have `folder_id` cleared (returned to the main list)
- `PUT /folders/order` `{ids: [folder_id, ...]}` → `{status}`; must list every one of the caller's folder ids exactly once (no more, no less, no dupes) → 400 otherwise; sets `position` to the array index
- New folders get `position` = current folder count (appended at the bottom)
- Deleting a user (`DELETE /admin/users/{id}`) also deletes that user's folders

## Settings (global appearance)
- `GET /settings` (public) · `PUT /settings` (admin; allowlisted keys only) `{appName, logo*, theme, colors..., fontSize, systemPrompt}`

## Frontend integration notes
- `AuthContext` stores the token in `localStorage.openwebui_token`, sets `axios.defaults.headers.common.Authorization` synchronously on login, and auto-logs out on any 401.
- `App.js` gates rendering: loading → `AuthPage` (no user) → `AppContent`.
- Admin-only UI: Settings tabs *Connections* / *Models*, sidebar *Admin Panel*, palette *Admin Panel* action.
- Search: `Sidebar` and `CommandPalette` debounce calls to `/chats/search`; palette message results call `jumpToMessage(chatId, term)` which opens the chat with the in-chat search bar pre-filled.
- Folders: `hooks/useFolders.js` wraps `/folders*` and `/chats/{id}/folder` calls and keeps local folder state in sync; `FolderSection.jsx` renders folders (HTML5 native drag/drop — no DnD library is installed), `FolderSettingsDialog.jsx` edits name/instructions/colour/icon. Folder collapse state is per-user in `localStorage` (`openwebui_collapsed_folders_<userId>`), not persisted server-side. Folder reordering is disabled while the sidebar search box has text.
- Server-side system prompt composition for a folder chat: global `systemPrompt` (from `/settings`) first, then `\n\nProject instructions:\n<folder.instructions>` if the chat's `folder_id` resolves to a folder with non-empty instructions.
