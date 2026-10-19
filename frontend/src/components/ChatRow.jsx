import React, { useState } from 'react';
import { MoreHorizontal, Pin, PinOff } from 'lucide-react';
import ChatRowMenu from '@/components/ChatRowMenu';

const ChatRow = ({ chat, isActive, snippet, folders, actions, onDragStart, onDragEnd }) => {
  const [hovered, setHovered] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const [editing, setEditing] = useState(false);
  const [title, setTitle] = useState(chat.title);
  const showActions = isActive || hovered || menuOpen;

  const finishRename = () => {
    if (title.trim() && title.trim() !== chat.title) actions.onRename(chat.id, title.trim());
    setEditing(false);
  };
  const togglePin = (e) => { e.stopPropagation(); chat.pinned ? actions.onUnpin(chat.id) : actions.onPin(chat.id); };

  return (
    <div
      data-testid={`chat-row-${chat.id}`}
      draggable={!editing}
      onDragStart={e => { e.dataTransfer.setData('text/chat-id', chat.id); e.dataTransfer.effectAllowed = 'move'; onDragStart(chat.id); }}
      onDragEnd={onDragEnd}
      className={`group relative rounded-lg cursor-pointer mb-0.5 transition-colors ${isActive ? 'bg-[#212121]' : 'hover:bg-white/5'}`}
      onClick={() => actions.onSelect(chat.id)}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      {editing ? (
        <input
          data-testid={`chat-rename-input-${chat.id}`}
          value={title}
          onChange={e => setTitle(e.target.value)}
          onBlur={finishRename}
          onKeyDown={e => { if (e.key === 'Enter') finishRename(); if (e.key === 'Escape') setEditing(false); }}
          className="w-full bg-transparent text-white text-sm py-2 px-3 outline-none"
          autoFocus
          onClick={e => e.stopPropagation()}
        />
      ) : (
        <div className="flex items-center">
          <div className="flex-1 min-w-0 py-2 px-3">
            <span data-testid={`chat-item-${chat.id}`} className="block text-sm text-neutral-200 truncate">{chat.title}</span>
            {snippet && <span data-testid={`chat-snippet-${chat.id}`} className="block text-[11px] text-neutral-500 truncate mt-0.5">{snippet}</span>}
          </div>
          {showActions && (
            <button data-testid={`chat-pin-toggle-${chat.id}`} title={chat.pinned ? 'Unpin' : 'Pin'} onClick={togglePin}
              className="shrink-0 p-1.5 rounded-md text-neutral-400 hover:text-white hover:bg-white/10 transition-colors">
              {chat.pinned ? <PinOff size={14} /> : <Pin size={14} />}
            </button>
          )}
          {showActions && (
            <button data-testid={`chat-menu-${chat.id}`} onClick={e => { e.stopPropagation(); setMenuOpen(!menuOpen); }}
              className="shrink-0 p-1.5 mr-1 rounded-md text-neutral-400 hover:text-white hover:bg-white/10 transition-colors">
              <MoreHorizontal size={16} />
            </button>
          )}
        </div>
      )}
      {menuOpen && (
        <ChatRowMenu chat={chat} folders={folders} actions={actions}
          onClose={() => { setMenuOpen(false); setHovered(false); }}
          onRename={() => { setTitle(chat.title); setEditing(true); setMenuOpen(false); }} />
      )}
    </div>
  );
};

export default ChatRow;
