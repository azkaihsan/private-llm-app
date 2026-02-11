import React, { useState, useCallback } from "react";
import "@/App.css";
import Sidebar from "@/components/Sidebar";
import WelcomeScreen from "@/components/WelcomeScreen";
import ChatArea from "@/components/ChatArea";
import ChatInput from "@/components/ChatInput";
import { models, initialChats, suggestions, mockResponses } from "@/data/mockData";
import { PanelLeft, SquarePen, ChevronDown, Check, Search } from "lucide-react";

function App() {
  const [chats, setChats] = useState(initialChats);
  const [activeChatId, setActiveChatId] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [selectedModel, setSelectedModel] = useState(models[0]);
  const [isTyping, setIsTyping] = useState(false);
  const [modelDropdownOpen, setModelDropdownOpen] = useState(false);
  const [modelSearch, setModelSearch] = useState("");

  const activeChat = chats.find(c => c.id === activeChatId);

  const createNewChat = useCallback(() => {
    setActiveChatId(null);
    setIsTyping(false);
  }, []);

  const selectChat = useCallback((chatId) => {
    setActiveChatId(chatId);
    setIsTyping(false);
  }, []);

  const deleteChat = useCallback((chatId) => {
    setChats(prev => prev.filter(c => c.id !== chatId));
    if (activeChatId === chatId) setActiveChatId(null);
  }, [activeChatId]);

  const renameChat = useCallback((chatId, newTitle) => {
    setChats(prev => prev.map(c => c.id === chatId ? { ...c, title: newTitle } : c));
  }, []);

  const sendMessage = useCallback((content) => {
    const msgId = `msg-${Date.now()}`;
    const userMsg = { id: msgId, role: "user", content, timestamp: Date.now() };

    if (!activeChatId) {
      const newChatId = `chat-${Date.now()}`;
      const title = content.length > 40 ? content.slice(0, 40) + "..." : content;
      const newChat = {
        id: newChatId,
        title,
        model: selectedModel.id,
        createdAt: Date.now(),
        messages: [userMsg],
      };
      setChats(prev => [newChat, ...prev]);
      setActiveChatId(newChatId);

      setIsTyping(true);
      setTimeout(() => {
        const aiResponse = mockResponses[Math.floor(Math.random() * mockResponses.length)];
        const aiMsg = { id: `msg-${Date.now()}`, role: "assistant", content: aiResponse, timestamp: Date.now() };
        setChats(prev => prev.map(c => c.id === newChatId ? { ...c, messages: [...c.messages, aiMsg] } : c));
        setIsTyping(false);
      }, 1200 + Math.random() * 800);
    } else {
      setChats(prev => prev.map(c =>
        c.id === activeChatId ? { ...c, messages: [...c.messages, userMsg] } : c
      ));

      setIsTyping(true);
      setTimeout(() => {
        const aiResponse = mockResponses[Math.floor(Math.random() * mockResponses.length)];
        const aiMsg = { id: `msg-${Date.now()}`, role: "assistant", content: aiResponse, timestamp: Date.now() };
        setChats(prev => prev.map(c =>
          c.id === activeChatId ? { ...c, messages: [...c.messages, aiMsg] } : c
        ));
        setIsTyping(false);
      }, 1200 + Math.random() * 800);
    }
  }, [activeChatId, selectedModel]);

  const handleSuggestionClick = useCallback((suggestion) => {
    sendMessage(`${suggestion.title} ${suggestion.subtitle}`);
  }, [sendMessage]);

  const filteredModels = models.filter(m =>
    m.name.toLowerCase().includes(modelSearch.toLowerCase())
  );

  return (
    <div className="App flex h-screen bg-[#212121] text-white overflow-hidden">
      {/* Sidebar */}
      <Sidebar
        chats={chats}
        activeChatId={activeChatId}
        onSelectChat={selectChat}
        onNewChat={createNewChat}
        onDeleteChat={deleteChat}
        onRenameChat={renameChat}
        isOpen={sidebarOpen}
        onToggle={() => setSidebarOpen(false)}
      />

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-w-0 relative">
        {/* Top Bar */}
        <div className="flex items-center gap-2 p-2 shrink-0">
          {!sidebarOpen && (
            <div className="flex items-center gap-0.5">
              <button
                onClick={() => setSidebarOpen(true)}
                className="p-2 rounded-lg hover:bg-white/5 text-neutral-400 hover:text-white transition-colors"
              >
                <PanelLeft size={20} />
              </button>
              <button
                onClick={createNewChat}
                className="p-2 rounded-lg hover:bg-white/5 text-neutral-400 hover:text-white transition-colors"
              >
                <SquarePen size={20} />
              </button>
            </div>
          )}

          {/* Model Selector */}
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
                          {model.size && <span className="text-xs text-neutral-500">{model.size}</span>}
                        </div>
                        {selectedModel.id === model.id && <Check size={16} className="text-white" />}
                      </button>
                    ))}
                  </div>
                </div>
              </>
            )}
          </div>
        </div>

        {/* Content */}
        {activeChat ? (
          <ChatArea messages={activeChat.messages} isTyping={isTyping} />
        ) : (
          <WelcomeScreen suggestions={suggestions} onSuggestionClick={handleSuggestionClick} />
        )}

        {/* Input */}
        <ChatInput
          onSend={sendMessage}
          isTyping={isTyping}
          placeholder={activeChat ? "Ask a follow-up..." : "Ask anything"}
        />
      </div>
    </div>
  );
}

export default App;
