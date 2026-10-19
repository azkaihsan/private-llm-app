import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import {
  Search, Trash2,
  PanelLeft, Folder, Settings, LogOut, CircleUser,
  SquarePen, EllipsisVertical, X, Archive,
  Upload, ArchiveRestore, ArrowLeft, Shield, Pin, FolderPlus
} from 'lucide-react';
import { useSettings } from '@/context/SettingsContext';
import { useAuth } from '@/context/AuthContext';
import ChatRow from '@/components/ChatRow';
import FolderSection, { useDropZone } from '@/components/FolderSection';
import FolderSettingsDialog from '@/components/FolderSettingsDialog';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const Sidebar = ({
  chats, activeChatId, onSelectChat, onNewChat, onDeleteChat,
  onRenameChat, isOpen, onToggle, onOpenSettings, onOpenUserManagement, onOpenPalette, archivedRequest,
  onArchiveChat, onExportChat, onImportChat, onPinChat, onUnpinChat,
  archivedChats, onUnarchiveChat, onDeleteArchivedChat, onDeleteAllArchived, onRefreshArchived,
  folders, onCreateFolder, onRenameFolder, onUpdateFolder, onDeleteFolder, onMoveChat
}) => {
  const { user, isAdmin, logout } = useAuth();
  const [searchQuery, setSearchQuery] = useState('');
  const [searchOpen, setSearchOpen] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [creatingFolder, setCreatingFolder] = useState(false);
  const [newFolderName, setNewFolderName] = useState('');
  const [draggingChatId, setDraggingChatId] = useState(null);
  const [settingsFolderId, setSettingsFolderId] = useState(null);
  const collapseKey = `openwebui_collapsed_folders_${user?.id}`;
  const [collapsedFolders, setCollapsedFolders] = useState(() => {
    try { return JSON.parse(localStorage.getItem(collapseKey)) || []; } catch { return []; }
  });
  const unfiledDrop = useDropZone(id => onMoveChat(id, null));
  const [showArchived, setShowArchived] = useState(false);
  const { settings } = useSettings();
  const fileInputRef = useRef(null);
  const [contentMatches, setContentMatches] = useState({});

  useEffect(() => {
    const q = searchQuery.trim();
    if (q.length < 2) { setContentMatches({}); return; }
    const t = setTimeout(async () => {
      try {
        const res = await axios.get(`${API}/chats/search`, { params: { q } });
        const map = {};
        res.data.forEach(r => { map[r.chat_id] = r; });
        setContentMatches(map);
      } catch (e) { console.error('Search failed:', e); }
    }, 300);
    return () => clearTimeout(t);
  }, [searchQuery]);

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
    c.title.toLowerCase().includes(searchQuery.toLowerCase()) || contentMatches[c.id]
  );
  const searching = searchQuery.trim().length > 0;
  const folderIds = new Set(folders.map(f => f.id));
  const pinnedChats = filteredChats.filter(c => c.pinned);
  const folderChats = {};
  filteredChats.forEach(c => {
    if (!c.pinned && folderIds.has(c.folder_id)) (folderChats[c.folder_id] = folderChats[c.folder_id] || []).push(c);
  });
  const visibleFolders = searching ? folders.filter(f => folderChats[f.id]?.length) : folders;
  const dateGroups = groupChatsByDate(filteredChats.filter(c => !c.pinned && !folderIds.has(c.folder_id)));

  const toggleFolder = (id) => setCollapsedFolders(prev => {
    const next = prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id];
    localStorage.setItem(collapseKey, JSON.stringify(next));
    return next;
  });

  const submitNewFolder = async () => {
    const name = newFolderName.trim();
    setCreatingFolder(false);
    setNewFolderName('');
    if (name) await onCreateFolder(name);
  };

  const rowActions = {
    onSelect: onSelectChat, onRename: onRenameChat, onPin: onPinChat, onUnpin: onUnpinChat,
    onExport: id => onExportChat && onExportChat(id), onArchive: id => onArchiveChat && onArchiveChat(id),
    onDelete: onDeleteChat, onMove: onMoveChat,
  };

  const renderChat = (chat) => (
    <ChatRow key={chat.id} chat={chat} isActive={activeChatId === chat.id} folders={folders} actions={rowActions}
      snippet={searchQuery && contentMatches[chat.id]?.snippet}
      onDragStart={setDraggingChatId} onDragEnd={() => setDraggingChatId(null)} />
  );

  const renderGroup = (group, items) => (
    <div key={group} className="mb-1">
      <div data-testid={`chat-group-${group.toLowerCase().replace(/\s+/g, '-')}`} className="px-2 py-2 text-[11px] font-medium text-neutral-500 uppercase tracking-wider flex items-center gap-1.5">
        {group === 'Pinned' && <Pin size={11} />}{group}
      </div>
      {items.map(renderChat)}
    </div>
  );

  const handleImportFile = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => {
      try {
        const data = JSON.parse(ev.target.result);
        onImportChat && onImportChat(data);
      } catch (err) {
        alert('Invalid chat file. Please select a valid JSON export.');
      }
    };
    reader.readAsText(file);
    e.target.value = '';
  };

  useEffect(() => {
    if (archivedRequest) { setShowArchived(true); onRefreshArchived && onRefreshArchived(); }
  }, [archivedRequest]);

  const handleOpenArchived = () => {
    setShowArchived(true);
    setShowUserMenu(false);
    onRefreshArchived && onRefreshArchived();
  };

  if (!isOpen) return null;

  // ===== Archived Chats View =====
  if (showArchived) {
    return (
      <div className="w-[260px] h-full flex flex-col relative shrink-0 transition-all duration-300" style={{ backgroundColor: settings.sidebarBg }}>
        <div className="flex items-center gap-2 p-2 pt-3">
          <button
            onClick={() => setShowArchived(false)}
            className="p-2 rounded-lg hover:bg-white/5 text-neutral-400 hover:text-white transition-colors"
          >
            <ArrowLeft size={20} />
          </button>
          <span className="text-sm font-medium text-neutral-200 flex-1">Archived Chats</span>
          {archivedChats && archivedChats.length > 0 && (
            <button
              onClick={() => { if (window.confirm('Delete all archived chats permanently?')) onDeleteAllArchived && onDeleteAllArchived(); }}
              className="p-2 rounded-lg hover:bg-white/5 text-neutral-400 hover:text-red-400 transition-colors"
              title="Delete all archived"
            >
              <Trash2 size={16} />
            </button>
          )}
        </div>

        <div className="flex-1 overflow-y-auto px-2 custom-scrollbar">
          <div className="pb-2">
            {(!archivedChats || archivedChats.length === 0) ? (
              <div className="text-center text-neutral-500 text-sm py-8">
                <Archive size={24} className="mx-auto mb-2 opacity-50" />
                No archived chats
              </div>
            ) : (
              archivedChats.map(chat => (
                <div
                  key={chat.id}
                  className="group flex items-center rounded-lg mb-0.5 hover:bg-white/5 transition-colors"
                >
                  <span className="flex-1 text-sm text-neutral-200 truncate py-2 px-3">
                    {chat.title}
                  </span>
                  <div className="flex items-center gap-0.5 pr-1 shrink-0 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button
                      onClick={() => onUnarchiveChat && onUnarchiveChat(chat.id)}
                      className="p-1 rounded hover:bg-white/10 text-neutral-400 hover:text-green-400 transition-colors"
                      title="Unarchive"
                    >
                      <ArchiveRestore size={14} />
                    </button>
                    <button
                      onClick={() => { if (window.confirm('Delete this chat permanently?')) onDeleteArchivedChat && onDeleteArchivedChat(chat.id); }}
                      className="p-1 rounded hover:bg-white/10 text-neutral-400 hover:text-red-400 transition-colors"
                      title="Delete permanently"
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    );
  }

  // ===== Main Sidebar View =====
  return (
    <div className="w-[260px] h-full flex flex-col relative shrink-0 transition-all duration-300" style={{ backgroundColor: settings.sidebarBg }}>
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
            data-testid="sidebar-search-toggle"
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

      {!searchOpen && (
        <div className="px-2 pb-2">
          <button
            data-testid="sidebar-palette-hint"
            onClick={onOpenPalette}
            className="w-full flex items-center gap-2 px-3 py-2 rounded-lg bg-white/[0.04] hover:bg-white/[0.08] text-neutral-400 hover:text-neutral-200 text-sm transition-colors"
          >
            <Search size={14} />
            <span className="flex-1 text-left">Search</span>
            <kbd className="text-[10px] px-1.5 py-0.5 rounded border border-white/15 text-neutral-500">Ctrl K</kbd>
          </button>
        </div>
      )}

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
              data-testid="sidebar-search-input"
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
      <div className="flex-1 overflow-y-auto px-2 custom-scrollbar">
        <div className="pb-2">
          {pinnedChats.length > 0 && renderGroup('Pinned', pinnedChats)}

          <div className="mb-1" data-testid="folders-section">
            <div className="px-2 py-2 text-[11px] font-medium text-neutral-500 uppercase tracking-wider flex items-center gap-1.5">
              <Folder size={11} /><span className="flex-1">Folders</span>
              <button data-testid="new-folder-button" title="New folder" onClick={() => setCreatingFolder(true)}
                className="p-0.5 rounded text-neutral-500 hover:text-white hover:bg-white/10 transition-colors"><FolderPlus size={13} /></button>
            </div>
            {creatingFolder && (
              <input data-testid="new-folder-input" autoFocus maxLength={60} value={newFolderName} placeholder="Folder name"
                onChange={e => setNewFolderName(e.target.value)} onBlur={submitNewFolder}
                onKeyDown={e => { if (e.key === 'Enter') submitNewFolder(); if (e.key === 'Escape') { setNewFolderName(''); setCreatingFolder(false); } }}
                className="w-full mb-1 bg-[#2f2f2f] text-white text-sm rounded-lg px-3 py-1.5 outline-none focus:ring-1 focus:ring-neutral-600 placeholder:text-neutral-500" />
            )}
            {visibleFolders.map(f => {
              const items = folderChats[f.id] || [];
              return (
                <FolderSection key={f.id} folder={f} count={items.length}
                  collapsed={!searching && collapsedFolders.includes(f.id)} onToggle={toggleFolder}
                  onRename={onRenameFolder} onEditSettings={setSettingsFolderId} onDelete={onDeleteFolder} onDropChat={id => onMoveChat(id, f.id)}>
                  {items.map(renderChat)}
                </FolderSection>
              );
            })}
            {folders.length === 0 && !creatingFolder && (
              <div data-testid="folders-empty" className="px-3 py-1 text-[11px] text-neutral-600">Create a folder, then drag chats into it</div>
            )}
          </div>

          <div data-testid="unfiled-drop-zone" {...unfiledDrop.props}
            className={`rounded-lg transition-colors ${unfiledDrop.over ? 'bg-white/[0.07] ring-1 ring-white/20' : ''}`}>
            {draggingChatId && dateGroups.length === 0 && (
              <div className="px-3 py-3 text-[11px] text-neutral-500 text-center border border-dashed border-white/10 rounded-lg">Drop here to remove from folder</div>
            )}
            {dateGroups.map(([group, items]) => renderGroup(group, items))}
          </div>
          {filteredChats.length === 0 && (
            <div className="text-center text-neutral-500 text-sm py-8">No chats found</div>
          )}
        </div>
      </div>

      <FolderSettingsDialog folder={folders.find(f => f.id === settingsFolderId)} open={!!settingsFolderId && folders.some(f => f.id === settingsFolderId)}
        onClose={() => setSettingsFolderId(null)} onSave={onUpdateFolder} />

      {/* Hidden file input for import */}
      <input
        ref={fileInputRef}
        type="file"
        accept=".json"
        onChange={handleImportFile}
        className="hidden"
      />

      {/* Workspace & User */}
      <div className="border-t border-white/5 p-2">
        <button
          onClick={() => fileInputRef.current?.click()}
          className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg hover:bg-white/5 text-neutral-300 hover:text-white transition-colors"
        >
          <Upload size={18} />
          <span className="text-sm">Import Chat</span>
        </button>
        <button className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg hover:bg-white/5 text-neutral-300 hover:text-white transition-colors">
          <Folder size={18} />
          <span className="text-sm">Workspace</span>
        </button>
        <div className="relative">
          <button
            data-testid="sidebar-user-menu-button"
            onClick={() => setShowUserMenu(!showUserMenu)}
            className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg hover:bg-white/5 text-neutral-300 hover:text-white transition-colors"
          >
            <div className={`w-7 h-7 rounded-full bg-gradient-to-br ${isAdmin ? 'from-amber-500 to-orange-600' : 'from-indigo-500 to-violet-600'} flex items-center justify-center text-white text-xs font-semibold`}>
              {(user?.name || 'U').charAt(0).toUpperCase()}
            </div>
            <span data-testid="sidebar-user-name" className="text-sm flex-1 text-left truncate">{user?.name || 'User'}</span>
            {isAdmin && <span data-testid="sidebar-admin-badge" className="text-[10px] px-1.5 py-0.5 rounded-full font-semibold uppercase bg-amber-500/15 text-amber-400">admin</span>}
            <EllipsisVertical size={16} className="text-neutral-500" />
          </button>
          {showUserMenu && (
            <>
              <div className="fixed inset-0 z-40" onClick={() => setShowUserMenu(false)} />
              <div data-testid="sidebar-user-menu" className="absolute bottom-full left-0 w-full mb-1 bg-[#2f2f2f] rounded-xl shadow-xl border border-white/10 overflow-hidden z-50">
                {isAdmin && (
                  <>
                    <button data-testid="user-menu-admin-panel" onClick={() => { onOpenUserManagement && onOpenUserManagement(); setShowUserMenu(false); }} className="w-full flex items-center gap-3 px-3 py-2.5 hover:bg-white/5 text-neutral-300 text-sm">
                      <Shield size={16} /> Admin Panel
                    </button>
                    <div className="border-t border-white/10" />
                  </>
                )}
                <button data-testid="user-menu-settings" onClick={() => { onOpenSettings && onOpenSettings(); setShowUserMenu(false); }} className="w-full flex items-center gap-3 px-3 py-2.5 hover:bg-white/5 text-neutral-300 text-sm">
                  <Settings size={16} /> Settings
                </button>
                <button data-testid="user-menu-archived" onClick={handleOpenArchived} className="w-full flex items-center gap-3 px-3 py-2.5 hover:bg-white/5 text-neutral-300 text-sm">
                  <Archive size={16} /> Archived Chats
                </button>
                <div className="border-t border-white/10" />
                <button data-testid="user-menu-sign-out" onClick={() => { setShowUserMenu(false); logout(); }} className="w-full flex items-center gap-3 px-3 py-2.5 hover:bg-white/5 text-red-400 text-sm">
                  <LogOut size={16} /> Sign Out
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default Sidebar;
