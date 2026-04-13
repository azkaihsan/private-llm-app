import React, { useState, useRef, useEffect, useCallback } from 'react';
import {
  X, Upload, Type, Image, RotateCcw, Check, Palette, Settings, MessageSquare,
  Link2, Cpu, Eye, EyeOff, Zap, CheckCircle2, XCircle, Loader2, ToggleLeft, ToggleRight
} from 'lucide-react';
import { useSettings } from '@/context/SettingsContext';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const tabs = [
  { id: 'connections', label: 'Connections', icon: Link2 },
  { id: 'models', label: 'Models', icon: Cpu },
  { id: 'general', label: 'General', icon: Settings },
  { id: 'theme', label: 'Theme', icon: Palette },
  { id: 'system', label: 'System Prompt', icon: MessageSquare },
];

const PROVIDER_INFO = {
  openai: { name: 'OpenAI', color: '#10a37f', models: ['gpt-4o', 'gpt-4.1-mini', 'gpt-5.1', 'gpt-5-mini'] },
  anthropic: { name: 'Anthropic', color: '#d4a574', models: ['claude-sonnet-4-5-20250929', 'claude-4-sonnet-20250514'] },
  gemini: { name: 'Google Gemini', color: '#4285f4', models: ['gemini-2.5-flash', 'gemini-2.5-pro'] },
};

