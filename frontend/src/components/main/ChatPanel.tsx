import { useState, useRef, useEffect } from 'react';
import { useAppStore } from '../../stores/appStore';
import { useChatSessions, useChatSession, useSendMessage, useCreateSession } from '../../hooks/useChat';

export default function ChatPanel() {
  const { chatOpen, setChatOpen, chatSessionId, setChatSessionId, jurisdictionId, fieldName } = useAppStore();
  const { data: sessions } = useChatSessions();
  const { data: session } = useChatSession(chatSessionId);
  const sendMutation = useSendMessage();
  const createMutation = useCreateSession();
  const [input, setInput] = useState('');
  const [showSessions, setShowSessions] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [session?.messages]);

  if (!chatOpen) return null;

  const handleSend = async () => {
    if (!input.trim()) return;
    const msg = input.trim();
    setInput('');

    let sid = chatSessionId;
    if (!sid) {
      try {
        const newSession = await createMutation.mutateAsync(msg.slice(0, 50));
        sid = newSession.id;
        setChatSessionId(sid);
      } catch {
        return;
      }
    }

    sendMutation.mutate({
      sessionId: sid,
      content: msg,
      jurisdictionId: jurisdictionId || undefined,
      fieldName: fieldName || undefined,
    });
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const messages = session?.messages || [];

  return (
    <>
      <div className="chat-drawer-overlay" onClick={() => setChatOpen(false)} />

      <div className="chat-drawer">
        {/* Header */}
        <div
          className="flex items-center justify-between px-4 py-3 shrink-0"
          style={{ background: 'linear-gradient(135deg, #dc2626, #991b1b)' }}
        >
          <div className="flex items-center gap-2 text-white">
            <svg className="w-4 h-4 opacity-90" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
            </svg>
            <span className="font-bold text-[13px] tracking-[-0.01em]">Synapse Chat</span>
          </div>
          <div className="flex items-center gap-0.5">
            <button
              onClick={() => setShowSessions(!showSessions)}
              className="text-white/60 hover:text-white p-1.5 rounded-lg hover:bg-white/10 transition-colors"
              title="History"
            >
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                <path d="M12 8v4l3 3" /><circle cx="12" cy="12" r="10" />
              </svg>
            </button>
            <button
              onClick={() => { setChatSessionId(null); setShowSessions(false); }}
              className="text-white/60 hover:text-white p-1.5 rounded-lg hover:bg-white/10 transition-colors"
              title="New chat"
            >
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                <line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" />
              </svg>
            </button>
            <button
              onClick={() => setChatOpen(false)}
              className="text-white/60 hover:text-white p-1.5 rounded-lg hover:bg-white/10 transition-colors"
            >
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                <path d="M18 6 6 18M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* Session list */}
        {showSessions && (
          <div className="absolute top-[46px] left-0 right-0 bg-white border-b border-gray-200 max-h-[280px] overflow-y-auto z-10 shadow-lg">
            <div className="px-3 py-2 text-[9px] font-bold uppercase tracking-[0.08em] text-gray-400 bg-gray-50 border-b border-gray-100">
              Recent Conversations
            </div>
            {(sessions || []).map((s) => (
              <button
                key={s.id}
                onClick={() => { setChatSessionId(s.id); setShowSessions(false); }}
                className="w-full text-left px-4 py-2.5 hover:bg-gray-50 border-b border-gray-50 transition-colors"
                style={{ background: chatSessionId === s.id ? '#fef2f2' : 'transparent' }}
              >
                <div className="text-[12px] font-medium text-gray-800 truncate">{s.title}</div>
                <div className="text-[10px] text-gray-400 mt-0.5">
                  {new Date(s.created_at).toLocaleDateString()} — {s.message_count} messages
                </div>
              </button>
            ))}
            {(!sessions || sessions.length === 0) && (
              <div className="px-4 py-6 text-[11px] text-gray-400 text-center">No conversations yet</div>
            )}
          </div>
        )}

        {/* Context bar */}
        {(jurisdictionId || fieldName) && (
          <div className="px-4 py-2 bg-red-50/50 border-b border-red-100/50 text-[10px] text-gray-500 flex items-center gap-2">
            <svg className="w-3 h-3 text-brand/60" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" />
            </svg>
            {jurisdictionId && <span className="font-semibold text-brand">{jurisdictionId.toUpperCase()}</span>}
            {fieldName && (
              <code className="text-[9px] bg-white px-1.5 py-px rounded border border-red-200/60 text-gray-600">{fieldName}</code>
            )}
          </div>
        )}

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-4 py-4 space-y-3">
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center h-full text-center">
              <div
                className="w-14 h-14 rounded-2xl flex items-center justify-center mb-4"
                style={{ background: 'linear-gradient(135deg, #fef2f2, #fee2e2)' }}
              >
                <svg className="w-7 h-7 text-brand/70" fill="none" stroke="currentColor" strokeWidth="1.5" viewBox="0 0 24 24">
                  <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                </svg>
              </div>
              <div className="text-[13px] font-semibold text-gray-600 mb-1">Ask anything</div>
              <div className="text-[11px] text-gray-400 max-w-[220px] leading-relaxed">
                Field logic, regulatory requirements, data lineage, or compliance queries.
              </div>
            </div>
          )}

          {messages.map((msg) => (
            <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div
                className="max-w-[85%] px-3.5 py-2.5 text-[12.5px] leading-[1.65]"
                style={
                  msg.role === 'user'
                    ? {
                        background: 'linear-gradient(135deg, #dc2626, #b91c1c)',
                        color: '#fff',
                        borderRadius: '14px 14px 4px 14px',
                      }
                    : {
                        background: '#f3f4f6',
                        color: '#374151',
                        borderRadius: '14px 14px 14px 4px',
                      }
                }
              >
                <div className="whitespace-pre-wrap">{msg.content}</div>
                <div className="text-[9px] mt-1.5 opacity-40">
                  {new Date(msg.created_at).toLocaleTimeString()}
                </div>
              </div>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="shrink-0 border-t border-gray-100 px-3 py-3 bg-gray-50/50">
          <div className="flex gap-2">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask a question..."
              rows={1}
              className="flex-1 px-3.5 py-2.5 text-[12.5px] border border-gray-200 rounded-xl bg-white resize-none focus:outline-none focus:ring-2 focus:ring-brand/15 focus:border-brand/30 transition-all"
              style={{ maxHeight: 100 }}
            />
            <button
              onClick={handleSend}
              disabled={!input.trim() || sendMutation.isPending}
              className="px-3 py-2.5 rounded-xl text-white transition-all disabled:opacity-30 hover:shadow-lg active:scale-95"
              style={{ background: 'linear-gradient(135deg, #dc2626, #b91c1c)' }}
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24">
                <line x1="22" y1="2" x2="11" y2="13" /><polygon points="22 2 15 22 11 13 2 9 22 2" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </>
  );
}
