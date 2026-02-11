import React, { useState, useRef } from 'react';
import { X, Upload, Type, Image, RotateCcw, Check, Palette, Settings, MessageSquare } from 'lucide-react';
import { useSettings } from '@/context/SettingsContext';

const tabs = [
  { id: 'general', label: 'General', icon: Settings },
  { id: 'theme', label: 'Theme', icon: Palette },
  { id: 'system', label: 'System Prompt', icon: MessageSquare },
];

const SettingsModal = ({ open, onClose }) => {
  const { settings, updateSettings, resetSettings, themePresets } = useSettings();
  const [activeTab, setActiveTab] = useState('general');
  const [localSettings, setLocalSettings] = useState(settings);
  const fileInputRef = useRef(null);

  if (!open) return null;

  const handleChange = (key, value) => {
    setLocalSettings(prev => ({ ...prev, [key]: value }));
  };

  const handleSave = () => {
    updateSettings(localSettings);
    onClose();
  };

  const handleReset = () => {
    resetSettings();
    setLocalSettings({ ...settings });
    onClose();
  };

  const handleThemePreset = (presetKey) => {
    const preset = themePresets[presetKey];
    setLocalSettings(prev => ({ ...prev, theme: presetKey, ...preset }));
  };

  const handleImageUpload = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (file.size > 512 * 1024) { alert('Image must be under 512KB'); return; }
    const reader = new FileReader();
    reader.onload = (ev) => {
      handleChange('logoImageUrl', ev.target.result);
      handleChange('logoType', 'image');
    };
    reader.readAsDataURL(file);
  };

  const isLight = isLightBg(localSettings.mainBg);

  return (
    <>
      <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4" onClick={onClose}>
        <div
          className="w-full max-w-2xl rounded-2xl shadow-2xl border overflow-hidden flex flex-col max-h-[85vh]"
          style={{
            backgroundColor: localSettings.inputBg || '#2f2f2f',
            borderColor: isLight ? 'rgba(0,0,0,0.15)' : 'rgba(255,255,255,0.1)',
            color: isLight ? '#1a1a1a' : '#f0f0f0',
          }}
          onClick={e => e.stopPropagation()}
        >
          {/* Header */}
          <div className="flex items-center justify-between px-6 py-4" style={{ borderBottom: `1px solid ${isLight ? 'rgba(0,0,0,0.1)' : 'rgba(255,255,255,0.08)'}` }}>
            <h2 className="text-lg font-semibold">Settings</h2>
            <button onClick={onClose} className="p-1.5 rounded-lg transition-colors" style={{ color: isLight ? '#666' : '#999' }}>
              <X size={20} />
            </button>
          </div>

          <div className="flex flex-1 min-h-0">
            {/* Tab Navigation */}
            <div className="w-44 shrink-0 p-3 space-y-0.5" style={{ borderRight: `1px solid ${isLight ? 'rgba(0,0,0,0.1)' : 'rgba(255,255,255,0.08)'}` }}>
              {tabs.map(tab => {
                const Icon = tab.icon;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm font-medium transition-colors`}
                    style={{
                      backgroundColor: activeTab === tab.id ? (isLight ? 'rgba(0,0,0,0.08)' : 'rgba(255,255,255,0.1)') : 'transparent',
                      color: activeTab === tab.id ? (isLight ? '#000' : '#fff') : (isLight ? '#555' : '#999'),
                    }}
                  >
                    <Icon size={16} />
                    {tab.label}
                  </button>
                );
              })}
            </div>

            {/* Tab Content */}
            <div className="flex-1 overflow-y-auto p-6 space-y-6">
              {activeTab === 'general' && (
                <>
                  {/* App Name */}
                  <div>
                    <label className="block text-sm font-medium mb-2" style={{ color: isLight ? '#333' : '#ccc' }}>App Name</label>
                    <input
                      type="text"
                      value={localSettings.appName}
                      onChange={e => handleChange('appName', e.target.value)}
                      className="w-full rounded-lg px-3 py-2 text-sm outline-none transition-colors"
                      style={{
                        backgroundColor: isLight ? '#fff' : '#3a3a3a',
                        color: isLight ? '#000' : '#fff',
                        border: `1px solid ${isLight ? 'rgba(0,0,0,0.15)' : 'rgba(255,255,255,0.1)'}`,
                      }}
                    />
                  </div>

                  {/* Logo Type */}
                  <div>
                    <label className="block text-sm font-medium mb-3" style={{ color: isLight ? '#333' : '#ccc' }}>Logo Type</label>
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleChange('logoType', 'text')}
                        className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors"
                        style={{
                          backgroundColor: localSettings.logoType === 'text' ? (isLight ? 'rgba(0,0,0,0.1)' : 'rgba(255,255,255,0.15)') : 'transparent',
                          border: `1px solid ${isLight ? 'rgba(0,0,0,0.15)' : 'rgba(255,255,255,0.1)'}`,
                        }}
                      >
                        <Type size={16} /> Text
                      </button>
                      <button
                        onClick={() => handleChange('logoType', 'image')}
                        className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors"
                        style={{
                          backgroundColor: localSettings.logoType === 'image' ? (isLight ? 'rgba(0,0,0,0.1)' : 'rgba(255,255,255,0.15)') : 'transparent',
                          border: `1px solid ${isLight ? 'rgba(0,0,0,0.15)' : 'rgba(255,255,255,0.1)'}`,
                        }}
                      >
                        <Image size={16} /> Image
                      </button>
                    </div>
                  </div>

                  {/* Logo Text Settings */}
                  {localSettings.logoType === 'text' && (
                    <div className="space-y-4">
                      <div>
                        <label className="block text-sm font-medium mb-2" style={{ color: isLight ? '#333' : '#ccc' }}>Logo Text</label>
                        <input
                          type="text"
                          value={localSettings.logoText}
                          onChange={e => handleChange('logoText', e.target.value.slice(0, 4))}
                          maxLength={4}
                          className="w-32 rounded-lg px-3 py-2 text-sm outline-none"
                          style={{
                            backgroundColor: isLight ? '#fff' : '#3a3a3a',
                            color: isLight ? '#000' : '#fff',
                            border: `1px solid ${isLight ? 'rgba(0,0,0,0.15)' : 'rgba(255,255,255,0.1)'}`,
                          }}
                        />
                        <p className="text-xs mt-1" style={{ color: isLight ? '#888' : '#666' }}>Max 4 characters</p>
                      </div>
                      <div className="flex gap-6">
                        <div>
                          <label className="block text-sm font-medium mb-2" style={{ color: isLight ? '#333' : '#ccc' }}>Background</label>
                          <div className="flex items-center gap-2">
                            <input type="color" value={localSettings.logoBgColor} onChange={e => handleChange('logoBgColor', e.target.value)} className="w-10 h-10 rounded-lg cursor-pointer border-0 bg-transparent" />
                            <span className="text-xs font-mono" style={{ color: isLight ? '#666' : '#888' }}>{localSettings.logoBgColor}</span>
                          </div>
                        </div>
                        <div>
                          <label className="block text-sm font-medium mb-2" style={{ color: isLight ? '#333' : '#ccc' }}>Text Color</label>
                          <div className="flex items-center gap-2">
                            <input type="color" value={localSettings.logoTextColor} onChange={e => handleChange('logoTextColor', e.target.value)} className="w-10 h-10 rounded-lg cursor-pointer border-0 bg-transparent" />
                            <span className="text-xs font-mono" style={{ color: isLight ? '#666' : '#888' }}>{localSettings.logoTextColor}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Logo Image Upload */}
                  {localSettings.logoType === 'image' && (
                    <div>
                      <label className="block text-sm font-medium mb-2" style={{ color: isLight ? '#333' : '#ccc' }}>Logo Image</label>
                      <div className="flex items-center gap-4">
                        {localSettings.logoImageUrl && (
                          <img src={localSettings.logoImageUrl} alt="Logo" className="w-12 h-12 rounded-full object-cover" />
                        )}
                        <button
                          onClick={() => fileInputRef.current?.click()}
                          className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm transition-colors"
                          style={{
                            backgroundColor: isLight ? 'rgba(0,0,0,0.06)' : 'rgba(255,255,255,0.08)',
                            border: `1px solid ${isLight ? 'rgba(0,0,0,0.15)' : 'rgba(255,255,255,0.1)'}`,
                          }}
                        >
                          <Upload size={16} /> Upload Image
                        </button>
                        <input ref={fileInputRef} type="file" accept="image/*" onChange={handleImageUpload} className="hidden" />
                      </div>
                      <p className="text-xs mt-2" style={{ color: isLight ? '#888' : '#666' }}>Max 512KB. PNG, JPG, SVG supported.</p>
                    </div>
                  )}

                  {/* Logo Preview */}
                  <div>
                    <label className="block text-sm font-medium mb-3" style={{ color: isLight ? '#333' : '#ccc' }}>Preview</label>
                    <div className="flex items-center gap-3 p-4 rounded-xl" style={{ backgroundColor: isLight ? 'rgba(0,0,0,0.04)' : 'rgba(255,255,255,0.04)' }}>
                      <LogoPreview settings={localSettings} size={48} />
                      <span className="font-semibold">{localSettings.appName}</span>
                    </div>
                  </div>
                </>
              )}

              {activeTab === 'theme' && (
                <>
                  {/* Theme Presets */}
                  <div>
                    <label className="block text-sm font-medium mb-3" style={{ color: isLight ? '#333' : '#ccc' }}>Theme Presets</label>
                    <div className="grid grid-cols-3 gap-2">
                      {Object.entries(themePresets).map(([key, preset]) => (
                        <button
                          key={key}
                          onClick={() => handleThemePreset(key)}
                          className="relative flex flex-col items-center gap-2 p-3 rounded-xl text-xs font-medium transition-all"
                          style={{
                            border: `2px solid ${localSettings.theme === key ? preset.accentColor : (isLight ? 'rgba(0,0,0,0.1)' : 'rgba(255,255,255,0.08)')}`,
                            backgroundColor: isLight ? 'rgba(0,0,0,0.02)' : 'rgba(255,255,255,0.02)',
                          }}
                        >
                          <div className="flex gap-1 w-full">
                            <div className="w-6 h-8 rounded" style={{ backgroundColor: preset.sidebarBg }} />
                            <div className="flex-1 h-8 rounded" style={{ backgroundColor: preset.mainBg }} />
                          </div>
                          <span style={{ color: isLight ? '#333' : '#ccc' }}>{preset.label}</span>
                          {localSettings.theme === key && (
                            <div className="absolute top-1.5 right-1.5 w-4 h-4 rounded-full flex items-center justify-center" style={{ backgroundColor: preset.accentColor }}>
                              <Check size={10} style={{ color: isLightBg(preset.accentColor) ? '#000' : '#fff' }} />
                            </div>
                          )}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Custom Colors */}
                  <div>
                    <label className="block text-sm font-medium mb-3" style={{ color: isLight ? '#333' : '#ccc' }}>Custom Colors</label>
                    <div className="grid grid-cols-2 gap-4">
                      {[
                        { key: 'mainBg', label: 'Main Background' },
                        { key: 'sidebarBg', label: 'Sidebar' },
                        { key: 'inputBg', label: 'Input Area' },
                        { key: 'accentColor', label: 'Accent' },
                        { key: 'userBubbleBg', label: 'User Bubble' },
                      ].map(({ key, label }) => (
                        <div key={key} className="flex items-center gap-3">
                          <input
                            type="color"
                            value={localSettings[key]}
                            onChange={e => { handleChange(key, e.target.value); handleChange('theme', 'custom'); }}
                            className="w-9 h-9 rounded-lg cursor-pointer border-0 bg-transparent shrink-0"
                          />
                          <div className="flex flex-col">
                            <span className="text-sm">{label}</span>
                            <span className="text-xs font-mono" style={{ color: isLight ? '#888' : '#666' }}>{localSettings[key]}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Font Size */}
                  <div>
                    <label className="block text-sm font-medium mb-2" style={{ color: isLight ? '#333' : '#ccc' }}>
                      Font Size: {localSettings.fontSize}px
                    </label>
                    <input
                      type="range"
                      min={12}
                      max={20}
                      value={localSettings.fontSize}
                      onChange={e => handleChange('fontSize', parseInt(e.target.value))}
                      className="w-full accent-white"
                    />
                    <div className="flex justify-between text-xs mt-1" style={{ color: isLight ? '#888' : '#666' }}>
                      <span>12px</span>
                      <span>20px</span>
                    </div>
                  </div>
                </>
              )}

              {activeTab === 'system' && (
                <div>
                  <label className="block text-sm font-medium mb-2" style={{ color: isLight ? '#333' : '#ccc' }}>System Prompt</label>
                  <p className="text-xs mb-3" style={{ color: isLight ? '#888' : '#666' }}>Customize how the AI assistant behaves in all new conversations.</p>
                  <textarea
                    value={localSettings.systemPrompt}
                    onChange={e => handleChange('systemPrompt', e.target.value)}
                    rows={8}
                    className="w-full rounded-xl px-4 py-3 text-sm outline-none resize-none leading-relaxed"
                    style={{
                      backgroundColor: isLight ? '#fff' : '#3a3a3a',
                      color: isLight ? '#000' : '#fff',
                      border: `1px solid ${isLight ? 'rgba(0,0,0,0.15)' : 'rgba(255,255,255,0.1)'}`,
                    }}
                  />
                </div>
              )}
            </div>
          </div>

          {/* Footer */}
          <div className="flex items-center justify-between px-6 py-4" style={{ borderTop: `1px solid ${isLight ? 'rgba(0,0,0,0.1)' : 'rgba(255,255,255,0.08)'}` }}>
            <button
              onClick={handleReset}
              className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm transition-colors"
              style={{ color: isLight ? '#666' : '#999' }}
            >
              <RotateCcw size={14} /> Reset to Defaults
            </button>
            <div className="flex gap-2">
              <button
                onClick={onClose}
                className="px-4 py-2 rounded-lg text-sm transition-colors"
                style={{
                  backgroundColor: isLight ? 'rgba(0,0,0,0.06)' : 'rgba(255,255,255,0.08)',
                  color: isLight ? '#333' : '#ccc',
                }}
              >
                Cancel
              </button>
              <button
                onClick={handleSave}
                className="px-5 py-2 rounded-lg text-sm font-medium transition-colors"
                style={{
                  backgroundColor: localSettings.accentColor,
                  color: isLightBg(localSettings.accentColor) ? '#000' : '#fff',
                }}
              >
                Save
              </button>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export const LogoPreview = ({ settings, size = 48, className = '' }) => {
  const s = settings || {};
  const dim = size;
  const fontSize = Math.max(dim * 0.35, 10);

  if (s.logoType === 'image' && s.logoImageUrl) {
    return <img src={s.logoImageUrl} alt="Logo" className={`rounded-full object-cover ${className}`} style={{ width: dim, height: dim }} />;
  }

  return (
    <div
      className={`rounded-full flex items-center justify-center font-bold shrink-0 ${className}`}
      style={{ width: dim, height: dim, backgroundColor: s.logoBgColor || '#fff', color: s.logoTextColor || '#000', fontSize }}
    >
      {s.logoText || 'OI'}
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

export default SettingsModal;
