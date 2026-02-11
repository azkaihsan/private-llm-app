import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const defaultSettings = {
  appName: 'Open WebUI',
  logoType: 'text',
  logoText: 'OI',
  logoImageUrl: '',
  logoBgColor: '#ffffff',
  logoTextColor: '#000000',
  theme: 'dark-default',
  mainBg: '#212121',
  sidebarBg: '#171717',
  inputBg: '#2f2f2f',
  accentColor: '#ffffff',
  userBubbleBg: '#2f2f2f',
  fontSize: 15,
  systemPrompt: 'You are a helpful AI assistant. You provide clear, accurate, and well-formatted responses using markdown when appropriate.',
};

const themePresets = {
  'dark-default': {
    label: 'Dark (Default)',
    mainBg: '#212121',
    sidebarBg: '#171717',
    inputBg: '#2f2f2f',
    accentColor: '#ffffff',
    userBubbleBg: '#2f2f2f',
  },
  'midnight-blue': {
    label: 'Midnight Blue',
    mainBg: '#1a1a2e',
    sidebarBg: '#16213e',
    inputBg: '#253350',
    accentColor: '#5e9fff',
    userBubbleBg: '#253350',
  },
  'forest': {
    label: 'Forest',
    mainBg: '#1a2421',
    sidebarBg: '#141e1b',
    inputBg: '#243530',
    accentColor: '#6bcf9f',
    userBubbleBg: '#243530',
  },
  'rose': {
    label: 'Ros\u00e9',
    mainBg: '#261a1f',
    sidebarBg: '#1e1418',
    inputBg: '#382530',
    accentColor: '#f59eb4',
    userBubbleBg: '#382530',
  },
  'pure-dark': {
    label: 'OLED Dark',
    mainBg: '#000000',
    sidebarBg: '#0a0a0a',
    inputBg: '#1a1a1a',
    accentColor: '#ffffff',
    userBubbleBg: '#1a1a1a',
  },
  'light': {
    label: 'Light',
    mainBg: '#f5f5f5',
    sidebarBg: '#e8e8e8',
    inputBg: '#ffffff',
    accentColor: '#171717',
    userBubbleBg: '#e0e0e0',
  },
};

const SettingsContext = createContext();

export const useSettings = () => useContext(SettingsContext);

export const SettingsProvider = ({ children }) => {
  const [settings, setSettings] = useState(() => {
    try {
      const saved = localStorage.getItem('openwebui_settings');
      return saved ? { ...defaultSettings, ...JSON.parse(saved) } : defaultSettings;
    } catch {
      return defaultSettings;
    }
  });

  const [settingsLoaded, setSettingsLoaded] = useState(false);

  // Load settings from backend on mount
  useEffect(() => {
    const load = async () => {
      try {
        const res = await axios.get(`${API}/settings`);
        if (res.data && Object.keys(res.data).length > 0) {
          const merged = { ...defaultSettings, ...res.data };
          setSettings(merged);
          localStorage.setItem('openwebui_settings', JSON.stringify(merged));
        }
      } catch (e) {
        // Backend settings not available, use localStorage
      }
      setSettingsLoaded(true);
    };
    load();
  }, []);

  // Apply CSS variables whenever settings change
  useEffect(() => {
    const root = document.documentElement;
    root.style.setProperty('--main-bg', settings.mainBg);
    root.style.setProperty('--sidebar-bg', settings.sidebarBg);
    root.style.setProperty('--input-bg', settings.inputBg);
    root.style.setProperty('--accent-color', settings.accentColor);
    root.style.setProperty('--user-bubble-bg', settings.userBubbleBg);
    root.style.setProperty('--font-size', `${settings.fontSize}px`);
    document.body.style.backgroundColor = settings.mainBg;

    // Determine if light theme
    const isLight = isLightColor(settings.mainBg);
    root.style.setProperty('--text-primary', isLight ? '#1a1a1a' : '#f0f0f0');
    root.style.setProperty('--text-secondary', isLight ? '#555555' : '#a3a3a3');
    root.style.setProperty('--text-muted', isLight ? '#888888' : '#737373');
    root.style.setProperty('--border-color', isLight ? 'rgba(0,0,0,0.1)' : 'rgba(255,255,255,0.08)');
    root.style.setProperty('--hover-bg', isLight ? 'rgba(0,0,0,0.05)' : 'rgba(255,255,255,0.05)');
    root.style.setProperty('--code-bg', isLight ? '#f0f0f0' : '#1e1e1e');
  }, [settings]);

  const updateSettings = useCallback(async (newSettings) => {
    const merged = { ...settings, ...newSettings };
    setSettings(merged);
    localStorage.setItem('openwebui_settings', JSON.stringify(merged));
    try {
      await axios.put(`${API}/settings`, merged);
    } catch (e) {
      console.error('Failed to save settings:', e);
    }
  }, [settings]);

  const resetSettings = useCallback(async () => {
    setSettings(defaultSettings);
    localStorage.setItem('openwebui_settings', JSON.stringify(defaultSettings));
    try {
      await axios.put(`${API}/settings`, defaultSettings);
    } catch (e) {
      console.error('Failed to reset settings:', e);
    }
  }, []);

  return (
    <SettingsContext.Provider value={{ settings, updateSettings, resetSettings, themePresets, defaultSettings }}>
      {children}
    </SettingsContext.Provider>
  );
};

function isLightColor(hex) {
  if (!hex) return false;
  const c = hex.replace('#', '');
  const r = parseInt(c.substr(0, 2), 16);
  const g = parseInt(c.substr(2, 2), 16);
  const b = parseInt(c.substr(4, 2), 16);
  return (r * 299 + g * 587 + b * 114) / 1000 > 128;
}

export default SettingsContext;
