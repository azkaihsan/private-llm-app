import React, { useState, useRef, useEffect, useCallback, forwardRef, useImperativeHandle } from 'react';
import { ArrowUp, Plus, Mic, X, FileText, Image, File, Loader2, CircleStop, MicOff } from 'lucide-react';
import { useSettings } from '@/context/SettingsContext';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const ACCEPT_TYPES = [
  'image/*',
  '.pdf,.doc,.docx,.txt,.md,.csv,.json,.xml,.yaml,.yml',
  '.html,.css,.js,.jsx,.ts,.tsx,.py,.java,.c,.cpp,.h,.go,.rs,.rb,.php,.sh,.sql,.swift,.kt',
  '.xlsx,.xls,.toml,.ini,.cfg,.log,.env,.svg'
].join(',');

const FILE_ICONS = {
  image: Image,
  pdf: FileText,
  document: FileText,
  default: File,
};

function getFileIcon(file) {
  if (file.is_image || file.content_type?.startsWith('image/')) return FILE_ICONS.image;
  if (file.content_type?.includes('pdf')) return FILE_ICONS.pdf;
  if (file.original_filename?.match(/\.(docx?|txt|md|csv|xlsx?)$/i)) return FILE_ICONS.document;
  return FILE_ICONS.default;
}

function formatSize(bytes) {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

const ChatInput = forwardRef(({ onSend, isTyping, placeholder }, ref) => {
  const [message, setMessage] = useState('');
  const [attachedFiles, setAttachedFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const textareaRef = useRef(null);
  const fileInputRef = useRef(null);
  const recognitionRef = useRef(null);
  const { settings } = useSettings();

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 200) + 'px';
    }
  }, [message]);

  const handleSend = useCallback(() => {
    const hasContent = message.trim() || attachedFiles.length > 0;
    if (!hasContent || isTyping || uploading) return;

    const fileIds = attachedFiles.map(f => f.id);
    onSend(message.trim(), fileIds.length > 0 ? fileIds : undefined, attachedFiles);
    setMessage('');
    setAttachedFiles([]);
    if (textareaRef.current) textareaRef.current.style.height = 'auto';
  }, [message, attachedFiles, isTyping, uploading, onSend]);

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // Shared upload logic
  const uploadFileList = useCallback(async (files) => {
    if (files.length === 0) return;
    setUploading(true);
    const uploaded = [];
    for (const file of files) {
      if (file.size > 20 * 1024 * 1024) {
        alert(`${file.name} is too large (max 20MB)`);
        continue;
      }
      try {
        const formData = new FormData();
        formData.append('file', file);
        const res = await axios.post(`${API}/files/upload`, formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        });
        uploaded.push(res.data);
      } catch (err) {
        console.error(`Failed to upload ${file.name}:`, err);
        alert(`Failed to upload ${file.name}`);
      }
    }
    setAttachedFiles(prev => [...prev, ...uploaded]);
    setUploading(false);
    textareaRef.current?.focus();
  }, []);

  const handleFileSelect = async (e) => {
    const files = Array.from(e.target.files || []);
    if (files.length === 0) return;
    e.target.value = '';
    await uploadFileList(files);
  };

  // Expose addFiles for drag-and-drop from parent
  useImperativeHandle(ref, () => ({
    addFiles: (files) => uploadFileList(Array.from(files)),
  }), [uploadFileList]);

  const removeFile = (fileId) => {
    setAttachedFiles(prev => prev.filter(f => f.id !== fileId));
  };

  // Web Speech API
  const toggleSpeech = useCallback(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert('Speech recognition is not supported in this browser. Try Chrome or Edge.');
      return;
    }

    if (isListening && recognitionRef.current) {
      recognitionRef.current.stop();
      setIsListening(false);
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-US';

    let finalTranscript = '';

    recognition.onresult = (event) => {
      let interim = '';
      for (let i = event.resultIndex; i < event.results.length; i++) {
        if (event.results[i].isFinal) {
          finalTranscript += event.results[i][0].transcript + ' ';
        } else {
          interim += event.results[i][0].transcript;
        }
      }
      setMessage(prev => {
        const base = prev.replace(/\u200B.*$/, '');
        return finalTranscript + interim;
      });
    };

    recognition.onerror = (event) => {
      console.error('Speech recognition error:', event.error);
      setIsListening(false);
    };

    recognition.onend = () => {
      setIsListening(false);
      recognitionRef.current = null;
    };

    recognitionRef.current = recognition;
    recognition.start();
    setIsListening(true);
  }, [isListening]);

  // Cleanup recognition on unmount
  useEffect(() => {
    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
    };
  }, []);

  const hasContent = message.trim() || attachedFiles.length > 0;

  return (
    <div className="w-full max-w-3xl mx-auto px-2 sm:px-4 pb-3 sm:pb-4">
      <div className="relative rounded-2xl sm:rounded-3xl shadow-lg" style={{ backgroundColor: settings.inputBg }}>
        {/* Attached Files Preview */}
        {attachedFiles.length > 0 && (
          <div className="flex flex-wrap gap-2 px-3 pt-3 pb-1">
            {attachedFiles.map(file => {
              const Icon = getFileIcon(file);
              const isImg = file.is_image;
              return (
                <div
                  key={file.id}
                  className="relative group flex items-center gap-2 rounded-xl px-3 py-2 text-sm max-w-[200px]"
                  style={{ backgroundColor: 'rgba(255,255,255,0.08)', border: '1px solid rgba(255,255,255,0.1)' }}
                  data-testid={`attached-file-${file.id}`}
                >
                  {isImg ? (
                    <div className="w-8 h-8 rounded overflow-hidden shrink-0">
                      <img
                        src={`${API}/files/${file.id}?auth=${localStorage.getItem('openwebui_token')}`}
                        alt={file.original_filename}
                        className="w-full h-full object-cover"
                      />
                    </div>
                  ) : (
                    <Icon size={16} className="text-neutral-400 shrink-0" />
                  )}
                  <span className="truncate text-neutral-300 text-xs">{file.original_filename}</span>
                  <button
                    onClick={() => removeFile(file.id)}
                    className="absolute -top-1.5 -right-1.5 w-5 h-5 rounded-full bg-neutral-600 hover:bg-red-500 flex items-center justify-center transition-colors opacity-0 group-hover:opacity-100"
                    data-testid={`remove-file-${file.id}`}
                  >
                    <X size={10} className="text-white" />
                  </button>
                </div>
              );
            })}
            {uploading && (
              <div className="flex items-center gap-2 rounded-xl px-3 py-2 text-sm" style={{ backgroundColor: 'rgba(255,255,255,0.05)' }}>
                <Loader2 size={14} className="animate-spin text-neutral-400" />
                <span className="text-xs text-neutral-500">Uploading...</span>
              </div>
            )}
          </div>
        )}

        {/* Input Row */}
        <div className="flex items-end gap-2 p-2">
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={uploading}
            className="p-2 rounded-full hover:bg-white/10 text-neutral-400 hover:text-white transition-colors shrink-0 mb-0.5"
            data-testid="file-upload-button"
          >
            {uploading ? <Loader2 size={20} className="animate-spin" /> : <Plus size={20} />}
          </button>
          <input
            ref={fileInputRef}
            type="file"
            accept={ACCEPT_TYPES}
            onChange={handleFileSelect}
            multiple
            className="hidden"
            data-testid="file-input"
          />
          <textarea
            ref={textareaRef}
            value={message}
            onChange={e => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder || 'Ask anything'}
            rows={1}
            className="flex-1 bg-transparent text-white text-[15px] resize-none outline-none py-2.5 px-1 placeholder:text-neutral-500 max-h-[200px] leading-relaxed"
            data-testid="chat-message-input"
          />
          <div className="flex items-center gap-1 shrink-0 mb-0.5">
            <button
              onClick={toggleSpeech}
              className={`p-2 rounded-full transition-colors ${
                isListening
                  ? 'bg-red-500/20 text-red-400 hover:bg-red-500/30'
                  : 'hover:bg-white/10 text-neutral-400 hover:text-white'
              }`}
              data-testid="mic-button"
              title={isListening ? 'Stop listening' : 'Voice input'}
            >
              {isListening ? <MicOff size={20} /> : <Mic size={20} />}
            </button>
            {isTyping ? (
              <button className="p-2 rounded-full bg-white text-black hover:bg-neutral-200 transition-colors" data-testid="stop-button">
                <CircleStop size={20} />
              </button>
            ) : (
              <button
                onClick={handleSend}
                disabled={!hasContent || uploading}
                className={`p-2 rounded-full transition-colors ${
                  hasContent && !uploading
                    ? 'bg-white text-black hover:bg-neutral-200'
                    : 'bg-neutral-600 text-neutral-400 cursor-not-allowed'
                }`}
                data-testid="send-button"
              >
                <ArrowUp size={20} />
              </button>
            )}
          </div>
        </div>
      </div>
      <p className="text-center text-[11px] text-neutral-500 mt-2">
        Open WebUI can make mistakes. Consider checking important information.
      </p>
    </div>
  );
});

export default ChatInput;
