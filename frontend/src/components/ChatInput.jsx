import React, { useState, useRef, useEffect } from 'react';
import { ArrowUp, Plus, Mic, Paperclip, Globe, CircleStop } from 'lucide-react';
import { useSettings } from '@/context/SettingsContext';

const ChatInput = ({ onSend, isTyping, placeholder }) => {
  const [message, setMessage] = useState('');
  const textareaRef = useRef(null);
  const { settings } = useSettings();

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 200) + 'px';
    }
  }, [message]);

  const handleSend = () => {
    if (message.trim() && !isTyping) {
      onSend(message.trim());
      setMessage('');
      if (textareaRef.current) textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="w-full max-w-3xl mx-auto px-4 pb-4">
      <div className="relative bg-[#2f2f2f] rounded-3xl shadow-lg">
        {/* Input Row */}
        <div className="flex items-end gap-2 p-2">
          <button className="p-2 rounded-full hover:bg-white/10 text-neutral-400 hover:text-white transition-colors shrink-0 mb-0.5">
            <Plus size={20} />
          </button>
          <textarea
            ref={textareaRef}
            value={message}
            onChange={e => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder || 'Ask anything'}
            rows={1}
            className="flex-1 bg-transparent text-white text-[15px] resize-none outline-none py-2.5 px-1 placeholder:text-neutral-500 max-h-[200px] leading-relaxed"
          />
          <div className="flex items-center gap-1 shrink-0 mb-0.5">
            <button className="p-2 rounded-full hover:bg-white/10 text-neutral-400 hover:text-white transition-colors">
              <Mic size={20} />
            </button>
            {isTyping ? (
              <button className="p-2 rounded-full bg-white text-black hover:bg-neutral-200 transition-colors">
                <CircleStop size={20} />
              </button>
            ) : (
              <button
                onClick={handleSend}
                disabled={!message.trim()}
                className={`p-2 rounded-full transition-colors ${
                  message.trim()
                    ? 'bg-white text-black hover:bg-neutral-200'
                    : 'bg-neutral-600 text-neutral-400 cursor-not-allowed'
                }`}
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
};

export default ChatInput;
