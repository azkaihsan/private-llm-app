# Product Requirements Document (PRD)
## Open WebUI Clone

---

### 1. Product Overview

A self-hosted, multi-model AI chat interface inspired by Open WebUI. The product provides a clean, dark-themed conversational UI that connects to multiple LLM providers (OpenAI, Anthropic, Google Gemini) through a unified backend, with persistent chat history, full chat management, and deep UI customization.

---

### 2. Target Users

- Developers and AI enthusiasts who want a self-hosted ChatGPT-like interface
- Teams needing a centralized multi-model AI assistant
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
| Context menu (⋯) on hover/active | Done | Rename, Export, Archive, Delete |
| User profile section | Done | Avatar + name at bottom |
| User menu (Settings, Archived Chats, Sign Out) | Done | Popover from user button |
| Import Chat button | Done | Sidebar footer |

#### 3.5 Settings & Customization
| Requirement | Status | Notes |
|---|---|---|
| Settings modal with tabbed navigation | Done | General, Theme, System Prompt |
| Change app name | Done | Text input |
| Logo customization: text mode (custom text, bg color, text color) | Done | Max 4 chars, dual color pickers |
| Logo customization: image mode (upload up to 512KB) | Done | Base64 storage |
| Live logo preview | Done | In General tab |
| 6 built-in theme presets | Done | Dark, Midnight Blue, Forest, Rosé, OLED Dark, Light |
| Custom color pickers (5 areas) | Done | Main BG, Sidebar, Input, Accent, User Bubble |
| Font size slider (12–20px) | Done | Applied via CSS variable |
| System prompt customization | Done | Textarea, applied to all new LLM calls |
| Settings persistence to MongoDB | Done | GET/PUT /api/settings |
| Settings load from localStorage as fallback | Done | Instant load before API response |
| Reset to defaults | Done | Button in modal footer |
| Light/dark text auto-detection | Done | Based on background luminance |

#### 3.6 Welcome Screen
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
- **State**: React useState/useCallback/useEffect + Context API for settings
- **HTTP**: Axios

#### 4.2 Backend
- **Framework**: FastAPI with APIRouter (all routes under `/api` prefix)
- **Database**: MongoDB via Motor (async driver)
- **LLM Integration**: emergentintegrations library with universal EMERGENT_LLM_KEY
- **Provider routing**: Model ID → provider mapping (openai/anthropic/gemini)
- **Validation**: Pydantic v2 models

#### 4.3 Database Schema

**chats**
```json
{
  "id": "uuid",
  "title": "string",
  "model": "string (model id)",
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

**app_settings**
```json
{
  "_id": "global",
  "appName": "string",
  "logoType": "text | image",
  "logoText": "string",
  "logoImageUrl": "string (base64)",
  "logoBgColor": "hex",
  "logoTextColor": "hex",
  "theme": "preset key or 'custom'",
  "mainBg": "hex",
  "sidebarBg": "hex",
  "inputBg": "hex",
  "accentColor": "hex",
  "userBubbleBg": "hex",
  "fontSize": "number (12-20)",
  "systemPrompt": "string"
}
```

---

### 5. API Endpoints (17 total)

| # | Method | Endpoint | Purpose |
|---|--------|----------|----------|
| 1 | GET | /api/models | List available LLM models |
| 2 | GET | /api/chats | List active chats |
| 3 | POST | /api/chats | Create new chat |
| 4 | GET | /api/chats/:id | Get chat + messages |
| 5 | PUT | /api/chats/:id | Rename chat |
| 6 | DELETE | /api/chats/:id | Delete chat + messages |
| 7 | POST | /api/chats/:id/messages | Send message, get AI response |
| 8 | GET | /api/chats/archived | List archived chats |
| 9 | PUT | /api/chats/:id/archive | Archive a chat |
| 10 | PUT | /api/chats/:id/unarchive | Unarchive a chat |
| 11 | GET | /api/chats/:id/export | Export chat as JSON |
| 12 | POST | /api/chats/import | Import chat from JSON |
| 13 | DELETE | /api/chats/archived/all | Delete all archived |
| 14 | GET | /api/settings | Get global settings |
| 15 | PUT | /api/settings | Save global settings |
| 16 | GET | /api/ | Health check |
| 17 | GET/POST | /api/status | Status check (legacy) |

---

### 6. Non-Functional Requirements

| Requirement | Implementation |
|---|---|
| Responsive sidebar | Collapsible with smooth transition |
| Dark theme by default | #212121 main, #171717 sidebar |
| Custom scrollbars | 6px thin scrollbar, subtle hover |
| Performance | Optimistic UI updates, lazy message loading |
| Error handling | Try-catch on all API calls, graceful LLM error display |
| Persistence | MongoDB for all data, localStorage as fast cache for settings |

---

### 7. Future Enhancements (Not Yet Implemented)

- Streaming responses (real-time token display)
- User authentication (JWT or OAuth)
- Multi-user support with separate chat histories
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

### 8. Known Limitations

- LLM responses are non-streaming (full response returned after generation completes)
- No authentication — single-user mode
- Logo image stored as base64 in MongoDB (max 512KB enforced on frontend)
- Emergent LLM key budget may need topping up (Profile → Universal Key → Add Balance)
