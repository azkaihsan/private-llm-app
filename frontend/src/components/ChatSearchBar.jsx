import React, { useEffect, useRef } from 'react';
import { Search, ChevronUp, ChevronDown, X } from 'lucide-react';

export const ChatSearchBar = ({ term, onTermChange, matchCount, currentIndex, onPrev, onNext, onClose }) => {
  const inputRef = useRef(null);
  useEffect(() => { inputRef.current?.focus(); }, []);

  const handleKeyDown = (e) => {
    if (e.key === 'Escape') onClose();
    if (e.key === 'Enter') { e.preventDefault(); e.shiftKey ? onPrev() : onNext(); }
  };

  return (
    <div data-testid="chat-search-bar" className="flex items-center gap-1 bg-[#2f2f2f] border border-white/10 rounded-lg pl-2 pr-1 py-1 shadow-lg">
      <Search size={14} className="text-neutral-500 shrink-0" />
      <input
        ref={inputRef}
        data-testid="chat-search-input"
        type="text"
        value={term}
        onChange={e => onTermChange(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Search in chat"
        className="bg-transparent text-white text-sm outline-none w-44 placeholder:text-neutral-500"
      />
      <span data-testid="chat-search-count" className="text-xs text-neutral-400 tabular-nums px-1 whitespace-nowrap">
        {term ? (matchCount ? `${currentIndex + 1}/${matchCount}` : '0/0') : ''}
      </span>
      <button data-testid="chat-search-prev" onClick={onPrev} disabled={!matchCount} className="p-1 rounded text-neutral-400 hover:text-white hover:bg-white/10 disabled:opacity-30">
        <ChevronUp size={14} />
      </button>
      <button data-testid="chat-search-next" onClick={onNext} disabled={!matchCount} className="p-1 rounded text-neutral-400 hover:text-white hover:bg-white/10 disabled:opacity-30">
        <ChevronDown size={14} />
      </button>
      <button data-testid="chat-search-close" onClick={onClose} className="p-1 rounded text-neutral-400 hover:text-white hover:bg-white/10">
        <X size={14} />
      </button>
    </div>
  );
};

export default ChatSearchBar;
