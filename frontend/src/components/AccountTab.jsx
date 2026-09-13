import React, { useState } from 'react';
import { Loader2, Check } from 'lucide-react';
import { useAuth } from '@/context/AuthContext';

const errText = (e, fallback) => {
  const d = e.response?.data?.detail;
  return Array.isArray(d) ? d.map(x => x.msg).join(' ') : (typeof d === 'string' ? d : fallback);
};

export const AccountTab = ({ inputStyle, labelColor, mutedColor, accentColor, accentText }) => {
  const { user, updateProfile, changePassword } = useAuth();
  const [name, setName] = useState(user?.name || '');
  const [nameState, setNameState] = useState({ loading: false, msg: '', err: '' });
  const [pw, setPw] = useState({ current: '', next: '', confirm: '' });
  const [pwState, setPwState] = useState({ loading: false, msg: '', err: '' });

  const saveName = async (e) => {
    e.preventDefault();
    if (!name.trim()) { setNameState({ loading: false, msg: '', err: 'Name cannot be empty' }); return; }
    setNameState({ loading: true, msg: '', err: '' });
    try {
      await updateProfile(name.trim());
      setNameState({ loading: false, msg: 'Name updated', err: '' });
    } catch (err) {
      setNameState({ loading: false, msg: '', err: errText(err, 'Failed to update name') });
    }
  };

  const savePassword = async (e) => {
    e.preventDefault();
    if (pw.next.length < 6) { setPwState({ loading: false, msg: '', err: 'New password must be at least 6 characters' }); return; }
    if (pw.next !== pw.confirm) { setPwState({ loading: false, msg: '', err: 'Passwords do not match' }); return; }
    setPwState({ loading: true, msg: '', err: '' });
    try {
      await changePassword(pw.current, pw.next);
      setPw({ current: '', next: '', confirm: '' });
      setPwState({ loading: false, msg: 'Password changed', err: '' });
    } catch (err) {
      setPwState({ loading: false, msg: '', err: errText(err, 'Failed to change password') });
    }
  };

  const btnStyle = { backgroundColor: accentColor, color: accentText };

  return (
    <div data-testid="account-tab" className="space-y-8">
      <form onSubmit={saveName} className="space-y-3">
        <div>
          <label className="block text-sm font-medium mb-2" style={{ color: labelColor }}>Display Name</label>
          <input data-testid="account-name-input" type="text" value={name} onChange={e => setName(e.target.value)} className="w-full rounded-lg px-3 py-2 text-sm outline-none" style={inputStyle} />
        </div>
        <div>
          <label className="block text-sm font-medium mb-2" style={{ color: labelColor }}>Email</label>
          <input data-testid="account-email" type="email" value={user?.email || ''} disabled className="w-full rounded-lg px-3 py-2 text-sm outline-none opacity-60" style={inputStyle} />
          <p className="text-xs mt-1" style={{ color: mutedColor }}>Role: {user?.role}</p>
        </div>
        {nameState.err && <p data-testid="account-name-error" className="text-xs text-red-400">{nameState.err}</p>}
        {nameState.msg && <p data-testid="account-name-success" className="text-xs text-green-400 flex items-center gap-1"><Check size={12} /> {nameState.msg}</p>}
        <button data-testid="account-name-save" type="submit" disabled={nameState.loading} className="px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-1.5" style={btnStyle}>
          {nameState.loading && <Loader2 size={14} className="animate-spin" />} Save Name
        </button>
      </form>

      <form onSubmit={savePassword} className="space-y-3">
        <h3 className="text-sm font-semibold" style={{ color: labelColor }}>Change Password</h3>
        <input data-testid="account-current-password" type="password" value={pw.current} onChange={e => setPw(p => ({ ...p, current: e.target.value }))} placeholder="Current password" required className="w-full rounded-lg px-3 py-2 text-sm outline-none" style={inputStyle} />
        <input data-testid="account-new-password" type="password" value={pw.next} onChange={e => setPw(p => ({ ...p, next: e.target.value }))} placeholder="New password (min 6 characters)" required className="w-full rounded-lg px-3 py-2 text-sm outline-none" style={inputStyle} />
        <input data-testid="account-confirm-password" type="password" value={pw.confirm} onChange={e => setPw(p => ({ ...p, confirm: e.target.value }))} placeholder="Confirm new password" required className="w-full rounded-lg px-3 py-2 text-sm outline-none" style={inputStyle} />
        {pwState.err && <p data-testid="account-password-error" className="text-xs text-red-400">{pwState.err}</p>}
        {pwState.msg && <p data-testid="account-password-success" className="text-xs text-green-400 flex items-center gap-1"><Check size={12} /> {pwState.msg}</p>}
        <button data-testid="account-password-save" type="submit" disabled={pwState.loading} className="px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-1.5" style={btnStyle}>
          {pwState.loading && <Loader2 size={14} className="animate-spin" />} Change Password
        </button>
      </form>
    </div>
  );
};

export default AccountTab;
