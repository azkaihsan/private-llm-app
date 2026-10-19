import React, { useState } from 'react';
import { Pencil, Pin, PinOff, Download, Archive, Trash2, FolderInput, FolderMinus, Folder, ChevronRight, Check } from 'lucide-react';

const item = "w-full flex items-center gap-3 px-3 py-2.5 hover:bg-white/5 text-neutral-300 text-sm";

const ChatRowMenu = ({ chat, folders, actions, onClose, onRename }) => {
  const [showFolders, setShowFolders] = useState(false);
  const run = (fn) => { fn(); onClose(); };

  const position = (el) => {
    if (!el) return;
    let anchor = el.parentElement;
    while (anchor && getComputedStyle(anchor).display === 'contents') anchor = anchor.parentElement;
    const row = anchor?.getBoundingClientRect();
    if (!row) return;
    const top = Math.min(row.bottom + 4, window.innerHeight - el.offsetHeight - 8);
    el.style.top = `${Math.max(8, top)}px`;
    el.style.left = `${row.left}px`;
  };

  return (
    <>
      <div className="fixed inset-0 z-[100]" onClick={e => { e.stopPropagation(); onClose(); }} />
      <div ref={position} data-testid={`chat-menu-panel-${chat.id}`} onClick={e => e.stopPropagation()}
        className="fixed z-[101] w-52 max-h-[70vh] overflow-y-auto bg-[#2f2f2f] rounded-xl shadow-2xl border border-white/10">
        <button data-testid={`chat-menu-rename-${chat.id}`} onClick={onRename} className={item}><Pencil size={14} /> Rename</button>
        <button data-testid={`chat-menu-pin-${chat.id}`} onClick={() => run(() => chat.pinned ? actions.onUnpin(chat.id) : actions.onPin(chat.id))} className={item}>
          {chat.pinned ? <><PinOff size={14} /> Unpin</> : <><Pin size={14} /> Pin</>}
        </button>
        <button data-testid={`chat-menu-move-${chat.id}`} onClick={() => setShowFolders(!showFolders)} className={item}>
          <FolderInput size={14} /> <span className="flex-1 text-left">Move to folder</span>
          <ChevronRight size={14} className={`transition-transform ${showFolders ? 'rotate-90' : ''}`} />
        </button>
        {showFolders && (
          <div className="bg-black/20 py-1" data-testid={`chat-menu-folder-list-${chat.id}`}>
            {folders.length === 0 && <div className="px-4 py-2 text-xs text-neutral-500">No folders yet</div>}
            {folders.map(f => (
              <button key={f.id} data-testid={`chat-menu-folder-option-${f.id}`} onClick={() => run(() => actions.onMove(chat.id, f.id))}
                className="w-full flex items-center gap-2 pl-6 pr-3 py-2 hover:bg-white/5 text-neutral-300 text-sm">
                <Folder size={13} /> <span className="flex-1 text-left truncate">{f.name}</span>
                {chat.folder_id === f.id && <Check size={13} className="text-green-400" />}
              </button>
            ))}
            {chat.folder_id && (
              <button data-testid={`chat-menu-remove-folder-${chat.id}`} onClick={() => run(() => actions.onMove(chat.id, null))}
                className="w-full flex items-center gap-2 pl-6 pr-3 py-2 hover:bg-white/5 text-neutral-400 text-sm">
                <FolderMinus size={13} /> Remove from folder
              </button>
            )}
          </div>
        )}
        <button data-testid={`chat-menu-export-${chat.id}`} onClick={() => run(() => actions.onExport(chat.id))} className={item}><Download size={14} /> Export Chat</button>
        <button data-testid={`chat-menu-archive-${chat.id}`} onClick={() => run(() => actions.onArchive(chat.id))} className={item}><Archive size={14} /> Archive</button>
        <div className="border-t border-white/10" />
        <button data-testid={`chat-menu-delete-${chat.id}`} onClick={() => { if (window.confirm('Delete this chat?')) run(() => actions.onDelete(chat.id)); }}
          className="w-full flex items-center gap-3 px-3 py-2.5 hover:bg-white/5 text-red-400 text-sm"><Trash2 size={14} /> Delete</button>
      </div>
    </>
  );
};

export default ChatRowMenu;
