# Open WebUI Clone

A full-stack AI chat application inspired by [Open WebUI](https://github.com/open-webui/open-webui). Built with React, FastAPI, MongoDB, and multi-provider LLM support (OpenAI, Anthropic, Google Gemini).

---

## Features

### Chat Interface
- Real-time AI conversations with markdown-rendered responses
- Syntax-highlighted code blocks with one-click copy
- Auto-resizing input area with keyboard shortcuts (Enter to send, Shift+Enter for newline)
- Typing indicator animation while AI generates responses
- Message actions: copy, thumbs up/down, regenerate, edit

### Multi-Model Support
- **OpenAI**: GPT-4o, GPT-4.1 mini, GPT-5.1, GPT-5 mini
- **Anthropic**: Claude Sonnet 4.5, Claude 4 Sonnet
- **Google**: Gemini 2.5 Flash, Gemini 2.5 Pro
- Searchable model selector dropdown
- Per-chat model selection

### Chat Management
- **Export** — Download any chat as a `.json` file with full message history
- **Import** — Upload a previously exported `.json` file to restore a chat
- **Archive** — Hide chats from the main list; view/restore/delete from Archived Chats panel
- **Delete** — Permanently remove a chat and all its messages
- **Rename** — Inline rename from the sidebar context menu
- Auto-titling based on the first message sent

### Sidebar
- Collapsible sidebar with chat history
- Chats grouped by date: Today, Yesterday, Previous 7 Days, Previous 30 Days, Older
- Search/filter chats
- Context menu (⋯) on hover with Rename, Export, Archive, Delete actions
- Quick access to Import Chat, Workspace, and User menu

### Settings & Customization
- **General**: App name, logo customization (text or image upload), logo colors
- **Theme**: 6 built-in presets (Dark, Midnight Blue, Forest, Rosé, OLED Dark, Light) + fully custom color pickers for main background, sidebar, input area, accent, and user bubble
- **Font Size**: Adjustable from 12px–20px
- **System Prompt**: Customize AI assistant behavior globally
- All settings persist to MongoDB across sessions

---

## Tech Stack

| Layer | Technology |
|------------|---------------------------------------------|
| Frontend | React 19, Tailwind CSS, shadcn/ui, Lucide Icons |
| Backend | FastAPI, Pydantic, Motor (async MongoDB) |
| Database | MongoDB |
| LLM | emergentintegrations (OpenAI, Anthropic, Gemini) |
| Markdown | react-markdown, remark-gfm, react-syntax-highlighter |

---

## Project Structure

```
/app
├── backend/
│   ├── server.py              # FastAPI app with all API routes
│   ├── requirements.txt       # Python dependencies
│   └── .env                   # MONGO_URL, DB_NAME, EMERGENT_LLM_KEY
├── frontend/
│   ├── src/
│   │   ├── App.js             # Main app with state management
│   │   ├── App.css            # Global styles, scrollbar, animations
│   │   ├── index.css          # Tailwind + CSS variables for theming
│   │   ├── components/
│   │   │   ├── Sidebar.jsx    # Chat list, search, context menu, archived view
│   │   │   ├── ChatArea.jsx   # Message list with markdown rendering
│   │   │   ├── ChatInput.jsx  # Auto-resizing input with send/mic buttons
│   │   │   ├── WelcomeScreen.jsx  # Landing view with suggestions
│   │   │   ├── SettingsModal.jsx  # Settings with General/Theme/System tabs
│   │   │   └── ui/            # shadcn/ui component library
│   │   ├── context/
│   │   │   └── SettingsContext.jsx  # Global settings state + CSS variable injection
│   │   └── data/
│   │       └── mockData.js    # Suggestion cards data
│   ├── package.json
│   └── tailwind.config.js
├── contracts.md               # API contracts & integration plan
└── README.md
```

---

## API Reference

### Models
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/models` | List available AI models |

### Chats
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/chats` | List all active (non-archived) chats |
| POST | `/api/chats` | Create a new chat |
| GET | `/api/chats/:id` | Get chat with all messages |
| PUT | `/api/chats/:id` | Rename a chat |
| DELETE | `/api/chats/:id` | Delete a chat permanently |

### Messages
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/chats/:id/messages` | Send a message and receive AI response |

### Archive
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/chats/archived` | List archived chats |
| PUT | `/api/chats/:id/archive` | Archive a chat |
| PUT | `/api/chats/:id/unarchive` | Restore an archived chat |
| DELETE | `/api/chats/archived/all` | Delete all archived chats |

### Export / Import
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/chats/:id/export` | Export chat as JSON |
| POST | `/api/chats/import` | Import a chat from JSON |

### Settings
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/settings` | Get app settings |
| PUT | `/api/settings` | Save/update app settings |

---

## Environment Variables

### Backend (`/app/backend/.env`)
| Variable | Description |
|----------|-------------|
| `MONGO_URL` | MongoDB connection string |
| `DB_NAME` | Database name |
| `EMERGENT_LLM_KEY` | Universal LLM API key for OpenAI/Anthropic/Gemini |
| `CORS_ORIGINS` | Allowed CORS origins |

### Frontend (`/app/frontend/.env`)
| Variable | Description |
|----------|-------------|
| `REACT_APP_BACKEND_URL` | Backend API base URL |

---

## MongoDB Collections

| Collection | Purpose |
|------------|----------|
| `chats` | Chat metadata (id, title, model, created_at, archived) |
| `messages` | Individual messages (id, chat_id, role, content, timestamp) |
| `app_settings` | Global app settings (theme, logo, system prompt) |

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

---

## License

MIT
