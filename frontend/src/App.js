import React, { useState, useCallback, useEffect, useMemo, useRef } from "react";
import "@/App.css";
import Sidebar from "@/components/Sidebar";
import WelcomeScreen from "@/components/WelcomeScreen";
import ChatArea from "@/components/ChatArea";
import ChatInput from "@/components/ChatInput";
import SettingsModal from "@/components/SettingsModal";
import AuthPage from "@/components/AuthPage";
import UserManagement from "@/components/UserManagement";
import ChatSearchBar from "@/components/ChatSearchBar";
import CommandPalette, { paletteIcons } from "@/components/CommandPalette";
import { SettingsProvider, useSettings } from "@/context/SettingsContext";
import { AuthProvider, useAuth } from "@/context/AuthContext";
import { suggestions } from "@/data/mockData";
import { PanelLeft, SquarePen, ChevronDown, Check, Search, Loader2, FolderOpen, X } from "lucide-react";
import axios from "axios";
import { Toaster } from "sonner";
import { useFolders } from "@/hooks/useFolders";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function AppContent() {
  const { settings } = useSettings();
  const { user, isAdmin } = useAuth();
  const [chats, setChats] = useState([]);
  const [activeChatId, setActiveChatId] = useState(null);
  const folderApi = useFolders(user?.id, setChats);
  const [pendingFolderId, setPendingFolderId] = useState(null);
  const pendingFolder = folderApi.folders.find(f => f.id === pendingFolderId);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [selectedModel, setSelectedModel] = useState(null);
  const [models, setModels] = useState([]);
  const [isTyping, setIsTyping] = useState(false);
  const [modelDropdownOpen, setModelDropdownOpen] = useState(false);
  const [modelSearch, setModelSearch] = useState("");
  const [activeMessages, setActiveMessages] = useState([]);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [userMgmtOpen, setUserMgmtOpen] = useState(false);
  const activeChatRef = useRef(null);
  const skipFetchRef = useRef(null);
  useEffect(() => { activeChatRef.current = activeChatId; }, [activeChatId]);
  const [chatSearchOpen, setChatSearchOpen] = useState(false);
  const [chatSearchTerm, setChatSearchTerm] = useState("");
  const [chatSearchIndex, setChatSearchIndex] = useState(0);

  const chatSearchMatches = useMemo(() => {
    const t = chatSearchTerm.trim().toLowerCase();
    if (!t) return [];
    return activeMessages.filter(m => m.content?.toLowerCase().includes(t)).map(m => m.id);
  }, [activeMessages, chatSearchTerm]);
  useEffect(() => { setChatSearchIndex(0); }, [chatSearchTerm, activeChatId]);
  useEffect(() => {
    const onKey = (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'f' && activeChatId) {
        e.preventDefault();
        setChatSearchOpen(true);
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [activeChatId]);
  const closeChatSearch = () => { setChatSearchOpen(false); setChatSearchTerm(""); };

  // Command palette (Ctrl/Cmd+K)
  const [paletteOpen, setPaletteOpen] = useState(false);
  const [archivedRequest, setArchivedRequest] = useState(0);
  useEffect(() => {
    const onKey = (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        setPaletteOpen(o => !o);
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, []);
  const jumpToMessage = useCallback((chatId, term) => {
    setActiveChatId(chatId);
    setIsTyping(false);
    setChatSearchTerm(term);
    setChatSearchOpen(true);
  }, []);
  const paletteActions = useMemo(() => [
    { id: 'new-chat', label: 'New Chat', icon: paletteIcons.SquarePen, run: () => createNewChat() },
    { id: 'settings', label: 'Open Settings', icon: paletteIcons.Settings, run: () => setSettingsOpen(true) },
    { id: 'archived', label: 'Archived Chats', icon: paletteIcons.Archive, run: () => setArchivedRequest(n => n + 1) },
    ...(isAdmin ? [{ id: 'admin', label: 'Admin Panel', icon: paletteIcons.Shield, run: () => setUserMgmtOpen(true) }] : []),
  ], [isAdmin]);
  const stepMatch = (dir) => {
    if (!chatSearchMatches.length) return;
    setChatSearchIndex(i => (i + dir + chatSearchMatches.length) % chatSearchMatches.length);
  };

  // Fetch models on mount
  const fetchModels = useCallback(async () => {
    try {
      const res = await axios.get(`${API}/models`);
      const enabledModels = res.data.filter(m => m.enabled !== false);
      setModels(enabledModels);
      let defaultModelId = null;
      if (isAdmin) {
        try {
          const connRes = await axios.get(`${API}/connections`);
          defaultModelId = connRes.data?.defaultModel;
        } catch (e) { /* non-admin or no connections */ }
      }
      const defaultModel = enabledModels.find(m => m.id === defaultModelId);
      if (defaultModel) setSelectedModel(defaultModel);
      else if (enabledModels.length > 0) setSelectedModel(prev => prev || enabledModels[0]);
    } catch (e) {
      console.error("Failed to fetch models:", e);
    }
  }, [isAdmin]);

  useEffect(() => { fetchModels(); }, [fetchModels]);

  // Fetch chats on mount / user change
  useEffect(() => {
    setActiveChatId(null);
    setActiveMessages([]);
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
  }, [user?.id]);

  // Fetch messages when active chat changes
  useEffect(() => {
    if (!activeChatId) { setActiveMessages([]); return; }
    if (skipFetchRef.current === activeChatId) { skipFetchRef.current = null; return; }
    let cancelled = false;
    const fetchMessages = async () => {
      try {
        const res = await axios.get(`${API}/chats/${activeChatId}`);
        if (!cancelled) setActiveMessages(res.data.messages || []);
      } catch (e) {
        console.error("Failed to fetch chat:", e);
        if (!cancelled && e.response?.status === 404) {
          setChats(prev => prev.filter(c => c.id !== activeChatId));
          setActiveChatId(null);
        }
      }
    };
    fetchMessages();
    return () => { cancelled = true; };
  }, [activeChatId]);

  const createNewChat = useCallback(() => {
    setActiveChatId(null);
    setActiveMessages([]);
    setIsTyping(false);
    setPendingFolderId(null);
  }, []);

  const startChatInFolder = useCallback((folderId) => {
    createNewChat();
    setPendingFolderId(folderId);
  }, [createNewChat]);

  const selectChat = useCallback((chatId) => {
    setPendingFolderId(null);
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

  const setPinned = useCallback(async (chatId, pinned) => {
    try {
      await axios.put(`${API}/chats/${chatId}/${pinned ? 'pin' : 'unpin'}`);
      setChats(prev => prev.map(c => c.id === chatId ? { ...c, pinned } : c));
    } catch (e) { console.error("Failed to update pin:", e); }
  }, []);
  const pinChat = useCallback((id) => setPinned(id, true), [setPinned]);
  const unpinChat = useCallback((id) => setPinned(id, false), [setPinned]);

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
        const res = await axios.post(`${API}/chats`, { title, model: modelId, folder_id: pendingFolder?.id || null });
        setPendingFolderId(null);
        const newChat = { ...res.data, createdAt: new Date(res.data.created_at).getTime() };
        setChats(prev => [newChat, ...prev]);
        skipFetchRef.current = newChat.id;
        setActiveChatId(newChat.id);

        // Optimistic: show user message immediately
        const tempUserMsg = { id: `temp-${Date.now()}`, role: "user", content, timestamp: new Date().toISOString() };
        setActiveMessages([tempUserMsg]);
        setIsTyping(true);

        // Send message to backend
        const msgRes = await axios.post(`${API}/chats/${newChat.id}/messages`, { content });
        if (activeChatRef.current === newChat.id) {
          setActiveMessages([msgRes.data.user_message, msgRes.data.assistant_message]);
          setIsTyping(false);
        }
      } catch (e) {
        console.error("Failed to create chat:", e);
        setIsTyping(false);
        setActiveMessages(prev => [...prev, { id: `err-${Date.now()}`, role: "assistant", content: "Failed to send message. Please try again." }]);
      }
    } else {
      // Add message to existing chat
      const tempUserMsg = { id: `temp-${Date.now()}`, role: "user", content, timestamp: new Date().toISOString() };
      setActiveMessages(prev => [...prev, tempUserMsg]);
      setIsTyping(true);

      try {
        const msgRes = await axios.post(`${API}/chats/${activeChatId}/messages`, { content });
        if (activeChatRef.current !== activeChatId) return;
        setActiveMessages(prev => {
          const filtered = prev.filter(m => m.id !== tempUserMsg.id);
          return [...filtered, msgRes.data.user_message, msgRes.data.assistant_message];
        });
        setIsTyping(false);
      } catch (e) {
        console.error("Failed to send message:", e);
        if (activeChatRef.current !== activeChatId) return;
        setIsTyping(false);
        setActiveMessages(prev => [...prev, { id: `err-${Date.now()}`, role: "assistant", content: "Failed to send message. Please try again." }]);
      }
    }
  }, [activeChatId, selectedModel, isTyping, pendingFolder]);

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
        onOpenUserManagement={() => setUserMgmtOpen(true)}
        onOpenPalette={() => setPaletteOpen(true)}
        archivedRequest={archivedRequest}
        onArchiveChat={archiveChat}
        onPinChat={pinChat}
        onUnpinChat={unpinChat}
        onExportChat={exportChat}
        onImportChat={importChat}
        archivedChats={archivedChats}
        onUnarchiveChat={unarchiveChat}
        onDeleteArchivedChat={deleteArchivedChat}
        onDeleteAllArchived={deleteAllArchived}
        onRefreshArchived={fetchArchivedChats}
        folders={folderApi.folders}
        onCreateFolder={folderApi.createFolder}
        onRenameFolder={folderApi.renameFolder}
        onUpdateFolder={folderApi.updateFolder}
        onReorderFolder={folderApi.reorderFolder}
        onDeleteFolder={folderApi.deleteFolder}
        onMoveChat={folderApi.moveChat}
        onNewChatInFolder={startChatInFolder}
        pendingFolderId={pendingFolder?.id || null}
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

          {!activeChatId && pendingFolder && (
            <div data-testid="pending-folder-badge" className="flex items-center gap-1.5 pl-2.5 pr-1 py-1 rounded-full bg-white/[0.06] border border-white/10 text-xs text-neutral-300">
              <FolderOpen size={13} className="text-neutral-400" />
              <span>New chat in <span data-testid="pending-folder-name" className="font-medium text-white">{pendingFolder.name}</span></span>
              <button data-testid="pending-folder-clear" title="Don't add to folder" onClick={() => setPendingFolderId(null)}
                className="p-0.5 rounded-full text-neutral-500 hover:text-white hover:bg-white/10 transition-colors"><X size={12} /></button>
            </div>
          )}

          {activeChatId && (
            <div className="ml-auto flex items-center">
              {chatSearchOpen ? (
                <ChatSearchBar
                  term={chatSearchTerm}
                  onTermChange={setChatSearchTerm}
                  matchCount={chatSearchMatches.length}
                  currentIndex={chatSearchIndex}
                  onPrev={() => stepMatch(-1)}
                  onNext={() => stepMatch(1)}
                  onClose={closeChatSearch}
                />
              ) : (
                <button
                  data-testid="chat-search-toggle"
                  onClick={() => setChatSearchOpen(true)}
                  title="Search in chat (Ctrl+F)"
                  className="p-2 rounded-lg hover:bg-white/5 text-neutral-400 hover:text-white transition-colors"
                >
                  <Search size={18} />
                </button>
              )}
            </div>
          )}
        </div>

        {activeChatId ? (
          <ChatArea
            messages={activeMessages}
            isTyping={isTyping}
            searchTerm={chatSearchOpen ? chatSearchTerm.trim() : ""}
            currentMatchId={chatSearchOpen ? chatSearchMatches[chatSearchIndex] || null : null}
          />
        ) : (
          <WelcomeScreen suggestions={suggestions} onSuggestionClick={handleSuggestionClick} />
        )}

        <ChatInput
          onSend={sendMessage}
          isTyping={isTyping}
          placeholder={activeChatId ? "Ask a follow-up..." : "Ask anything"}
        />
      </div>

      <SettingsModal open={settingsOpen} onClose={() => setSettingsOpen(false)} onModelsChanged={fetchModels} />
      {isAdmin && <UserManagement open={userMgmtOpen} onClose={() => setUserMgmtOpen(false)} />}
      <CommandPalette
        open={paletteOpen}
        onClose={() => setPaletteOpen(false)}
        chats={chats}
        actions={paletteActions}
        onSelectChat={selectChat}
        onJumpToMessage={jumpToMessage}
      />
      <Toaster theme="dark" position="bottom-right" richColors />
    </div>
  );
}

function AuthGate() {
  const { user, loading } = useAuth();
  const { settings, applyLocalTheme } = useSettings();
  useEffect(() => { applyLocalTheme(user?.id); }, [user?.id, applyLocalTheme]);
  if (loading) {
    return (
      <div data-testid="auth-loading" className="h-screen flex items-center justify-center" style={{ backgroundColor: settings.mainBg }}>
        <Loader2 size={28} className="animate-spin" style={{ color: 'var(--text-muted)' }} />
      </div>
    );
  }
  return user ? <AppContent /> : <AuthPage />;
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
