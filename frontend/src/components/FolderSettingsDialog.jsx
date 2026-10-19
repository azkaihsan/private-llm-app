import React, { useState, useEffect } from 'react';
import { Check } from 'lucide-react';
import { FOLDER_COLORS, FOLDER_ICONS } from '@/components/folderStyles';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';

const MAX = 4000;

const FolderSettingsDialog = ({ folder, open, onClose, onSave }) => {
  const [name, setName] = useState('');
  const [instructions, setInstructions] = useState('');
  const [saving, setSaving] = useState(false);
  const [color, setColor] = useState('');
  const [icon, setIcon] = useState('folder');

  useEffect(() => {
    if (open && folder) { setName(folder.name); setInstructions(folder.instructions || ''); setColor(folder.color || ''); setIcon(folder.icon || 'folder'); }
  }, [open, folder]);

  const save = async () => {
    if (!name.trim()) return;
    setSaving(true);
    const ok = await onSave(folder.id, { name: name.trim(), instructions: instructions.trim(), color, icon });
    setSaving(false);
    if (ok) onClose();
  };

  return (
    <Dialog open={open} onOpenChange={o => !o && onClose()}>
      <DialogContent data-testid="folder-settings-dialog" className="bg-[#212121] border-white/10 text-neutral-200 sm:max-w-lg max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-base">Folder settings</DialogTitle>
          <DialogDescription className="text-neutral-500 text-xs">
            Instructions are added after the global system prompt for every chat in this folder.
          </DialogDescription>
        </DialogHeader>
        <label className="text-xs text-neutral-400">Name</label>
        <input data-testid="folder-settings-name-input" value={name} maxLength={60} onChange={e => setName(e.target.value)}
          className="w-full bg-[#2f2f2f] text-white text-sm rounded-lg px-3 py-2 outline-none focus:ring-1 focus:ring-neutral-600" />
        <label className="text-xs text-neutral-400 mt-2">Colour</label>
        <div className="flex flex-wrap gap-2" data-testid="folder-color-picker">
          {FOLDER_COLORS.map(c => (
            <button key={c || 'default'} data-testid={`folder-color-${c ? c.slice(1) : 'default'}`} title={c || 'Default'} onClick={() => setColor(c)}
              className={`w-6 h-6 rounded-full flex items-center justify-center transition-transform hover:scale-110 ${color === c ? 'ring-2 ring-white ring-offset-2 ring-offset-[#212121]' : ''} ${c ? '' : 'border border-dashed border-neutral-500'}`}
              style={{ backgroundColor: c || 'transparent' }}>
              {color === c && <Check size={12} className={c ? 'text-white' : 'text-neutral-300'} />}
            </button>
          ))}
        </div>
        <label className="text-xs text-neutral-400 mt-2">Icon</label>
        <div className="grid grid-cols-8 gap-1.5" data-testid="folder-icon-picker">
          {Object.entries(FOLDER_ICONS).map(([key, Icon]) => (
            <button key={key} data-testid={`folder-icon-${key}`} title={key} onClick={() => setIcon(key)}
              className={`h-9 rounded-lg flex items-center justify-center transition-colors ${icon === key ? 'bg-white/15' : 'bg-[#2f2f2f] hover:bg-white/10'}`}
              style={{ color: color || '#d4d4d4' }}>
              <Icon size={16} />
            </button>
          ))}
        </div>
        <label className="text-xs text-neutral-400 mt-2">Instructions</label>
        <textarea data-testid="folder-settings-instructions-input" value={instructions} maxLength={MAX} rows={5}
          onChange={e => setInstructions(e.target.value)}
          placeholder="e.g. You are helping with Project Atlas. Answer concisely and use TypeScript for code examples."
          className="w-full bg-[#2f2f2f] text-white text-sm rounded-lg px-3 py-2 outline-none resize-y focus:ring-1 focus:ring-neutral-600 placeholder:text-neutral-600" />
        <div data-testid="folder-settings-char-count" className="text-[11px] text-neutral-500 text-right -mt-1">{instructions.length}/{MAX}</div>
        <div className="flex justify-end gap-2 pt-1">
          <button data-testid="folder-settings-cancel" onClick={onClose}
            className="px-4 py-2 rounded-lg text-sm text-neutral-300 hover:bg-white/5 transition-colors">Cancel</button>
          <button data-testid="folder-settings-save" onClick={save} disabled={saving || !name.trim()}
            className="px-4 py-2 rounded-lg text-sm bg-white text-black font-medium hover:bg-neutral-200 disabled:opacity-50 transition-colors">
            {saving ? 'Saving…' : 'Save'}
          </button>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default FolderSettingsDialog;
