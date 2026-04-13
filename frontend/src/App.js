import React, { useState, useCallback, useEffect } from "react";
import "@/App.css";
import Sidebar from "@/components/Sidebar";
import WelcomeScreen from "@/components/WelcomeScreen";
import ChatArea from "@/components/ChatArea";
import ChatInput from "@/components/ChatInput";
import SettingsModal from "@/components/SettingsModal";
import UserManagement from "@/components/UserManagement";
import AuthPage from "@/components/AuthPage";
import { SettingsProvider, useSettings } from "@/context/SettingsContext";
import { AuthProvider, useAuth } from "@/context/AuthContext";
import { suggestions } from "@/data/mockData";
import { PanelLeft, SquarePen, ChevronDown, Check, Search, Loader2 } from "lucide-react";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function AppContent() {
  const { settings } = useSettings();
  const { user, isAdmin, logout } = useAuth();
  const [chats, setChats] = useState([]);
  const [activeChatId, setActiveChatId] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [selectedModel, setSelectedModel] = useState(null);
  const [models, setModels] = useState([]);
  const [isTyping, setIsTyping] = useState(false);
  const [modelDropdownOpen, setModelDropdownOpen] = useState(false);
  const [modelSearch, setModelSearch] = useState("");
  const [activeMessages, setActiveMessages] = useState([]);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [userMgmtOpen, setUserMgmtOpen] = useState(false);

  // Fetch models on mount
  const fetchModels = useCallback(async () => {
    try {
      const res = await axios.get(`${API}/models`);
      const enabledModels = res.data.filter(m => m.enabled !== false);
      setModels(enabledModels);
      // Try to load default model from connections
      const connRes = await axios.get(`${API}/connections`);
      const defaultModelId = connRes.data?.defaultModel;
      const defaultModel = enabledModels.find(m => m.id === defaultModelId);
      if (defaultModel) setSelectedModel(defaultModel);
      else if (enabledModels.length > 0 && !selectedModel) setSelectedModel(enabledModels[0]);
    } catch (e) {
      console.error("Failed to fetch models:", e);
    }
  }, []);

  useEffect(() => { fetchModels(); }, [fetchModels]);

  // Fetch chats on mount
  useEffect(() => {
    const fetchChats = async () => {
      try {
        const res = await axios.get(`${API}/chats`);
        const mapped = res.data.map(c => ({
          ...c,
          createdAt: new Date(c.created_at).getTime(),
        }));
        setChats(mapped);
      } catch (e) {
        console.error("Failed to fetch chats:", e);
      }
    };
    fetchChats();
  }, []);

  // Fetch messages when active chat changes
  useEffect(() => {
    if (!activeChatId) { setActiveMessages([]); return; }
    const fetchMessages = async () => {
      try {
        const res = await axios.get(`${API}/chats/${activeChatId}`);
        setActiveMessages(res.data.messages || []);
      } catch (e) {
        console.error("Failed to fetch chat:", e);
      }
    };
    fetchMessages();
  }, [activeChatId]);

  const createNewChat = useCallback(() => {
    setActiveChatId(null);
    setActiveMessages([]);
    setIsTyping(false);
  }, []);

  const selectChat = useCallback((chatId) => {
    setActiveChatId(chatId);
    setIsTyping(false);
  }, []);

  const deleteChat = useCallback(async (chatId) => {
    try {
      await axios.delete(`${API}/chats/${chatId}`);
      setChats(prev => prev.filter(c => c.id !== chatId));
      if (activeChatId === chatId) { setActiveChatId(null); setActiveMessages([]); }
    } catch (e) { console.error("Failed to delete chat:", e); }
  }, [activeChatId]);

  const renameChat = useCallback(async (chatId, newTitle) => {
    try {
      await axios.put(`${API}/chats/${chatId}`, { title: newTitle });
      setChats(prev => prev.map(c => c.id === chatId ? { ...c, title: newTitle } : c));
    } catch (e) { console.error("Failed to rename chat:", e); }
  }, []);

  // ===== Archive, Export, Import =====
  const [archivedChats, setArchivedChats] = useState([]);

  const archiveChat = useCallback(async (chatId) => {
    try {
      await axios.put(`${API}/chats/${chatId}/archive`);
      setChats(prev => prev.filter(c => c.id !== chatId));
      if (activeChatId === chatId) { setActiveChatId(null); setActiveMessages([]); }
    } catch (e) { console.error("Failed to archive chat:", e); }
  }, [activeChatId]);

  const fetchArchivedChats = useCallback(async () => {
    try {
      const res = await axios.get(`${API}/chats/archived`);
      setArchivedChats(res.data.map(c => ({ ...c, createdAt: new Date(c.created_at).getTime() })));
    } catch (e) { console.error("Failed to fetch archived chats:", e); }
  }, []);

  const unarchiveChat = useCallback(async (chatId) => {
    try {
      await axios.put(`${API}/chats/${chatId}/unarchive`);
      setArchivedChats(prev => prev.filter(c => c.id !== chatId));
      // Refresh main chats
      const res = await axios.get(`${API}/chats`);
      setChats(res.data.map(c => ({ ...c, createdAt: new Date(c.created_at).getTime() })));
    } catch (e) { console.error("Failed to unarchive chat:", e); }
  }, []);

  const deleteArchivedChat = useCallback(async (chatId) => {
    try {
      await axios.delete(`${API}/chats/${chatId}`);
      setArchivedChats(prev => prev.filter(c => c.id !== chatId));
    } catch (e) { console.error("Failed to delete archived chat:", e); }
  }, []);

  const deleteAllArchived = useCallback(async () => {
    try {
      await axios.delete(`${API}/chats/archived/all`);
      setArchivedChats([]);
    } catch (e) { console.error("Failed to delete all archived:", e); }
  }, []);

  const exportChat = useCallback(async (chatId) => {
    try {
      const res = await axios.get(`${API}/chats/${chatId}/export`);
      const blob = new Blob([JSON.stringify(res.data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      const title = res.data.chat?.title || 'chat';
      a.download = `${title.replace(/[^a-z0-9]/gi, '_').toLowerCase()}_export.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (e) { console.error("Failed to export chat:", e); }
  }, []);

  const importChat = useCallback(async (data) => {
    try {
      const payload = { version: data.version || "1.0", chat: data.chat, messages: data.messages };
      const res = await axios.post(`${API}/chats/import`, payload);
      // Refresh chats list
      const chatsRes = await axios.get(`${API}/chats`);
      setChats(chatsRes.data.map(c => ({ ...c, createdAt: new Date(c.created_at).getTime() })));
      // Select the imported chat
      if (res.data.chat_id) setActiveChatId(res.data.chat_id);
    } catch (e) { console.error("Failed to import chat:", e); alert("Failed to import chat. Please check the file format."); }
  }, []);

  const sendMessage = useCallback(async (content) => {
    if (isTyping) return;
    const modelId = selectedModel?.id || "gpt-4o";

    if (!activeChatId) {
      // Create new chat first
      try {
        const title = content.length > 50 ? content.slice(0, 50) + "..." : content;
        const res = await axios.post(`${API}/chats`, { title, model: modelId });
        const newChat = { ...res.data, createdAt: new Date(res.data.created_at).getTime() };
        setChats(prev => [newChat, ...prev]);
        setActiveChatId(newChat.id);

        // Optimistic: show user message immediately
        const tempUserMsg = { id: `temp-${Date.now()}`, role: "user", content, timestamp: new Date().toISOString() };
        setActiveMessages([tempUserMsg]);
        setIsTyping(true);

        // Send message to backend
        const msgRes = await axios.post(`${API}/chats/${newChat.id}/messages`, { content });
        setActiveMessages([msgRes.data.user_message, msgRes.data.assistant_message]);

        // Update chat title from backend
        const updatedChat = await axios.get(`${API}/chats/${newChat.id}`);
        setChats(prev => prev.map(c => c.id === newChat.id ? { ...c, title: updatedChat.data.title } : c));
        setIsTyping(false);
      } catch (e) {
        console.error("Failed to create chat:", e);
        setIsTyping(false);
      }
    } else {
      // Add message to existing chat
      const tempUserMsg = { id: `temp-${Date.now()}`, role: "user", content, timestamp: new Date().toISOString() };
      setActiveMessages(prev => [...prev, tempUserMsg]);
      setIsTyping(true);

      try {
        const msgRes = await axios.post(`${API}/chats/${activeChatId}/messages`, { content });
        setActiveMessages(prev => {
          const filtered = prev.filter(m => m.id !== tempUserMsg.id);
          return [...filtered, msgRes.data.user_message, msgRes.data.assistant_message];
        });
        setIsTyping(false);
      } catch (e) {
        console.error("Failed to send message:", e);
        setIsTyping(false);
      }
    }
  }, [activeChatId, selectedModel, isTyping]);

  const handleSuggestionClick = useCallback((suggestion) => {
    sendMessage(`${suggestion.title} ${suggestion.subtitle}`);
  }, [sendMessage]);

  const filteredModels = models.filter(m =>
    m.name.toLowerCase().includes(modelSearch.toLowerCase())
  );

  return (
    <div className="App flex h-screen text-white overflow-hidden" style={{ backgroundColor: settings.mainBg, color: 'var(--text-primary)' }}>
      <Sidebar
        chats={chats}
        activeChatId={activeChatId}
        onSelectChat={selectChat}
        onNewChat={createNewChat}
        onDeleteChat={deleteChat}
        onRenameChat={renameChat}
        isOpen={sidebarOpen}
        onToggle={() => setSidebarOpen(false)}
        onOpenSettings={() => setSettingsOpen(true)}
        onArchiveChat={archiveChat}
        onExportChat={exportChat}
        onImportChat={importChat}
        archivedChats={archivedChats}
        onUnarchiveChat={unarchiveChat}
        onDeleteArchivedChat={deleteArchivedChat}
        onDeleteAllArchived={deleteAllArchived}
        onRefreshArchived={fetchArchivedChats}
        user={user}
        isAdmin={isAdmin}
        onLogout={logout}
        onOpenUserManagement={() => setUserMgmtOpen(true)}
      />

      <div className="flex-1 flex flex-col min-w-0 relative">
        <div className="flex items-center gap-2 p-2 shrink-0">
          {!sidebarOpen && (
            <div className="flex items-center gap-0.5">
              <button onClick={() => setSidebarOpen(true)} className="p-2 rounded-lg hover:bg-white/5 text-neutral-400 hover:text-white transition-colors">
                <PanelLeft size={20} />
              </button>
              <button onClick={createNewChat} className="p-2 rounded-lg hover:bg-white/5 text-neutral-400 hover:text-white transition-colors">
                <SquarePen size={20} />
              </button>
            </div>
          )}

          {selectedModel && (
            <div className="relative">
              <button
                onClick={() => setModelDropdownOpen(!modelDropdownOpen)}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg hover:bg-white/5 transition-colors"
              >
                <span className="text-sm font-medium text-neutral-200">{selectedModel.name}</span>
                <ChevronDown size={14} className="text-neutral-400" />
              </button>

              {modelDropdownOpen && (
                <>
                  <div className="fixed inset-0 z-40" onClick={() => setModelDropdownOpen(false)} />
                  <div className="absolute top-full left-0 mt-1 w-72 bg-[#2f2f2f] rounded-xl shadow-2xl border border-white/10 overflow-hidden z-50">
                    <div className="p-2">
                      <div className="relative">
                        <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-neutral-500" />
                        <input
                          type="text"
                          value={modelSearch}
                          onChange={e => setModelSearch(e.target.value)}
                          placeholder="Search a model"
                          className="w-full bg-[#3a3a3a] text-white text-sm rounded-lg pl-9 pr-3 py-2 outline-none placeholder:text-neutral-500"
                          autoFocus
                        />
                      </div>
                    </div>
                    <div className="max-h-60 overflow-y-auto px-1 pb-1">
                      {filteredModels.map(model => (
                        <button
                          key={model.id}
                          onClick={() => { setSelectedModel(model); setModelDropdownOpen(false); setModelSearch(""); }}
                          className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-sm transition-colors ${
                            selectedModel.id === model.id ? 'bg-white/10 text-white' : 'text-neutral-300 hover:bg-white/5'
                          }`}
                        >
                          <div className="flex flex-col items-start">
                            <span className="font-medium">{model.name}</span>
                            {model.provider && <span className="text-xs text-neutral-500">{model.provider}</span>}
                          </div>
                          {selectedModel.id === model.id && <Check size={16} className="text-white" />}
                        </button>
                      ))}
                    </div>
                  </div>
                </>
              )}
            </div>
          )}
        </div>

        {activeChatId ? (
          <ChatArea messages={activeMessages} isTyping={isTyping} />
        ) : (
          <WelcomeScreen suggestions={suggestions} onSuggestionClick={handleSuggestionClick} />
        )}

        <ChatInput
          onSend={sendMessage}
          isTyping={isTyping}
          placeholder={activeChatId ? "Ask a follow-up..." : "Ask anything"}
        />
      </div>

      <SettingsModal open={settingsOpen} onClose={() => setSettingsOpen(false)} onModelsChanged={fetchModels} isAdmin={isAdmin} />
      {isAdmin && <UserManagement open={userMgmtOpen} onClose={() => setUserMgmtOpen(false)} />}
    </div>
  );
}

function AuthGate() {
  const { user, loading } = useAuth();
  const { settings } = useSettings();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ backgroundColor: settings.mainBg }}>
        <Loader2 size={32} className="animate-spin" style={{ color: settings.accentColor }} />
      </div>
    );
  }

  if (!user) return <AuthPage />;
  return <AppContent />;
}

function App() {
  return (
    <SettingsProvider>
      <AuthProvider>
        <AuthGate />
      </AuthProvider>
    </SettingsProvider>
  );
}

export default App;
