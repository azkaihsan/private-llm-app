# API Contracts & Integration Plan

## API Endpoints

### Models
- `GET /api/models` → Returns list of available AI models

### Chats
- `GET /api/chats` → List all chats (sorted by createdAt desc)
- `POST /api/chats` → Create new chat `{ title, model }`
- `GET /api/chats/{chat_id}` → Get chat with all messages
- `PUT /api/chats/{chat_id}` → Update chat (rename) `{ title }`
- `DELETE /api/chats/{chat_id}` → Delete chat and its messages

### Messages
- `POST /api/chats/{chat_id}/messages` → Send message and get AI response `{ content }`

## Mocked Data to Replace
- `mockData.js` → models array → replace with GET /api/models
- `mockData.js` → initialChats → replace with GET /api/chats
- `mockData.js` → mockResponses → replace with POST /api/chats/{id}/messages (real LLM)
- `mockData.js` → suggestions → keep as frontend constants

## Backend Implementation
- MongoDB collections: `chats`, `messages`
- LLM: emergentintegrations library with EMERGENT_LLM_KEY
- Provider mapping: openai, anthropic, gemini
- Session-based chat history managed in DB

## Frontend Integration
- App.js: fetch chats on mount, call real APIs for CRUD
- ChatInput: POST to /api/chats/{id}/messages, show loading state
- Model selector: fetch from /api/models
- Remove mockData imports except suggestions
