import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const errMsg = (e, fallback) => e?.response?.data?.detail && typeof e.response.data.detail === 'string' ? e.response.data.detail : fallback;

export const useFolders = (userId, setChats) => {
  const [folders, setFolders] = useState([]);

  useEffect(() => {
    setFolders([]);
    if (!userId) return;
    axios.get(`${API}/folders`).then(r => setFolders(r.data)).catch(e => console.error('Failed to fetch folders:', e));
  }, [userId]);

  const createFolder = useCallback(async (name) => {
    try {
      const res = await axios.post(`${API}/folders`, { name });
      setFolders(prev => [...prev, res.data]);
      return res.data;
    } catch (e) { toast.error(errMsg(e, 'Failed to create folder')); return null; }
  }, []);

  const renameFolder = useCallback(async (id, name) => {
    try {
      await axios.put(`${API}/folders/${id}`, { name });
      setFolders(prev => prev.map(f => f.id === id ? { ...f, name: name.split(/\s+/).filter(Boolean).join(' ') } : f));
    } catch (e) { toast.error(errMsg(e, 'Failed to rename folder')); }
  }, []);

  const updateFolder = useCallback(async (id, data) => {
    try {
      await axios.put(`${API}/folders/${id}`, data);
      const name = data.name.split(/\s+/).filter(Boolean).join(' ');
      setFolders(prev => prev.map(f => f.id === id ? { ...f, name, instructions: data.instructions } : f));
      toast.success('Folder saved');
      return true;
    } catch (e) { toast.error(errMsg(e, 'Failed to save folder')); return false; }
  }, []);

  const deleteFolder = useCallback(async (id) => {
    try {
      await axios.delete(`${API}/folders/${id}`);
      setFolders(prev => prev.filter(f => f.id !== id));
      setChats(prev => prev.map(c => c.folder_id === id ? { ...c, folder_id: null } : c));
    } catch (e) { toast.error(errMsg(e, 'Failed to delete folder')); }
  }, [setChats]);

  const moveChat = useCallback(async (chatId, folderId) => {
    const target = folderId || null;
    let previous;
    setChats(prev => prev.map(c => {
      if (c.id !== chatId) return c;
      previous = c.folder_id || null;
      return { ...c, folder_id: target };
    }));
    try {
      await axios.put(`${API}/chats/${chatId}/folder`, { folder_id: target });
    } catch (e) {
      setChats(prev => prev.map(c => c.id === chatId ? { ...c, folder_id: previous } : c));
      toast.error(errMsg(e, 'Failed to move chat'));
    }
  }, [setChats]);

  return { folders, createFolder, renameFolder, updateFolder, deleteFolder, moveChat };
};
