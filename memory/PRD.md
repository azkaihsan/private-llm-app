# Product Requirements Document (PRD)
## Open WebUI Clone

---

### 1. Product Overview

A self-hosted, multi-model AI chat interface inspired by Open WebUI. The product provides a clean, dark-themed conversational UI that connects to multiple LLM providers (OpenAI, Anthropic, Google Gemini) through a unified backend, with persistent chat history, full chat management, deep UI customization, and Role-Based Access Control (RBAC).

---

### 2. Target Users

- Developers and AI enthusiasts who want a self-hosted ChatGPT-like interface
- Teams needing a centralized multi-model AI assistant with user management
- Users who want control over their data, theming, and system prompt

---

### 3. Core Features

#### 3.1 AI Chat Conversations
| Requirement | Status | Notes |
|---|---|---|
| Send messages and receive AI-generated responses | Done | Real LLM via emergentintegrations |
| Markdown rendering (headings, lists, tables, links, bold, italic) | Done | react-markdown + remark-gfm |
| Syntax-highlighted code blocks with language label | Done | react-syntax-highlighter (oneDark) |
| One-click copy for code blocks and messages | Done | Clipboard API |
| Typing indicator while AI generates response | Done | Animated dots |
| Auto-scroll to latest message | Done | useRef + scrollIntoView |
| Message action buttons (copy, thumbs up/down, regenerate, edit) | Done | Hover-reveal actions |

#### 3.2 Multi-Model Support
| Requirement | Status | Notes |
|---|---|---|
| OpenAI models (GPT-4o, GPT-4.1 mini, GPT-5.1, GPT-5 mini) | Done | |
| Anthropic models (Claude Sonnet 4.5, Claude 4 Sonnet) | Done | |
| Google models (Gemini 2.5 Flash, Gemini 2.5 Pro) | Done | |
| Searchable model selector dropdown | Done | Top bar of main area |
| Model persisted per chat | Done | Stored in MongoDB |

#### 3.3 Chat Management
| Requirement | Status | Notes |
|---|---|---|
| Create new chat | Done | Sidebar button + auto-create on first message |
| Auto-title chat from first message content | Done | First 50 chars |
| Rename chat | Done | Inline edit via context menu |
| Delete chat with confirmation | Done | Removes chat + all messages |
| Export chat as JSON file | Done | Downloads `.json` with chat metadata + messages |
| Import chat from JSON file | Done | File picker in sidebar footer |
| Archive chat (soft-hide from main list) | Done | Moves to archived state |
| View archived chats in dedicated panel | Done | Accessible via User menu |
| Unarchive chat (restore to main list) | Done | Button in archived panel |
| Delete individual archived chat | Done | With confirmation |
| Bulk delete all archived chats | Done | Trash icon in archived panel header |

#### 3.4 Sidebar
| Requirement | Status | Notes |
|---|---|---|
| Collapsible sidebar | Done | Toggle with PanelLeft icon |
| Chat history grouped by date | Done | Today, Yesterday, 7 Days, 30 Days, Older |
| Search/filter chats | Done | Search icon + text input |
| Context menu on hover/active | Done | Rename, Export, Archive, Delete |
| User profile section | Done | Shows authenticated user name + avatar initial |
| User menu (Settings, Archived Chats, User Mgmt, Sign Out) | Done | Popover from user button |
| Import Chat button | Done | Sidebar footer |

#### 3.5 Settings & Customization
| Requirement | Status | Notes |
|---|---|---|
| Settings modal with tabbed navigation | Done | General, Theme, System Prompt (+ Connections, Models for admin) |
| Change app name | Done | Text input |
| Logo customization: text mode (custom text, bg color, text color) | Done | Max 4 chars, dual color pickers |
| Logo customization: image mode (upload up to 512KB) | Done | Base64 storage |
| Live logo preview | Done | In General tab |
| 6 built-in theme presets | Done | Dark, Midnight Blue, Forest, Rose, OLED Dark, Light |
| Custom color pickers (5 areas) | Done | Main BG, Sidebar, Input, Accent, User Bubble |
| Font size slider (12-20px) | Done | Applied via CSS variable |
| System prompt customization | Done | Textarea, applied to all new LLM calls |
| Settings persistence to MongoDB | Done | GET/PUT /api/settings |
| Settings load from localStorage as fallback | Done | Instant load before API response |
| Reset to defaults | Done | Button in modal footer |

#### 3.6 Authentication & RBAC
| Requirement | Status | Notes |
|---|---|---|
| JWT-based authentication | Done | bcrypt + pyjwt, 72hr token expiry |
| Login page with email/password | Done | Themed AuthPage component |
| Signup page with name/email/password | Done | Toggle from login |
| First registered user becomes admin | Done | Automatic via user count check |
| Admin: Connections & Models settings | Done | Admin-only tabs in SettingsModal |
| Admin: User Management panel | Done | Create, edit, delete users with roles |
| Regular user: Limited settings | Done | Only General, Theme, System Prompt tabs |
| Chat isolation between users | Done | user_id scoped queries |
| Logout with token cleanup | Done | Clears localStorage + axios headers |

