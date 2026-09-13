import React, { useEffect, useRef } from 'react';
import { Copy, Check, RotateCcw, Pencil, ThumbsUp, ThumbsDown, ChevronDown } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { useSettings } from '@/context/SettingsContext';
import { LogoPreview } from '@/components/SettingsModal';

const CopyButton = ({ text }) => {
  const [copied, setCopied] = React.useState(false);
  const handleCopy = () => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };
  return (
    <button onClick={handleCopy} className="p-1 rounded hover:bg-white/10 text-neutral-400 hover:text-white transition-colors">
      {copied ? <Check size={14} /> : <Copy size={14} />}
    </button>
  );
};

const escapeRx = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');

const highlightText = (text, term) => {
  if (!term) return text;
  const parts = text.split(new RegExp(`(${escapeRx(term)})`, 'gi'));
  return parts.map((p, i) => p.toLowerCase() === term.toLowerCase()
    ? <mark key={i} className="bg-yellow-400/80 text-black rounded-sm px-0.5">{p}</mark>
    : p);
};

const highlightChildren = (children, term) => {
  if (!term) return children;
  return React.Children.map(children, c => typeof c === 'string' ? highlightText(c, term) : c);
};

const MarkdownContent = ({ content, highlight }) => {
  const h = (children) => highlightChildren(children, highlight);
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      components={{
        code({ node, inline, className, children, ...props }) {
          const match = /language-(\w+)/.exec(className || '');
          const codeStr = String(children).replace(/\n$/, '');
          if (!inline && match) {
            return (
              <div className="relative group/code my-3 rounded-xl overflow-hidden">
                <div className="flex items-center justify-between bg-[#1e1e1e] px-4 py-2 border-b border-white/5">
                  <span className="text-xs text-neutral-400">{match[1]}</span>
                  <CopyButton text={codeStr} />
                </div>
                <SyntaxHighlighter
                  style={oneDark}
                  language={match[1]}
                  PreTag="div"
                  customStyle={{ margin: 0, borderRadius: 0, background: '#1e1e1e', fontSize: '13px', padding: '16px' }}
                  {...props}
                >
                  {codeStr}
                </SyntaxHighlighter>
              </div>
            );
          }
          if (!inline) {
            return (
              <div className="relative group/code my-3 rounded-xl overflow-hidden">
                <div className="flex items-center justify-between bg-[#1e1e1e] px-4 py-2 border-b border-white/5">
                  <span className="text-xs text-neutral-400">code</span>
                  <CopyButton text={codeStr} />
                </div>
                <pre className="bg-[#1e1e1e] p-4 overflow-x-auto text-[13px]">
                  <code {...props}>{children}</code>
                </pre>
              </div>
            );
          }
          return <code className="bg-[#2a2a2a] text-orange-300 px-1.5 py-0.5 rounded text-[13px]" {...props}>{h(children)}</code>;
        },
        p: ({ children }) => <p className="mb-3 last:mb-0 leading-7">{h(children)}</p>,
        h1: ({ children }) => <h1 className="text-xl font-bold mb-3 mt-5">{h(children)}</h1>,
        h2: ({ children }) => <h2 className="text-lg font-semibold mb-2 mt-4">{h(children)}</h2>,
        h3: ({ children }) => <h3 className="text-base font-semibold mb-2 mt-3">{h(children)}</h3>,
        ul: ({ children }) => <ul className="list-disc pl-6 mb-3 space-y-1">{children}</ul>,
        ol: ({ children }) => <ol className="list-decimal pl-6 mb-3 space-y-1">{children}</ol>,
        li: ({ children }) => <li className="leading-7">{h(children)}</li>,
        strong: ({ children }) => <strong className="font-semibold">{h(children)}</strong>,
        em: ({ children }) => <em>{h(children)}</em>,
        table: ({ children }) => (
          <div className="overflow-x-auto my-3">
            <table className="min-w-full border-collapse border border-white/10 rounded">{children}</table>
          </div>
        ),
        thead: ({ children }) => <thead className="bg-white/5">{children}</thead>,
        th: ({ children }) => <th className="border border-white/10 px-4 py-2 text-left text-sm font-medium">{h(children)}</th>,
        td: ({ children }) => <td className="border border-white/10 px-4 py-2 text-sm">{h(children)}</td>,
        blockquote: ({ children }) => <blockquote className="border-l-2 border-neutral-500 pl-4 italic text-neutral-400 my-3">{children}</blockquote>,
        a: ({ children, href }) => <a href={href} className="text-blue-400 hover:underline" target="_blank" rel="noreferrer">{h(children)}</a>,
      }}
    >
      {content}
    </ReactMarkdown>
  );
};

