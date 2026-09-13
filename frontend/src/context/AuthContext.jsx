import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const AuthContext = createContext();

const setAuthHeader = (t) => {
  if (t) axios.defaults.headers.common['Authorization'] = `Bearer ${t}`;
  else delete axios.defaults.headers.common['Authorization'];
};
setAuthHeader(localStorage.getItem('openwebui_token'));

export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(() => localStorage.getItem('openwebui_token'));
  const [loading, setLoading] = useState(true);

  const applyToken = (t) => { setAuthHeader(t); setToken(t); };

  // Set axios default header
  useEffect(() => { setAuthHeader(token); }, [token]);

  // Auto-logout on 401
  useEffect(() => {
    const id = axios.interceptors.response.use(
      r => r,
      err => {
        if (err.response?.status === 401 && localStorage.getItem('openwebui_token')) {
          localStorage.removeItem('openwebui_token');
          applyToken(null);
          setUser(null);
        }
        return Promise.reject(err);
      }
    );
    return () => axios.interceptors.response.eject(id);
  }, []);

  // Load user on mount if token exists
  useEffect(() => {
    const loadUser = async () => {
      if (!token) { setLoading(false); return; }
      try {
        axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
        const res = await axios.get(`${API}/auth/me`);
        setUser(res.data);
      } catch (e) {
        console.error('Auth check failed:', e);
        localStorage.removeItem('openwebui_token');
        applyToken(null);
        setUser(null);
      }
      setLoading(false);
    };
    loadUser();
  }, [token]);

  const login = useCallback(async (email, password) => {
    const res = await axios.post(`${API}/auth/login`, { email, password });
    const { token: newToken, user: userData } = res.data;
    localStorage.setItem('openwebui_token', newToken);
    applyToken(newToken);
    setUser(userData);
    return userData;
  }, []);

  const signup = useCallback(async (name, email, password) => {
    const res = await axios.post(`${API}/auth/signup`, { name, email, password });
    const { token: newToken, user: userData } = res.data;
    localStorage.setItem('openwebui_token', newToken);
    applyToken(newToken);
    setUser(userData);
    return userData;
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem('openwebui_token');
    applyToken(null);
    setUser(null);
  }, []);

  const updateProfile = useCallback(async (name) => {
    const res = await axios.put(`${API}/auth/profile`, { name });
    setUser(res.data);
    return res.data;
  }, []);

  const changePassword = useCallback(async (current_password, new_password) => {
    await axios.put(`${API}/auth/password`, { current_password, new_password });
  }, []);

  const isAdmin = user?.role === 'admin';

  return (
    <AuthContext.Provider value={{ user, token, loading, login, signup, logout, isAdmin, updateProfile, changePassword }}>
      {children}
    </AuthContext.Provider>
  );
};

export default AuthContext;