#### 3.7 Welcome Screen
| Requirement | Status | Notes |
|---|---|---|
| Greeting message "How can I help you today?" | Done | Centered with logo |
| 4 suggestion cards | Done | Study, Ideas, Fun Fact, Workout |
| Click suggestion to start a new chat | Done | Auto-creates chat + sends message |

---

### 4. Technical Architecture

#### 4.1 Frontend
- **Framework**: React 19 with Create React App + CRACO
- **Styling**: Tailwind CSS 3 + CSS custom properties for dynamic theming
- **UI Library**: shadcn/ui (Radix primitives)
- **Icons**: Lucide React
- **Markdown**: react-markdown + remark-gfm + react-syntax-highlighter
- **State**: React useState/useCallback/useEffect + Context API (Settings + Auth)
- **HTTP**: Axios with auto-attached JWT Authorization header

#### 4.2 Backend
- **Framework**: FastAPI with APIRouter (all routes under `/api` prefix)
- **Database**: MongoDB via Motor (async driver)
- **LLM Integration**: emergentintegrations library with universal EMERGENT_LLM_KEY
- **Provider routing**: Model ID -> provider mapping (openai/anthropic/gemini) + litellm for 6 additional providers
- **Auth**: bcrypt password hashing, PyJWT token generation/validation
- **Validation**: Pydantic v2 models

#### 4.3 Database Schema

**users**
```json
{
  "id": "uuid",
  "name": "string",
  "email": "string (lowercase)",
  "password_hash": "bcrypt hash",
  "role": "admin | user",
  "created_at": "ISO datetime"
}
```

**chats**
```json
{
  "id": "uuid",
  "title": "string",
  "model": "string (model id)",
  "user_id": "uuid (FK to users.id)",
  "created_at": "ISO datetime",
  "archived": "boolean (optional)"
}
```

**messages**
```json
{
  "id": "uuid",
  "chat_id": "uuid (FK to chats.id)",
  "role": "user | assistant",
  "content": "string (markdown)",
  "timestamp": "ISO datetime"
}
```

**connections** (single doc, _id="global")
**app_settings** (single doc, _id="global")

---

### 5. API Endpoints

| # | Method | Endpoint | Auth | Purpose |
|---|--------|----------|------|----------|
| 1 | POST | /api/auth/signup | None | Register new user |
| 2 | POST | /api/auth/login | None | Login, get JWT token |
| 3 | GET | /api/auth/me | JWT | Get current user info |
| 4 | GET | /api/admin/users | Admin | List all users |
| 5 | POST | /api/admin/users | Admin | Create new user |
| 6 | PUT | /api/admin/users/:id | Admin | Update user |
| 7 | DELETE | /api/admin/users/:id | Admin | Delete user + chats |
| 8 | GET | /api/models | None | List available LLM models |
| 9 | GET | /api/connections | Admin | Get provider connections |
| 10 | PUT | /api/connections | Admin | Update connections |
| 11 | POST | /api/connections/test | Admin | Test provider connection |
| 12 | GET | /api/chats | JWT | List user's active chats |
| 13 | POST | /api/chats | JWT | Create new chat |
| 14 | GET | /api/chats/:id | JWT | Get chat + messages |
| 15 | PUT | /api/chats/:id | JWT | Rename chat |
| 16 | DELETE | /api/chats/:id | JWT | Delete chat + messages |
| 17 | POST | /api/chats/:id/messages | JWT | Send message, get AI response |
| 18 | GET | /api/chats/archived | JWT | List archived chats |
| 19 | PUT | /api/chats/:id/archive | JWT | Archive a chat |
| 20 | PUT | /api/chats/:id/unarchive | JWT | Unarchive a chat |
| 21 | GET | /api/chats/:id/export | JWT | Export chat as JSON |
| 22 | POST | /api/chats/import | JWT | Import chat from JSON |
| 23 | DELETE | /api/chats/archived/all | JWT | Delete all archived |
| 24 | GET | /api/settings | None | Get global settings |
| 25 | PUT | /api/settings | None | Save global settings |

---

### 6. Future Enhancements (Not Yet Implemented)

- Streaming responses (real-time token display)
- File/image upload in messages
- Conversation branching (edit + regenerate from any point)
- Prompt templates library
- Token usage tracking and cost estimation
- Keyboard shortcuts (Ctrl+N new chat, Ctrl+Shift+S settings)
- Mobile-optimized responsive layout
- RAG (Retrieval Augmented Generation) with document upload
- Voice input/output
- Plugin system for custom tools

---

### 7. Known Limitations

- LLM responses are non-streaming (full response returned after generation completes)
- Logo image stored as base64 in MongoDB (max 512KB enforced on frontend)
- Emergent LLM key budget may need topping up (Profile -> Universal Key -> Add Balance)
- `server.py` is ~700 lines and could benefit from router modularization
