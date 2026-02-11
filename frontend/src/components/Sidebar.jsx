import React, { useState } from 'react';
import {
  Plus, Search, MessageSquare, Pencil, Trash2,
  PanelLeft, Folder, Settings, LogOut, CircleUser,
  SquarePen, EllipsisVertical, X, Archive, ChevronDown
} from 'lucide-react';
import { ScrollArea } from '@/components/ui/scroll-area';

const Sidebar = ({
  chats, activeChatId, onSelectChat, onNewChat, onDeleteChat,
  onRenameChat, isOpen, onToggle
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchOpen, setSearchOpen] = useState(false);
  const [editingChatId, setEditingChatId] = useState(null);
  const [editTitle, setEditTitle] = useState('');
  const [hoveredChatId, setHoveredChatId] = useState(null);
  const [showUserMenu, setShowUserMenu] = useState(false);

  const groupChatsByDate = (chatList) => {
    const groups = { 'Today': [], 'Yesterday': [], 'Previous 7 Days': [], 'Previous 30 Days': [], 'Older': [] };
    chatList.forEach(chat => {
      const days = (Date.now() - chat.createdAt) / 86400000;
      if (days < 1) groups['Today'].push(chat);
      else if (days < 2) groups['Yesterday'].push(chat);
      else if (days < 7) groups['Previous 7 Days'].push(chat);
      else if (days < 30) groups['Previous 30 Days'].push(chat);
      else groups['Older'].push(chat);
    });
    return Object.entries(groups).filter(([, items]) => items.length > 0);
  };

  const filteredChats = chats.filter(c =>
    c.title.toLowerCase().includes(searchQuery.toLowerCase())
  );
  const groupedChats = groupChatsByDate(filteredChats);

  const handleStartRename = (e, chat) => {
    e.stopPropagation();
    setEditingChatId(chat.id);
    setEditTitle(chat.title);
  };

  const handleFinishRename = (chatId) => {
    if (editTitle.trim()) onRenameChat(chatId, editTitle.trim());
    setEditingChatId(null);
  };

  if (!isOpen) return null;

  return (
    <div className="w-[260px] h-full bg-[#171717] flex flex-col relative shrink-0 transition-all duration-300">
      {/* Header */}
      <div className="flex items-center justify-between p-2 pt-3">
        <button
          onClick={onToggle}
          className="p-2 rounded-lg hover:bg-white/5 text-neutral-400 hover:text-white transition-colors"
          title="Close sidebar"
        >
          <PanelLeft size={20} />
        </button>
        <div className="flex items-center gap-0.5">
          <button
            onClick={() => setSearchOpen(!searchOpen)}
            className="p-2 rounded-lg hover:bg-white/5 text-neutral-400 hover:text-white transition-colors"
          >
            <Search size={20} />
          </button>
          <button
            onClick={onNewChat}
            className="p-2 rounded-lg hover:bg-white/5 text-neutral-400 hover:text-white transition-colors"
            title="New Chat"
          >
            <SquarePen size={20} />
          </button>
        </div>
      </div>

      {/* Search */}
      {searchOpen && (
        <div className="px-2 pb-2">
          <div className="relative">
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-neutral-500" />
            <input
              type="text"
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              placeholder="Search chats..."
              className="w-full bg-[#2f2f2f] text-white text-sm rounded-lg pl-9 pr-8 py-2 outline-none placeholder:text-neutral-500 focus:ring-1 focus:ring-neutral-600"
              autoFocus
            />
            {searchQuery && (
              <button onClick={() => { setSearchQuery(''); setSearchOpen(false); }}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-neutral-500 hover:text-white">
                <X size={14} />
              </button>
            )}
          </div>
        </div>
      )}

      {/* Chat List */}
      <ScrollArea className="flex-1 px-2">
        <div className="pb-2">
          {groupedChats.map(([group, items]) => (
            <div key={group} className="mb-1">
              <div className="px-2 py-2 text-[11px] font-medium text-neutral-500 uppercase tracking-wider">
                {group}
              </div>
              {items.map(chat => (
                <div
                  key={chat.id}
                  className={`group relative flex items-center rounded-lg cursor-pointer mb-0.5 transition-colors ${
                    activeChatId === chat.id
                      ? 'bg-[#212121]'
                      : 'hover:bg-white/5'
                  }`}
                  onClick={() => onSelectChat(chat.id)}
                  onMouseEnter={() => setHoveredChatId(chat.id)}
                  onMouseLeave={() => setHoveredChatId(null)}
                >
                  {editingChatId === chat.id ? (
                    <input
                      type="text"
                      value={editTitle}
                      onChange={e => setEditTitle(e.target.value)}
                      onBlur={() => handleFinishRename(chat.id)}
                      onKeyDown={e => { if (e.key === 'Enter') handleFinishRename(chat.id); if (e.key === 'Escape') setEditingChatId(null); }}
                      className="flex-1 bg-transparent text-white text-sm py-2 px-3 outline-none"
                      autoFocus
                      onClick={e => e.stopPropagation()}
                    />
                  ) : (
                    <>
                      <span className="flex-1 text-sm text-neutral-200 truncate py-2 px-3">
                        {chat.title}
                      </span>
                      {(hoveredChatId === chat.id || activeChatId === chat.id) && (
                        <div className="flex items-center gap-0.5 pr-1 shrink-0">
                          <button
                            onClick={e => handleStartRename(e, chat)}
                            className="p-1 rounded hover:bg-white/10 text-neutral-400 hover:text-white transition-colors"
                          >
                            <Pencil size={14} />
                          </button>
                          <button
                            onClick={e => { e.stopPropagation(); onDeleteChat(chat.id); }}
                            className="p-1 rounded hover:bg-white/10 text-neutral-400 hover:text-red-400 transition-colors"
                          >
                            <Trash2 size={14} />
                          </button>
                        </div>
                      )}
                    </>
                  )}
                </div>
              ))}
            </div>
          ))}
          {filteredChats.length === 0 && (
            <div className="text-center text-neutral-500 text-sm py-8">No chats found</div>
          )}
        </div>
      </ScrollArea>

      {/* Workspace & User */}
      <div className="border-t border-white/5 p-2">
        <button className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg hover:bg-white/5 text-neutral-300 hover:text-white transition-colors">
          <Folder size={18} />
          <span className="text-sm">Workspace</span>
        </button>
        <div className="relative">
          <button
            onClick={() => setShowUserMenu(!showUserMenu)}
            className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg hover:bg-white/5 text-neutral-300 hover:text-white transition-colors"
          >
            <div className="w-7 h-7 rounded-full bg-gradient-to-br from-amber-500 to-orange-600 flex items-center justify-center text-white text-xs font-semibold">
              U
            </div>
            <span className="text-sm flex-1 text-left">User</span>
            <EllipsisVertical size={16} className="text-neutral-500" />
          </button>
          {showUserMenu && (
            <div className="absolute bottom-full left-0 w-full mb-1 bg-[#2f2f2f] rounded-xl shadow-xl border border-white/10 overflow-hidden z-50">
              <button className="w-full flex items-center gap-3 px-3 py-2.5 hover:bg-white/5 text-neutral-300 text-sm">
                <Settings size={16} /> Settings
              </button>
              <button className="w-full flex items-center gap-3 px-3 py-2.5 hover:bg-white/5 text-neutral-300 text-sm">
                <Archive size={16} /> Archived Chats
              </button>
              <div className="border-t border-white/10" />
              <button className="w-full flex items-center gap-3 px-3 py-2.5 hover:bg-white/5 text-red-400 text-sm">
                <LogOut size={16} /> Sign Out
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Sidebar;