const SettingsModal = ({ open, onClose, onModelsChanged }) => {
  const { settings, updateSettings, resetSettings, themePresets } = useSettings();
  const [activeTab, setActiveTab] = useState('connections');
  const [localSettings, setLocalSettings] = useState(settings);
  const fileInputRef = useRef(null);

  // Connections state
  const [connections, setConnections] = useState(null);
  const [testingProvider, setTestingProvider] = useState(null);
  const [testResults, setTestResults] = useState({});
  const [showApiKeys, setShowApiKeys] = useState({});

  // Models state
  const [allModels, setAllModels] = useState([]);

  // Load connections and models when modal opens
  useEffect(() => {
    if (!open) return;
    setLocalSettings(settings);
    loadConnections();
    loadModels();
  }, [open, settings]);

  const loadConnections = async () => {
    try {
      const res = await axios.get(`${API}/connections`);
      setConnections(res.data);
    } catch (e) {
      console.error('Failed to load connections:', e);
      setConnections({
        providers: {
          openai: { enabled: true, apiKey: '', name: 'OpenAI', useEmergentKey: true },
          anthropic: { enabled: true, apiKey: '', name: 'Anthropic', useEmergentKey: true },
          gemini: { enabled: true, apiKey: '', name: 'Google Gemini', useEmergentKey: true },
        },
        defaultModel: 'gpt-4o',
        modelParams: { temperature: 0.7, maxTokens: 4096, topP: 1.0 },
        disabledModels: [],
      });
    }
  };

  const loadModels = async () => {
    try {
      const res = await axios.get(`${API}/models`);
      setAllModels(res.data);
    } catch (e) { console.error('Failed to load models:', e); }
  };

  const handleConnectionChange = (provider, field, value) => {
    setConnections(prev => ({
      ...prev,
      providers: {
        ...prev.providers,
        [provider]: { ...prev.providers[provider], [field]: value },
      },
    }));
  };

  const handleToggleProvider = (provider) => {
    const current = connections.providers[provider]?.enabled ?? true;
    handleConnectionChange(provider, 'enabled', !current);
  };

  const handleToggleEmergentKey = (provider) => {
    const current = connections.providers[provider]?.useEmergentKey ?? true;
    handleConnectionChange(provider, 'useEmergentKey', !current);
  };

  const handleTestConnection = async (provider) => {
    const prov = connections.providers[provider];
    if (!prov) return;
    setTestingProvider(provider);
    setTestResults(prev => ({ ...prev, [provider]: null }));
    try {
      const key = prov.useEmergentKey ? 'emergent' : prov.apiKey;
      const res = await axios.post(`${API}/connections/test`, { provider, apiKey: key });
      setTestResults(prev => ({ ...prev, [provider]: res.data }));
    } catch (e) {
      setTestResults(prev => ({ ...prev, [provider]: { status: 'error', message: 'Request failed' } }));
    }
    setTestingProvider(null);
  };

  const handleToggleModel = (modelId) => {
    setConnections(prev => {
      const disabled = new Set(prev.disabledModels || []);
      if (disabled.has(modelId)) disabled.delete(modelId);
      else disabled.add(modelId);
      return { ...prev, disabledModels: Array.from(disabled) };
    });
  };

  const handleModelParamChange = (param, value) => {
    setConnections(prev => ({
      ...prev,
      modelParams: { ...prev.modelParams, [param]: value },
    }));
  };

  if (!open) return null;

  const handleChange = (key, value) => {
    setLocalSettings(prev => ({ ...prev, [key]: value }));
  };

  const handleSave = async () => {
    updateSettings(localSettings);
    if (connections) {
      try {
        await axios.put(`${API}/connections`, connections);
        onModelsChanged && onModelsChanged();
      } catch (e) { console.error('Failed to save connections:', e); }
    }
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
  const inputStyle = {
    backgroundColor: isLight ? '#fff' : '#3a3a3a',
    color: isLight ? '#000' : '#fff',
    border: `1px solid ${isLight ? 'rgba(0,0,0,0.15)' : 'rgba(255,255,255,0.1)'}`,
  };
  const labelColor = isLight ? '#333' : '#ccc';
  const mutedColor = isLight ? '#888' : '#666';
  const disabledModels = new Set(connections?.disabledModels || []);

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
                    className="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm font-medium transition-colors"
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

              {/* ===== CONNECTIONS TAB ===== */}
              {activeTab === 'connections' && connections && (
                <>
                  <div>
                    <p className="text-xs mb-4" style={{ color: mutedColor }}>
                      Configure API connections for each LLM provider. Toggle "Use Emergent Key" to use the built-in universal key, or provide your own API key.
                    </p>
                  </div>

                  {Object.entries(PROVIDER_INFO).map(([provKey, provInfo]) => {
                    const prov = connections.providers?.[provKey] || {};
                    const isEnabled = prov.enabled !== false;
                    const useEmergent = prov.useEmergentKey !== false;
                    const testResult = testResults[provKey];
                    const isTesting = testingProvider === provKey;

                    return (
                      <div key={provKey} className="rounded-xl p-4 space-y-3" style={{ backgroundColor: isLight ? 'rgba(0,0,0,0.03)' : 'rgba(255,255,255,0.03)', border: `1px solid ${isLight ? 'rgba(0,0,0,0.08)' : 'rgba(255,255,255,0.06)'}` }}>
                        {/* Provider Header */}
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-3">
                            <div className="w-2 h-2 rounded-full" style={{ backgroundColor: isEnabled ? provInfo.color : '#555' }} />
                            <span className="text-sm font-semibold">{provInfo.name}</span>
                            <span className="text-xs px-1.5 py-0.5 rounded" style={{ backgroundColor: isLight ? 'rgba(0,0,0,0.06)' : 'rgba(255,255,255,0.08)', color: mutedColor }}>
                              {provInfo.models.length} models
                            </span>
                          </div>
                          <button onClick={() => handleToggleProvider(provKey)} className="transition-colors" style={{ color: isEnabled ? provInfo.color : '#555' }}>
                            {isEnabled ? <ToggleRight size={28} /> : <ToggleLeft size={28} />}
                          </button>
                        </div>

                        {isEnabled && (
                          <>
                            {/* Emergent Key Toggle */}
                            <div className="flex items-center justify-between">
                              <div className="flex items-center gap-2">
                                <Zap size={14} style={{ color: useEmergent ? '#f59e0b' : mutedColor }} />
                                <span className="text-sm" style={{ color: labelColor }}>Use Emergent Universal Key</span>
                              </div>
                              <button onClick={() => handleToggleEmergentKey(provKey)} className="transition-colors" style={{ color: useEmergent ? '#f59e0b' : '#555' }}>
                                {useEmergent ? <ToggleRight size={24} /> : <ToggleLeft size={24} />}
                              </button>
                            </div>

                            {/* Custom API Key */}
                            {!useEmergent && (
                              <div>
                                <label className="block text-xs font-medium mb-1.5" style={{ color: labelColor }}>API Key</label>
                                <div className="flex gap-2">
                                  <div className="relative flex-1">
                                    <input
                                      type={showApiKeys[provKey] ? 'text' : 'password'}
                                      value={prov.apiKey || ''}
                                      onChange={e => handleConnectionChange(provKey, 'apiKey', e.target.value)}
                                      placeholder={`Enter ${provInfo.name} API key...`}
                                      className="w-full rounded-lg px-3 py-2 pr-10 text-sm outline-none"
                                      style={inputStyle}
                                    />
                                    <button
                                      onClick={() => setShowApiKeys(prev => ({ ...prev, [provKey]: !prev[provKey] }))}
                                      className="absolute right-2 top-1/2 -translate-y-1/2 p-1"
                                      style={{ color: mutedColor }}
                                    >
                                      {showApiKeys[provKey] ? <EyeOff size={14} /> : <Eye size={14} />}
                                    </button>
                                  </div>
                                </div>
                              </div>
                            )}

                            {/* Test Connection */}
                            <div className="flex items-center gap-3">
                              <button
                                onClick={() => handleTestConnection(provKey)}
                                disabled={isTesting}
                                className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors"
                                style={{ backgroundColor: isLight ? 'rgba(0,0,0,0.06)' : 'rgba(255,255,255,0.08)', color: labelColor }}
                              >
                                {isTesting ? <Loader2 size={12} className="animate-spin" /> : <Zap size={12} />}
                                {isTesting ? 'Testing...' : 'Verify Connection'}
                              </button>
                              {testResult && (
                                <div className="flex items-center gap-1.5 text-xs">
                                  {testResult.status === 'ok' ? (
                                    <><CheckCircle2 size={14} className="text-green-400" /><span className="text-green-400">Connected</span></>
                                  ) : (
                                    <><XCircle size={14} className="text-red-400" /><span className="text-red-400 max-w-[200px] truncate">{testResult.message}</span></>
                                  )}
                                </div>
                              )}
                            </div>
                          </>
                        )}
                      </div>
                    );
                  })}
                </>
              )}

              {/* ===== MODELS TAB ===== */}
              {activeTab === 'models' && connections && (
                <>
                  {/* Default Model */}
                  <div>
                    <label className="block text-sm font-medium mb-2" style={{ color: labelColor }}>Default Model</label>
                    <p className="text-xs mb-3" style={{ color: mutedColor }}>The model selected by default for new conversations.</p>
                    <select
                      value={connections.defaultModel || 'gpt-4o'}
                      onChange={e => setConnections(prev => ({ ...prev, defaultModel: e.target.value }))}
                      className="w-full rounded-lg px-3 py-2 text-sm outline-none appearance-none"
                      style={inputStyle}
                    >
                      {allModels.filter(m => !disabledModels.has(m.id)).map(m => (
                        <option key={m.id} value={m.id}>{m.name} ({m.provider})</option>
                      ))}
                    </select>
                  </div>

                  {/* Model Parameters */}
                  <div>
                    <label className="block text-sm font-medium mb-3" style={{ color: labelColor }}>Model Parameters</label>
                    <div className="space-y-4">
                      <div>
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-sm" style={{ color: labelColor }}>Temperature</span>
                          <span className="text-xs font-mono" style={{ color: mutedColor }}>{(connections.modelParams?.temperature ?? 0.7).toFixed(1)}</span>
                        </div>
                        <input
                          type="range" min={0} max={2} step={0.1}
                          value={connections.modelParams?.temperature ?? 0.7}
                          onChange={e => handleModelParamChange('temperature', parseFloat(e.target.value))}
                          className="w-full accent-white"
                        />
                        <div className="flex justify-between text-xs mt-0.5" style={{ color: mutedColor }}>
                          <span>Precise (0)</span><span>Creative (2)</span>
                        </div>
                      </div>

                      <div>
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-sm" style={{ color: labelColor }}>Max Tokens</span>
                          <span className="text-xs font-mono" style={{ color: mutedColor }}>{connections.modelParams?.maxTokens ?? 4096}</span>
                        </div>
                        <input
                          type="range" min={256} max={16384} step={256}
                          value={connections.modelParams?.maxTokens ?? 4096}
                          onChange={e => handleModelParamChange('maxTokens', parseInt(e.target.value))}
                          className="w-full accent-white"
                        />
                        <div className="flex justify-between text-xs mt-0.5" style={{ color: mutedColor }}>
                          <span>256</span><span>16384</span>
                        </div>
                      </div>

                      <div>
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-sm" style={{ color: labelColor }}>Top P</span>
                          <span className="text-xs font-mono" style={{ color: mutedColor }}>{(connections.modelParams?.topP ?? 1.0).toFixed(2)}</span>
                        </div>
                        <input
                          type="range" min={0} max={1} step={0.05}
                          value={connections.modelParams?.topP ?? 1.0}
                          onChange={e => handleModelParamChange('topP', parseFloat(e.target.value))}
                          className="w-full accent-white"
                        />
                        <div className="flex justify-between text-xs mt-0.5" style={{ color: mutedColor }}>
                          <span>Focused (0)</span><span>Diverse (1)</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Available Models */}
                  <div>
                    <label className="block text-sm font-medium mb-3" style={{ color: labelColor }}>Available Models</label>
                    <p className="text-xs mb-3" style={{ color: mutedColor }}>Toggle models on/off. Disabled models won't appear in the model selector.</p>
                    <div className="space-y-1">
                      {Object.entries(PROVIDER_INFO).map(([provKey, provInfo]) => {
                        const provEnabled = connections.providers?.[provKey]?.enabled !== false;
                        if (!provEnabled) return null;
                        const provModels = allModels.filter(m => m.provider === provKey);
                        if (provModels.length === 0) return null;

                        return (
                          <div key={provKey} className="mb-3">
                            <div className="flex items-center gap-2 mb-1.5 px-1">
                              <div className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: provInfo.color }} />
                              <span className="text-xs font-semibold uppercase tracking-wider" style={{ color: mutedColor }}>{provInfo.name}</span>
                            </div>
                            {provModels.map(model => {
                              const enabled = !disabledModels.has(model.id);
                              return (
                                <div
                                  key={model.id}
                                  className="flex items-center justify-between px-3 py-2.5 rounded-lg transition-colors cursor-pointer"
                                  style={{ backgroundColor: isLight ? 'rgba(0,0,0,0.02)' : 'rgba(255,255,255,0.02)' }}
                                  onClick={() => handleToggleModel(model.id)}
                                >
                                  <div className="flex items-center gap-3">
                                    <Cpu size={14} style={{ color: enabled ? provInfo.color : '#555' }} />
                                    <span className="text-sm" style={{ color: enabled ? labelColor : '#666', textDecoration: enabled ? 'none' : 'line-through' }}>
                                      {model.name}
                                    </span>
                                    {connections.defaultModel === model.id && (
                                      <span className="text-[10px] px-1.5 py-0.5 rounded-full font-medium" style={{ backgroundColor: isLight ? 'rgba(0,0,0,0.08)' : 'rgba(255,255,255,0.1)', color: mutedColor }}>
                                        Default
                                      </span>
                                    )}
                                  </div>
                                  <button style={{ color: enabled ? provInfo.color : '#555' }}>
                                    {enabled ? <ToggleRight size={22} /> : <ToggleLeft size={22} />}
                                  </button>
                                </div>
                              );
                            })}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </>
              )}

              {/* ===== GENERAL TAB ===== */}
              {activeTab === 'general' && (
                <>
                  <div>
                    <label className="block text-sm font-medium mb-2" style={{ color: labelColor }}>App Name</label>
                    <input type="text" value={localSettings.appName} onChange={e => handleChange('appName', e.target.value)} className="w-full rounded-lg px-3 py-2 text-sm outline-none" style={inputStyle} />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-3" style={{ color: labelColor }}>Logo Type</label>
                    <div className="flex gap-2">
                      <button onClick={() => handleChange('logoType', 'text')} className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium" style={{ backgroundColor: localSettings.logoType === 'text' ? (isLight ? 'rgba(0,0,0,0.1)' : 'rgba(255,255,255,0.15)') : 'transparent', border: `1px solid ${isLight ? 'rgba(0,0,0,0.15)' : 'rgba(255,255,255,0.1)'}` }}>
                        <Type size={16} /> Text
                      </button>
                      <button onClick={() => handleChange('logoType', 'image')} className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium" style={{ backgroundColor: localSettings.logoType === 'image' ? (isLight ? 'rgba(0,0,0,0.1)' : 'rgba(255,255,255,0.15)') : 'transparent', border: `1px solid ${isLight ? 'rgba(0,0,0,0.15)' : 'rgba(255,255,255,0.1)'}` }}>
                        <Image size={16} /> Image
                      </button>
                    </div>
                  </div>
                  {localSettings.logoType === 'text' && (
                    <div className="space-y-4">
                      <div>
                        <label className="block text-sm font-medium mb-2" style={{ color: labelColor }}>Logo Text</label>
                        <input type="text" value={localSettings.logoText} onChange={e => handleChange('logoText', e.target.value.slice(0, 4))} maxLength={4} className="w-32 rounded-lg px-3 py-2 text-sm outline-none" style={inputStyle} />
                        <p className="text-xs mt-1" style={{ color: mutedColor }}>Max 4 characters</p>
                      </div>
                      <div className="flex gap-6">
                        <div>
                          <label className="block text-sm font-medium mb-2" style={{ color: labelColor }}>Background</label>
                          <div className="flex items-center gap-2">
                            <input type="color" value={localSettings.logoBgColor} onChange={e => handleChange('logoBgColor', e.target.value)} className="w-10 h-10 rounded-lg cursor-pointer border-0 bg-transparent" />
                            <span className="text-xs font-mono" style={{ color: mutedColor }}>{localSettings.logoBgColor}</span>
                          </div>
                        </div>
                        <div>
                          <label className="block text-sm font-medium mb-2" style={{ color: labelColor }}>Text Color</label>
                          <div className="flex items-center gap-2">
                            <input type="color" value={localSettings.logoTextColor} onChange={e => handleChange('logoTextColor', e.target.value)} className="w-10 h-10 rounded-lg cursor-pointer border-0 bg-transparent" />
                            <span className="text-xs font-mono" style={{ color: mutedColor }}>{localSettings.logoTextColor}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                  {localSettings.logoType === 'image' && (
                    <div>
                      <label className="block text-sm font-medium mb-2" style={{ color: labelColor }}>Logo Image</label>
                      <div className="flex items-center gap-4">
                        {localSettings.logoImageUrl && <img src={localSettings.logoImageUrl} alt="Logo" className="w-12 h-12 rounded-full object-cover" />}
                        <button onClick={() => fileInputRef.current?.click()} className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm" style={{ backgroundColor: isLight ? 'rgba(0,0,0,0.06)' : 'rgba(255,255,255,0.08)', border: `1px solid ${isLight ? 'rgba(0,0,0,0.15)' : 'rgba(255,255,255,0.1)'}` }}>
                          <Upload size={16} /> Upload Image
                        </button>
                        <input ref={fileInputRef} type="file" accept="image/*" onChange={handleImageUpload} className="hidden" />
                      </div>
                      <p className="text-xs mt-2" style={{ color: mutedColor }}>Max 512KB. PNG, JPG, SVG supported.</p>
                    </div>
                  )}
                  <div>
                    <label className="block text-sm font-medium mb-3" style={{ color: labelColor }}>Preview</label>
                    <div className="flex items-center gap-3 p-4 rounded-xl" style={{ backgroundColor: isLight ? 'rgba(0,0,0,0.04)' : 'rgba(255,255,255,0.04)' }}>
                      <LogoPreview settings={localSettings} size={48} />
                      <span className="font-semibold">{localSettings.appName}</span>
                    </div>
                  </div>
                </>
              )}

              {/* ===== THEME TAB ===== */}
              {activeTab === 'theme' && (
                <>
                  <div>
                    <label className="block text-sm font-medium mb-3" style={{ color: labelColor }}>Theme Presets</label>
                    <div className="grid grid-cols-3 gap-2">
                      {Object.entries(themePresets).map(([key, preset]) => (
                        <button key={key} onClick={() => handleThemePreset(key)} className="relative flex flex-col items-center gap-2 p-3 rounded-xl text-xs font-medium transition-all" style={{ border: `2px solid ${localSettings.theme === key ? preset.accentColor : (isLight ? 'rgba(0,0,0,0.1)' : 'rgba(255,255,255,0.08)')}`, backgroundColor: isLight ? 'rgba(0,0,0,0.02)' : 'rgba(255,255,255,0.02)' }}>
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
                  <div>
                    <label className="block text-sm font-medium mb-3" style={{ color: labelColor }}>Custom Colors</label>
                    <div className="grid grid-cols-2 gap-4">
                      {[{ key: 'mainBg', label: 'Main Background' }, { key: 'sidebarBg', label: 'Sidebar' }, { key: 'inputBg', label: 'Input Area' }, { key: 'accentColor', label: 'Accent' }, { key: 'userBubbleBg', label: 'User Bubble' }].map(({ key, label }) => (
                        <div key={key} className="flex items-center gap-3">
                          <input type="color" value={localSettings[key]} onChange={e => { handleChange(key, e.target.value); handleChange('theme', 'custom'); }} className="w-9 h-9 rounded-lg cursor-pointer border-0 bg-transparent shrink-0" />
                          <div className="flex flex-col">
                            <span className="text-sm">{label}</span>
                            <span className="text-xs font-mono" style={{ color: mutedColor }}>{localSettings[key]}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-2" style={{ color: labelColor }}>Font Size: {localSettings.fontSize}px</label>
                    <input type="range" min={12} max={20} value={localSettings.fontSize} onChange={e => handleChange('fontSize', parseInt(e.target.value))} className="w-full accent-white" />
                    <div className="flex justify-between text-xs mt-1" style={{ color: mutedColor }}><span>12px</span><span>20px</span></div>
                  </div>
                </>
              )}

              {/* ===== SYSTEM PROMPT TAB ===== */}
              {activeTab === 'system' && (
                <div>
                  <label className="block text-sm font-medium mb-2" style={{ color: labelColor }}>System Prompt</label>
                  <p className="text-xs mb-3" style={{ color: mutedColor }}>Customize how the AI assistant behaves in all new conversations.</p>
                  <textarea value={localSettings.systemPrompt} onChange={e => handleChange('systemPrompt', e.target.value)} rows={8} className="w-full rounded-xl px-4 py-3 text-sm outline-none resize-none leading-relaxed" style={inputStyle} />
                </div>
              )}
            </div>
          </div>

          {/* Footer */}
          <div className="flex items-center justify-between px-6 py-4" style={{ borderTop: `1px solid ${isLight ? 'rgba(0,0,0,0.1)' : 'rgba(255,255,255,0.08)'}` }}>
            <button onClick={handleReset} className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm transition-colors" style={{ color: isLight ? '#666' : '#999' }}>
              <RotateCcw size={14} /> Reset to Defaults
            </button>
            <div className="flex gap-2">
              <button onClick={onClose} className="px-4 py-2 rounded-lg text-sm transition-colors" style={{ backgroundColor: isLight ? 'rgba(0,0,0,0.06)' : 'rgba(255,255,255,0.08)', color: isLight ? '#333' : '#ccc' }}>
                Cancel
              </button>
              <button onClick={handleSave} className="px-5 py-2 rounded-lg text-sm font-medium transition-colors" style={{ backgroundColor: localSettings.accentColor, color: isLightBg(localSettings.accentColor) ? '#000' : '#fff' }}>
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
