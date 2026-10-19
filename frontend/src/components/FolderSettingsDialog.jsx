import React, { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';

const MAX = 4000;

const FolderSettingsDialog = ({ folder, open, onClose, onSave }) => {
  const [name, setName] = useState('');
  const [instructions, setInstructions] = useState('');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (open && folder) { setName(folder.name); setInstructions(folder.instructions || ''); }
  }, [open, folder]);

  const save = async () => {
    if (!name.trim()) return;
    setSaving(true);
    const ok = await onSave(folder.id, { name: name.trim(), instructions: instructions.trim() });
    setSaving(false);
    if (ok) onClose();
  };

  return (
    <Dialog open={open} onOpenChange={o => !o && onClose()}>
      <DialogContent data-testid="folder-settings-dialog" className="bg-[#212121] border-white/10 text-neutral-200 sm:max-w-lg">
        <DialogHeader>
          <DialogTitle className="text-base">Folder settings</DialogTitle>
          <DialogDescription className="text-neutral-500 text-xs">
            Instructions are added after the global system prompt for every chat in this folder.
          </DialogDescription>
        </DialogHeader>
        <label className="text-xs text-neutral-400">Name</label>
        <input data-testid="folder-settings-name-input" value={name} maxLength={60} onChange={e => setName(e.target.value)}
          className="w-full bg-[#2f2f2f] text-white text-sm rounded-lg px-3 py-2 outline-none focus:ring-1 focus:ring-neutral-600" />
        <label className="text-xs text-neutral-400 mt-2">Instructions</label>
        <textarea data-testid="folder-settings-instructions-input" value={instructions} maxLength={MAX} rows={8}
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
