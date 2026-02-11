import React, { useEffect, useRef } from 'react';
import { Copy, Check, RotateCcw, Pencil, ThumbsUp, ThumbsDown, ChevronDown } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';

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

const MarkdownContent = ({ content }) => {
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
          return <code className="bg-[#2a2a2a] text-orange-300 px-1.5 py-0.5 rounded text-[13px]" {...props}>{children}</code>;
        },
        p: ({ children }) => <p className="mb-3 last:mb-0 leading-7">{children}</p>,
        h1: ({ children }) => <h1 className="text-xl font-bold mb-3 mt-5">{children}</h1>,
        h2: ({ children }) => <h2 className="text-lg font-semibold mb-2 mt-4">{children}</h2>,
        h3: ({ children }) => <h3 className="text-base font-semibold mb-2 mt-3">{children}</h3>,
        ul: ({ children }) => <ul className="list-disc pl-6 mb-3 space-y-1">{children}</ul>,
        ol: ({ children }) => <ol className="list-decimal pl-6 mb-3 space-y-1">{children}</ol>,
        li: ({ children }) => <li className="leading-7">{children}</li>,
        strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
        table: ({ children }) => (
          <div className="overflow-x-auto my-3">
            <table className="min-w-full border-collapse border border-white/10 rounded">{children}</table>
          </div>
        ),
        thead: ({ children }) => <thead className="bg-white/5">{children}</thead>,
        th: ({ children }) => <th className="border border-white/10 px-4 py-2 text-left text-sm font-medium">{children}</th>,
        td: ({ children }) => <td className="border border-white/10 px-4 py-2 text-sm">{children}</td>,
        blockquote: ({ children }) => <blockquote className="border-l-2 border-neutral-500 pl-4 italic text-neutral-400 my-3">{children}</blockquote>,
        a: ({ children, href }) => <a href={href} className="text-blue-400 hover:underline" target="_blank" rel="noreferrer">{children}</a>,
      }}
    >
      {content}
    </ReactMarkdown>
  );
};

const MessageBubble = ({ message, isTyping }) => {
  const [hovering, setHovering] = React.useState(false);
  const isUser = message.role === 'user';

  return (
    <div
      className={`group py-3 ${isUser ? 'flex justify-end' : ''}`}
      onMouseEnter={() => setHovering(true)}
      onMouseLeave={() => setHovering(false)}
    >
      <div className={`flex gap-4 ${isUser ? 'flex-row-reverse max-w-[85%]' : 'max-w-full'}`}>
        {!isUser && (
          <div className="w-7 h-7 rounded-full bg-white flex items-center justify-center shrink-0 mt-1">
            <span className="text-black font-bold text-[10px]">OI</span>
          </div>
        )}
        <div className="flex flex-col min-w-0 flex-1">
          <div className={`text-[15px] text-neutral-100 leading-relaxed ${
            isUser ? 'bg-[#2f2f2f] rounded-3xl px-5 py-3' : ''
          }`}>
            {isTyping ? (
              <div className="flex items-center gap-1 py-1">
                <div className="w-2 h-2 bg-neutral-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <div className="w-2 h-2 bg-neutral-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <div className="w-2 h-2 bg-neutral-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            ) : isUser ? (
              <span className="whitespace-pre-wrap">{message.content}</span>
            ) : (
              <div className="prose-invert max-w-none">
                <MarkdownContent content={message.content} />
              </div>
            )}
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

const ChatArea = ({ messages, isTyping }) => {
  const scrollRef = useRef(null);
  const endRef = useRef(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  return (
    <div ref={scrollRef} className="flex-1 overflow-y-auto">
      <div className="max-w-3xl mx-auto px-4 py-4">
        {messages.map(msg => (
          <MessageBubble key={msg.id} message={msg} />
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