const MessageBubble = ({ message, isTyping, highlight, isCurrentMatch }) => {
  const [hovering, setHovering] = React.useState(false);
  const { settings } = useSettings();
  const isUser = message.role === 'user';

  return (
    <div
      data-message-id={message.id}
      data-testid={`message-${message.role}`}
      className={`group py-3 rounded-2xl transition-shadow ${isUser ? 'flex justify-end' : ''} ${isCurrentMatch ? 'ring-2 ring-yellow-400/70 px-2 -mx-2' : ''}`}
      onMouseEnter={() => setHovering(true)}
      onMouseLeave={() => setHovering(false)}
    >
      <div className={`flex gap-4 ${isUser ? 'flex-row-reverse max-w-[85%]' : 'max-w-full'}`}>
        {!isUser && (
          <LogoPreview settings={settings} size={28} className="mt-1" />
        )}
        <div className="flex flex-col min-w-0 flex-1">
          <div style={{ fontSize: `${settings.fontSize}px` }} className={`leading-relaxed ${
            isUser ? 'rounded-3xl px-5 py-3' : ''
          }`}
          >
            {isUser && <div style={{ backgroundColor: settings.userBubbleBg, borderRadius: '1.5rem', padding: '12px 20px' }}>
              {isTyping ? null : <span className="whitespace-pre-wrap" style={{ color: 'var(--text-primary)' }}>{highlightText(message.content, highlight)}</span>}
            </div>}
            {!isUser && (isTyping ? (
              <div className="flex items-center gap-1 py-1">
                <div className="w-2 h-2 bg-neutral-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <div className="w-2 h-2 bg-neutral-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <div className="w-2 h-2 bg-neutral-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            ) : (
              <div className="prose-invert max-w-none" style={{ color: 'var(--text-primary)' }}>
                <MarkdownContent content={message.content} highlight={highlight} />
              </div>
            ))}
          </div>
          {/* Actions */}
          {!isTyping && hovering && !isUser && (
            <div className="flex items-center gap-1 mt-1.5">
              <CopyButton text={message.content} />
              <button className="p-1 rounded hover:bg-white/10 text-neutral-400 hover:text-white transition-colors">
                <ThumbsUp size={14} />
              </button>
              <button className="p-1 rounded hover:bg-white/10 text-neutral-400 hover:text-white transition-colors">
                <ThumbsDown size={14} />
              </button>
              <button className="p-1 rounded hover:bg-white/10 text-neutral-400 hover:text-white transition-colors">
                <RotateCcw size={14} />
              </button>
            </div>
          )}
          {!isTyping && hovering && isUser && (
            <div className="flex items-center gap-1 mt-1.5 justify-end">
              <CopyButton text={message.content} />
              <button className="p-1 rounded hover:bg-white/10 text-neutral-400 hover:text-white transition-colors">
                <Pencil size={14} />
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

const ChatArea = ({ messages, isTyping, searchTerm = '', currentMatchId = null }) => {
  const scrollRef = useRef(null);
  const endRef = useRef(null);

  useEffect(() => {
    if (!searchTerm) endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping, searchTerm]);

  useEffect(() => {
    if (!currentMatchId) return;
    scrollRef.current?.querySelector(`[data-message-id="${currentMatchId}"]`)?.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }, [currentMatchId]);

  return (
    <div ref={scrollRef} className="flex-1 overflow-y-auto">
      <div className="max-w-3xl mx-auto px-4 py-4">
        {messages.map(msg => (
          <MessageBubble key={msg.id} message={msg} highlight={searchTerm} isCurrentMatch={msg.id === currentMatchId} />
        ))}
        {isTyping && (
          <MessageBubble
            message={{ id: 'typing', role: 'assistant', content: '' }}
            isTyping={true}
          />
        )}
        <div ref={endRef} />
      </div>
    </div>
  );
};

export default ChatArea;
