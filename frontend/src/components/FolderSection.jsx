import React, { useState } from 'react';
import { folderIcon } from '@/components/folderStyles';
import { ChevronRight, Pencil, Trash2, ScrollText, SlidersHorizontal, Plus } from 'lucide-react';

export const useDropZone = (onDropChat) => {
  const [over, setOver] = useState(false);
  return {
    over,
    props: {
      onDragOver: e => { if (e.dataTransfer.types.includes('text/chat-id')) { e.preventDefault(); e.dataTransfer.dropEffect = 'move'; setOver(true); } },
      onDragLeave: e => { if (!e.currentTarget.contains(e.relatedTarget)) setOver(false); },
      onDrop: e => { e.preventDefault(); setOver(false); const id = e.dataTransfer.getData('text/chat-id'); if (id) onDropChat(id); },
    },
  };
};

const FolderSection = ({ folder, count, collapsed, onToggle, onRename, onEditSettings, onDelete, onDropChat, onNewChat, isPending, reorderable, draggingFolderId, onFolderDrag, onReorder, children }) => {
  const [editing, setEditing] = useState(false);
  const [name, setName] = useState(folder.name);
  const drop = useDropZone(onDropChat);
  const [dropPlace, setDropPlace] = useState(null);
  const folderDragOver = draggingFolderId && draggingFolderId !== folder.id;

  const handleDragOver = (e) => {
    if (!folderDragOver || !e.dataTransfer.types.includes('text/folder-id')) return drop.props.onDragOver(e);
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    const r = e.currentTarget.getBoundingClientRect();
    setDropPlace(e.clientY < r.top + Math.min(r.height, 36) / 2 ? 'before' : 'after');
  };
  const handleDrop = (e) => {
    if (!e.dataTransfer.types.includes('text/folder-id')) return drop.props.onDrop(e);
    e.preventDefault();
    const id = e.dataTransfer.getData('text/folder-id');
    if (id && id !== folder.id && dropPlace) onReorder(id, folder.id, dropPlace);
    setDropPlace(null);
  };
  const handleDragLeave = (e) => { drop.props.onDragLeave(e); if (!e.currentTarget.contains(e.relatedTarget)) setDropPlace(null); };

  const finish = () => {
    const n = name.trim();
    if (n && n !== folder.name) onRename(folder.id, n);
    else setName(folder.name);
    setEditing(false);
  };

  return (
    <div data-testid={`folder-${folder.id}`} onDragOver={handleDragOver} onDrop={handleDrop} onDragLeave={handleDragLeave}
      className={`relative rounded-lg mb-0.5 transition-[background-color,opacity] ${drop.over ? 'bg-white/[0.07] ring-1 ring-white/20' : ''} ${draggingFolderId === folder.id ? 'opacity-40' : ''}`}>
      {folderDragOver && dropPlace && (
        <div data-testid={`folder-drop-indicator-${dropPlace}-${folder.id}`}
          className={`absolute left-1 right-1 h-0.5 rounded-full bg-sky-400 pointer-events-none z-10 ${dropPlace === 'before' ? '-top-px' : '-bottom-px'}`} />
      )}
      <div data-testid={`folder-header-${folder.id}`} onClick={() => !editing && onToggle(folder.id)}
        draggable={reorderable && !editing}
        onDragStart={e => { e.dataTransfer.setData('text/folder-id', folder.id); e.dataTransfer.effectAllowed = 'move'; onFolderDrag(folder.id); }}
        onDragEnd={() => onFolderDrag(null)}
        className={`group flex items-center gap-1.5 px-2 py-2 rounded-lg cursor-pointer hover:bg-white/5 text-neutral-300 ${isPending ? 'bg-white/[0.06]' : ''}`}>
        <ChevronRight size={13} className={`shrink-0 text-neutral-500 transition-transform duration-200 ${collapsed ? '' : 'rotate-90'}`} />
        {React.createElement(folderIcon(folder, !collapsed), { size: 15, className: 'shrink-0', 'data-testid': `folder-icon-display-${folder.id}`, style: folder.color ? { color: folder.color } : undefined })}
        {editing ? (
          <input data-testid={`folder-rename-input-${folder.id}`} value={name} maxLength={60} autoFocus
            onChange={e => setName(e.target.value)} onBlur={finish} onClick={e => e.stopPropagation()}
            onKeyDown={e => { if (e.key === 'Enter') finish(); if (e.key === 'Escape') { setName(folder.name); setEditing(false); } }}
            className="flex-1 min-w-0 bg-[#2f2f2f] text-white text-sm rounded px-1.5 py-0.5 outline-none" />
        ) : (
          <span data-testid={`folder-name-${folder.id}`} className="flex-1 min-w-0 text-sm truncate">{folder.name}</span>
        )}
        {!editing && folder.instructions && (
          <span data-testid={`folder-instructions-indicator-${folder.id}`} title="Has folder instructions" className="shrink-0 text-amber-400/80 group-hover:hidden">
            <ScrollText size={12} />
          </span>
        )}
        {!editing && <span data-testid={`folder-count-${folder.id}`} className="text-[11px] text-neutral-500 group-hover:hidden">{count}</span>}
        {!editing && (
          <div className="hidden group-hover:flex items-center gap-0.5">
            <button data-testid={`folder-new-chat-${folder.id}`} title="New chat in folder" onClick={e => { e.stopPropagation(); onNewChat(folder.id); }}
              className="p-1 rounded text-neutral-400 hover:text-white hover:bg-white/10"><Plus size={12} /></button>
            <button data-testid={`folder-edit-instructions-${folder.id}`} title="Edit instructions" onClick={e => { e.stopPropagation(); onEditSettings(folder.id); }}
              className="p-1 rounded text-neutral-400 hover:text-white hover:bg-white/10"><SlidersHorizontal size={12} /></button>
            <button data-testid={`folder-rename-${folder.id}`} title="Rename folder" onClick={e => { e.stopPropagation(); setName(folder.name); setEditing(true); }}
              className="p-1 rounded text-neutral-400 hover:text-white hover:bg-white/10"><Pencil size={12} /></button>
            <button data-testid={`folder-delete-${folder.id}`} title="Delete folder"
              onClick={e => { e.stopPropagation(); if (window.confirm(`Delete folder "${folder.name}"? Its chats will move back to the main list.`)) onDelete(folder.id); }}
              className="p-1 rounded text-neutral-400 hover:text-red-400 hover:bg-white/10"><Trash2 size={12} /></button>
          </div>
        )}
      </div>
      {!collapsed && (
        <div data-testid={`folder-chats-${folder.id}`} className="pl-4 ml-2.5 border-l border-white/5" style={folder.color ? { borderColor: `${folder.color}59` } : undefined}>
          {children}
          {count === 0 && <div className="px-3 py-1.5 text-[11px] text-neutral-600 italic">Drag chats here</div>}
        </div>
      )}
    </div>
  );
};

export default FolderSection;
