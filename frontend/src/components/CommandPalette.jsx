import React, { useState, useEffect, useMemo, useRef } from 'react';
import { Search, MessageSquare, SquarePen, Settings, Archive, Shield, CornerDownLeft, FileText } from 'lucide-react';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export const CommandPalette = ({ open, onClose, chats, actions, onSelectChat, onJumpToMessage }) => {
  const [query, setQuery] = useState('');
  const [msgResults, setMsgResults] = useState([]);
  const [index, setIndex] = useState(0);
  const inputRef = useRef(null);
  const listRef = useRef(null);

  useEffect(() => {
    if (open) { setQuery(''); setMsgResults([]); setIndex(0); setTimeout(() => inputRef.current?.focus(), 30); }
  }, [open]);

  useEffect(() => {
    const q = query.trim();
    if (q.length < 2) { setMsgResults([]); return; }
    const t = setTimeout(async () => {
      try {
        const res = await axios.get(`${API}/chats/search`, { params: { q } });
        setMsgResults(res.data);
      } catch (e) { console.error('Palette search failed:', e); }
    }, 250);
    return () => clearTimeout(t);
  }, [query]);

  const items = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return actions.map(a => ({ type: 'action', key: `a-${a.id}`, ...a }));
    const titleMatches = chats.filter(c => c.title.toLowerCase().includes(q)).slice(0, 8)
      .map(c => ({ type: 'chat', key: `c-${c.id}`, chatId: c.id, label: c.title }));
    const titles = Object.fromEntries(chats.map(c => [c.id, c.title]));
    const messageMatches = msgResults.slice(0, 8)
      .map(r => ({ type: 'message', key: `m-${r.chat_id}`, chatId: r.chat_id, label: titles[r.chat_id] || 'Chat', snippet: r.snippet, count: r.count }));
    const actionMatches = actions.filter(a => a.label.toLowerCase().includes(q))
      .map(a => ({ type: 'action', key: `a-${a.id}`, ...a }));
    return [...titleMatches, ...messageMatches, ...actionMatches];
  }, [query, chats, msgResults, actions]);

  useEffect(() => { setIndex(0); }, [items.length, query]);

  useEffect(() => {
    listRef.current?.querySelector(`[data-index="${index}"]`)?.scrollIntoView({ block: 'nearest' });
  }, [index]);

  const run = (item) => {
    if (!item) return;
    if (item.type === 'chat') onSelectChat(item.chatId);
    else if (item.type === 'message') onJumpToMessage(item.chatId, query.trim());
    else item.run();
    onClose();
  };

  const onKeyDown = (e) => {
    if (e.key === 'ArrowDown') { e.preventDefault(); setIndex(i => Math.min(i + 1, items.length - 1)); }
    else if (e.key === 'ArrowUp') { e.preventDefault(); setIndex(i => Math.max(i - 1, 0)); }
    else if (e.key === 'Enter') { e.preventDefault(); run(items[index]); }
    else if (e.key === 'Escape') onClose();
  };

  if (!open) return null;

  const sections = [
    { type: 'chat', title: 'Chats', icon: MessageSquare },
    { type: 'message', title: 'Messages', icon: FileText },
    { type: 'action', title: query.trim() ? 'Actions' : 'Quick actions', icon: null },
  ];

  return (
    <div data-testid="command-palette-overlay" className="fixed inset-0 z-[60] bg-black/60 flex items-start justify-center pt-[12vh] px-4" onClick={onClose}>
      <div
        data-testid="command-palette"
        className="w-full max-w-xl bg-[#2f2f2f] border border-white/10 rounded-2xl shadow-2xl overflow-hidden"
        onClick={e => e.stopPropagation()}
      >
        <div className="flex items-center gap-3 px-4 py-3 border-b border-white/10">
          <Search size={18} className="text-neutral-500 shrink-0" />
          <input
            ref={inputRef}
            data-testid="command-palette-input"
            value={query}
            onChange={e => setQuery(e.target.value)}
            onKeyDown={onKeyDown}
            placeholder="Search chats, messages, or actions..."
            className="flex-1 bg-transparent text-white text-base outline-none placeholder:text-neutral-500"
          />
          <kbd className="text-[10px] px-1.5 py-0.5 rounded border border-white/15 text-neutral-400">ESC</kbd>
        </div>

        <div ref={listRef} className="max-h-[50vh] overflow-y-auto py-2">
          {items.length === 0 && (
            <div data-testid="command-palette-empty" className="px-4 py-8 text-center text-sm text-neutral-500">No results</div>
          )}
          {sections.map(sec => {
            const secItems = items.filter(i => i.type === sec.type);
            if (!secItems.length) return null;
            return (
              <div key={sec.type} className="mb-1">
                <div className="px-4 py-1.5 text-[11px] font-medium uppercase tracking-wider text-neutral-500">{sec.title}</div>
                {secItems.map(item => {
                  const i = items.indexOf(item);
                  const Icon = item.icon || sec.icon || MessageSquare;
                  const active = i === index;
                  return (
                    <button
                      key={item.key}
                      data-index={i}
                      data-testid={`palette-item-${item.type}-${item.chatId || item.id}`}
                      onMouseEnter={() => setIndex(i)}
                      onClick={() => run(item)}
                      className={`w-full flex items-center gap-3 px-4 py-2.5 text-left transition-colors ${active ? 'bg-white/10' : 'hover:bg-white/5'}`}
                    >
                      <Icon size={16} className={active ? 'text-white' : 'text-neutral-400'} />
                      <div className="flex-1 min-w-0">
                        <div className={`text-sm truncate ${active ? 'text-white' : 'text-neutral-200'}`}>{item.label}</div>
                        {item.snippet && <div className="text-xs text-neutral-500 truncate mt-0.5">{item.snippet}</div>}
                      </div>
                      {item.count > 1 && <span className="text-[10px] text-neutral-500">{item.count} matches</span>}
                      {active && <CornerDownLeft size={14} className="text-neutral-500" />}
                    </button>
                  );
                })}
              </div>
            );
          })}
        </div>

        <div className="flex items-center gap-4 px-4 py-2 border-t border-white/10 text-[11px] text-neutral-500">
          <span><kbd className="px-1 rounded border border-white/15">↑</kbd> <kbd className="px-1 rounded border border-white/15">↓</kbd> navigate</span>
          <span><kbd className="px-1 rounded border border-white/15">↵</kbd> open</span>
          <span className="ml-auto">Ctrl+K</span>
        </div>
      </div>
    </div>
  );
};

export const paletteIcons = { SquarePen, Settings, Archive, Shield };
export default CommandPalette;
