import React, { useState, useEffect, useCallback } from 'react';
import { X, Plus, Pencil, Trash2, Shield, User, Loader2, Search, ChevronDown } from 'lucide-react';
import { useSettings } from '@/context/SettingsContext';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const UserManagement = ({ open, onClose }) => {
  const { settings } = useSettings();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [editingUser, setEditingUser] = useState(null);
  const [formData, setFormData] = useState({ name: '', email: '', password: '', role: 'user' });
  const [formError, setFormError] = useState('');
  const [formLoading, setFormLoading] = useState(false);

  const isLight = isLightBg(settings.mainBg);
  const inputStyle = {
    backgroundColor: isLight ? '#fff' : '#3a3a3a',
    color: isLight ? '#000' : '#fff',
    border: `1px solid ${isLight ? 'rgba(0,0,0,0.15)' : 'rgba(255,255,255,0.1)'}`,
  };
  const labelColor = isLight ? '#333' : '#ccc';
  const mutedColor = isLight ? '#888' : '#666';

  const fetchUsers = useCallback(async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${API}/admin/users`);
      setUsers(res.data);
    } catch (e) { console.error('Failed to fetch users:', e); }
    setLoading(false);
  }, []);

  useEffect(() => { if (open) fetchUsers(); }, [open, fetchUsers]);

  const handleCreate = async (e) => {
    e.preventDefault();
    setFormError('');
    if (!formData.name || !formData.email || !formData.password) { setFormError('All fields required'); return; }
    if (formData.password.length < 6) { setFormError('Password min 6 chars'); return; }
    setFormLoading(true);
    try {
      await axios.post(`${API}/admin/users`, formData);
      setShowCreateForm(false);
      setFormData({ name: '', email: '', password: '', role: 'user' });
      fetchUsers();
    } catch (e) {
      setFormError(e.response?.data?.detail || 'Failed to create user');
    }
    setFormLoading(false);
  };

  const handleUpdate = async (e) => {
    e.preventDefault();
    setFormError('');
    setFormLoading(true);
    const updateData = {};
    if (formData.name) updateData.name = formData.name;
    if (formData.email) updateData.email = formData.email;
    if (formData.role) updateData.role = formData.role;
    if (formData.password) updateData.password = formData.password;
    try {
      await axios.put(`${API}/admin/users/${editingUser.id}`, updateData);
      setEditingUser(null);
      setFormData({ name: '', email: '', password: '', role: 'user' });
      fetchUsers();
    } catch (e) {
      setFormError(e.response?.data?.detail || 'Failed to update user');
    }
    setFormLoading(false);
  };

  const handleDelete = async (userId) => {
    if (!window.confirm('Delete this user and all their chats?')) return;
    try {
      await axios.delete(`${API}/admin/users/${userId}`);
      fetchUsers();
    } catch (e) {
      alert(e.response?.data?.detail || 'Failed to delete user');
    }
  };

  const startEdit = (u) => {
    setEditingUser(u);
    setFormData({ name: u.name, email: u.email, password: '', role: u.role });
    setShowCreateForm(false);
    setFormError('');
  };

  const filteredUsers = users.filter(u =>
    u.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    u.email.toLowerCase().includes(searchQuery.toLowerCase())
  );

  if (!open) return null;

  return (
    <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4" onClick={onClose}>
      <div
        className="w-full max-w-2xl rounded-2xl shadow-2xl border overflow-hidden flex flex-col max-h-[85vh]"
        style={{
          backgroundColor: settings.inputBg || '#2f2f2f',
          borderColor: isLight ? 'rgba(0,0,0,0.15)' : 'rgba(255,255,255,0.1)',
          color: isLight ? '#1a1a1a' : '#f0f0f0',
        }}
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4" style={{ borderBottom: `1px solid ${isLight ? 'rgba(0,0,0,0.1)' : 'rgba(255,255,255,0.08)'}` }}>
          <h2 className="text-lg font-semibold flex items-center gap-2">
            <Shield size={20} /> User Management
          </h2>
          <div className="flex items-center gap-2">
            <button
              onClick={() => { setShowCreateForm(!showCreateForm); setEditingUser(null); setFormError(''); setFormData({ name: '', email: '', password: '', role: 'user' }); }}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors"
              style={{ backgroundColor: isLight ? 'rgba(0,0,0,0.06)' : 'rgba(255,255,255,0.08)' }}
            >
              <Plus size={16} /> Add User
            </button>
            <button onClick={onClose} className="p-1.5 rounded-lg" style={{ color: isLight ? '#666' : '#999' }}>
              <X size={20} />
            </button>
          </div>
        </div>

        {/* Create / Edit Form */}
        {(showCreateForm || editingUser) && (
          <div className="px-6 py-4" style={{ borderBottom: `1px solid ${isLight ? 'rgba(0,0,0,0.1)' : 'rgba(255,255,255,0.08)'}` }}>
            <h3 className="text-sm font-semibold mb-3" style={{ color: labelColor }}>
              {editingUser ? `Edit: ${editingUser.name}` : 'Create New User'}
            </h3>
            <form onSubmit={editingUser ? handleUpdate : handleCreate} className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium mb-1" style={{ color: labelColor }}>Name</label>
                  <input type="text" value={formData.name} onChange={e => setFormData(p => ({ ...p, name: e.target.value }))} className="w-full rounded-lg px-3 py-2 text-sm outline-none" style={inputStyle} required={!editingUser} />
                </div>
                <div>
                  <label className="block text-xs font-medium mb-1" style={{ color: labelColor }}>Email</label>
                  <input type="email" value={formData.email} onChange={e => setFormData(p => ({ ...p, email: e.target.value }))} className="w-full rounded-lg px-3 py-2 text-sm outline-none" style={inputStyle} required={!editingUser} />
                </div>
                <div>
                  <label className="block text-xs font-medium mb-1" style={{ color: labelColor }}>{editingUser ? 'New Password (optional)' : 'Password'}</label>
                  <input type="password" value={formData.password} onChange={e => setFormData(p => ({ ...p, password: e.target.value }))} className="w-full rounded-lg px-3 py-2 text-sm outline-none" style={inputStyle} required={!editingUser} placeholder={editingUser ? 'Leave blank to keep current' : ''} />
                </div>
                <div>
                  <label className="block text-xs font-medium mb-1" style={{ color: labelColor }}>Role</label>
                  <select value={formData.role} onChange={e => setFormData(p => ({ ...p, role: e.target.value }))} className="w-full rounded-lg px-3 py-2 text-sm outline-none appearance-none" style={inputStyle}>
                    <option value="user">User</option>
                    <option value="admin">Admin</option>
                  </select>
                </div>
              </div>
              {formError && <p className="text-xs text-red-400">{formError}</p>}
              <div className="flex gap-2">
                <button type="submit" disabled={formLoading} className="px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-1.5" style={{ backgroundColor: settings.accentColor, color: isLightBg(settings.accentColor) ? '#000' : '#fff' }}>
                  {formLoading && <Loader2 size={14} className="animate-spin" />}
                  {editingUser ? 'Save Changes' : 'Create User'}
                </button>
                <button type="button" onClick={() => { setShowCreateForm(false); setEditingUser(null); setFormError(''); }} className="px-4 py-2 rounded-lg text-sm" style={{ backgroundColor: isLight ? 'rgba(0,0,0,0.06)' : 'rgba(255,255,255,0.08)' }}>
                  Cancel
                </button>
              </div>
            </form>
          </div>
        )}

        {/* Search */}
        <div className="px-6 pt-4">
          <div className="relative">
            <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2" style={{ color: mutedColor }} />
            <input
              type="text"
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              placeholder="Search users..."
              className="w-full rounded-lg pl-9 pr-3 py-2 text-sm outline-none"
              style={inputStyle}
            />
          </div>
        </div>

        {/* User List */}
        <div className="flex-1 overflow-y-auto px-6 py-3">
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 size={24} className="animate-spin" style={{ color: mutedColor }} />
            </div>
          ) : filteredUsers.length === 0 ? (
            <div className="text-center py-8 text-sm" style={{ color: mutedColor }}>No users found</div>
          ) : (
            <div className="space-y-1">
              {filteredUsers.map(u => (
                <div
                  key={u.id}
                  className="flex items-center gap-3 px-3 py-3 rounded-xl transition-colors group"
                  style={{ backgroundColor: isLight ? 'rgba(0,0,0,0.02)' : 'rgba(255,255,255,0.02)' }}
                >
                  <div className="w-9 h-9 rounded-full flex items-center justify-center text-white text-sm font-semibold shrink-0"
                    style={{ backgroundColor: u.role === 'admin' ? '#f59e0b' : '#6366f1' }}>
                    {u.name.charAt(0).toUpperCase()}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium truncate">{u.name}</span>
                      <span className="text-[10px] px-1.5 py-0.5 rounded-full font-semibold uppercase"
                        style={{ backgroundColor: u.role === 'admin' ? 'rgba(245,158,11,0.15)' : 'rgba(99,102,241,0.15)', color: u.role === 'admin' ? '#f59e0b' : '#818cf8' }}>
                        {u.role}
                      </span>
                    </div>
                    <p className="text-xs truncate" style={{ color: mutedColor }}>{u.email}</p>
                  </div>
                  <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button onClick={() => startEdit(u)} className="p-1.5 rounded-lg transition-colors" style={{ color: mutedColor }}
                      onMouseEnter={e => e.target.style.color = isLight ? '#000' : '#fff'}
                      onMouseLeave={e => e.target.style.color = mutedColor}>
                      <Pencil size={14} />
                    </button>
                    <button onClick={() => handleDelete(u.id)} className="p-1.5 rounded-lg transition-colors" style={{ color: mutedColor }}
                      onMouseEnter={e => e.target.style.color = '#ef4444'}
                      onMouseLeave={e => e.target.style.color = mutedColor}>
                      <Trash2 size={14} />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-3 text-xs" style={{ borderTop: `1px solid ${isLight ? 'rgba(0,0,0,0.1)' : 'rgba(255,255,255,0.08)'}`, color: mutedColor }}>
          {users.length} user{users.length !== 1 ? 's' : ''} total • {users.filter(u => u.role === 'admin').length} admin{users.filter(u => u.role === 'admin').length !== 1 ? 's' : ''}
        </div>
      </div>
    </div>
  );
};

function isLightBg(hex) {
  if (!hex) return false;
  const c = hex.replace('#', '');
  const r = parseInt(c.substr(0, 2), 16);
  const g = parseInt(c.substr(2, 2), 16);
  const b = parseInt(c.substr(4, 2), 16);
  return (r * 299 + g * 587 + b * 114) / 1000 > 128;
}

export default UserManagement;
