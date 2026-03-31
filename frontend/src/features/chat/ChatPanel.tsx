import React, { useCallback, useEffect, useRef, useState } from 'react';
import { MessageCircle, Plus, Trash2, X, Send, Loader2, Bot, User } from 'lucide-react';
import { useAppStore } from '../../store/appStore';
import type { ChatSession } from '../../store/appStore';
import {
  createChatSession, listChatSessions, getChatSession,
  sendMessage, deleteChatSession,
} from '../../api/lineageApi';

export function ChatPanel() {
  const {
    chatOpen, setChatOpen,
    chatSessions, setChatSessions,
    activeChatSession, setActiveChatSession,
    chatMessages, setChatMessages, appendChatMessages,
    isChatLoading, setChatLoading,
    traceResult, jurisdiction,
  } = useAppStore();

  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!chatOpen) return;
    listChatSessions()
      .then((sessions: any) => setChatSessions(sessions))
      .catch(console.error);
  }, [chatOpen]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages]);

  const loadSession = useCallback(async (sessionId: string) => {
    setActiveChatSession(sessionId);
    try {
      const session: any = await getChatSession(sessionId);
      setChatMessages(session.messages || []);
    } catch (e) { console.error(e); }
  }, []);

  const handleNewSession = useCallback(async () => {
    try {
      const session: any = await createChatSession();
      const updated: any = await listChatSessions();
      setChatSessions(updated);
      await loadSession(session.id);
    } catch (e) { console.error(e); }
  }, [loadSession]);

  const handleDeleteSession = useCallback(async (e: React.MouseEvent, sessionId: string) => {
    e.stopPropagation();
    try {
      await deleteChatSession(sessionId);
      const updated: any = await listChatSessions();
      setChatSessions(updated);
      if (activeChatSession === sessionId) {
        setActiveChatSession(null);
        setChatMessages([]);
      }
    } catch (e) { console.error(e); }
  }, [activeChatSession]);

  const handleSend = useCallback(async () => {
    if (!input.trim() || !activeChatSession || isChatLoading) return;
    const content = input.trim();
    setInput('');
    setChatLoading(true);
    try {
      const messages: any = await sendMessage(activeChatSession, {
        content,
        jurisdiction_id: jurisdiction || undefined,
        field_name: traceResult?.field_name || undefined,
      });
      appendChatMessages(messages);
      const updated: any = await listChatSessions();
      setChatSessions(updated);
    } catch (e) { console.error(e); }
    finally { setChatLoading(false); }
  }, [input, activeChatSession, isChatLoading, jurisdiction, traceResult]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); }
  };

  if (!chatOpen) return null;

  return (
    <div
      className="st-panel animate-panel"
      style={{ width: 480 }}
    >
      {/* Header */}
      <div
        className="flex items-center justify-between px-4 shrink-0"
        style={{ height: 48, borderBottom: '1px solid var(--border)' }}
      >
        <div className="flex items-center gap-2.5">
          <div
            style={{
              width: 28, height: 28,
              background: 'rgba(16,185,129,0.1)',
              border: '1px solid rgba(16,185,129,0.25)',
              borderRadius: 4,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}
          >
            <MessageCircle size={13} style={{ color: 'var(--emerald)' }} />
          </div>
          <div>
            <span className="label-heading" style={{ color: 'var(--text-primary)', fontSize: '11px' }}>
              AI ASSISTANT
            </span>
            {traceResult && (
              <span
                style={{
                  display: 'block',
                  fontFamily: "'IBM Plex Mono', monospace",
                  fontSize: '10px',
                  color: 'var(--amber)',
                  marginTop: 1,
                }}
              >
                {traceResult.field_name}
              </span>
            )}
          </div>
        </div>
        <PanelCloseBtn onClick={() => setChatOpen(false)} />
      </div>

      {/* Emerald accent line */}
      <div style={{ height: 1.5, background: 'var(--emerald)', opacity: 0.5 }} />

      <div className="flex flex-1 overflow-hidden">
        {/* Session list */}
        <div
          className="flex flex-col overflow-hidden shrink-0"
          style={{ width: 148, borderRight: '1px solid var(--border)', background: 'var(--bg-base)' }}
        >
          <div className="p-2" style={{ borderBottom: '1px solid var(--border)' }}>
            <button
              onClick={handleNewSession}
              className="w-full flex items-center justify-center gap-1.5 py-1.5 rounded transition-all label-tag"
              style={{
                fontSize: '10px',
                color: 'var(--emerald)',
                border: '1px solid rgba(16,185,129,0.3)',
                background: 'rgba(16,185,129,0.05)',
              }}
              onMouseEnter={(e) => ((e.currentTarget as HTMLElement).style.background = 'rgba(16,185,129,0.1)')}
              onMouseLeave={(e) => ((e.currentTarget as HTMLElement).style.background = 'rgba(16,185,129,0.05)')}
            >
              <Plus size={10} /> NEW CHAT
            </button>
          </div>
          <div className="flex-1 overflow-y-auto p-1">
            {chatSessions.length === 0 && (
              <p style={{ fontSize: '10px', color: 'var(--text-muted)', textAlign: 'center', padding: '12px 8px' }}>
                No sessions
              </p>
            )}
            {chatSessions.map((s: ChatSession) => {
              const isActive = activeChatSession === s.id;
              return (
                <div
                  key={s.id}
                  onClick={() => loadSession(s.id)}
                  className="group flex items-center justify-between px-2 py-1.5 rounded cursor-pointer transition-all"
                  style={{
                    background: isActive ? 'rgba(16,185,129,0.08)' : 'transparent',
                    border: isActive ? '1px solid rgba(16,185,129,0.2)' : '1px solid transparent',
                    marginBottom: 2,
                  }}
                >
                  <span
                    className="truncate flex-1"
                    style={{
                      fontFamily: "'IBM Plex Mono', monospace",
                      fontSize: '10px',
                      color: isActive ? 'var(--emerald)' : 'var(--text-muted)',
                    }}
                  >
                    {s.title || 'New chat'}
                  </span>
                  <button
                    onClick={(e) => handleDeleteSession(e, s.id)}
                    className="opacity-0 group-hover:opacity-100 transition-opacity"
                    style={{ color: 'var(--red)', padding: 2 }}
                  >
                    <Trash2 size={9} />
                  </button>
                </div>
              );
            })}
          </div>
        </div>

        {/* Message thread */}
        <div className="flex-1 flex flex-col overflow-hidden">
          <div className="flex-1 overflow-y-auto p-3 flex flex-col gap-3">
            {!activeChatSession && (
              <div className="flex flex-col items-center justify-center h-full gap-4"
                style={{ color: 'var(--text-muted)' }}>
                <Bot size={32} style={{ opacity: 0.3 }} />
                <span style={{ fontSize: '11px' }}>Select or create a session</span>
              </div>
            )}
            {chatMessages.map((msg) => (
              <div
                key={msg.id}
                className={`flex gap-2 animate-fade-up ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                {msg.role === 'assistant' && (
                  <div
                    style={{
                      width: 24, height: 24,
                      background: 'rgba(16,185,129,0.1)',
                      border: '1px solid rgba(16,185,129,0.25)',
                      borderRadius: '50%',
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      flexShrink: 0, marginTop: 2,
                    }}
                  >
                    <Bot size={11} style={{ color: 'var(--emerald)' }} />
                  </div>
                )}
                <div
                  style={{
                    maxWidth: '83%',
                    padding: '8px 11px',
                    borderRadius: msg.role === 'user' ? '8px 2px 8px 8px' : '2px 8px 8px 8px',
                    background: msg.role === 'user' ? 'rgba(245,166,35,0.12)' : 'var(--bg-elevated)',
                    border: msg.role === 'user'
                      ? '1px solid rgba(245,166,35,0.25)'
                      : '1px solid var(--border)',
                    fontFamily: "'IBM Plex Mono', monospace",
                    fontSize: '11px',
                    lineHeight: 1.6,
                    color: msg.role === 'user' ? '#fde68a' : 'var(--text-secondary)',
                    whiteSpace: 'pre-wrap',
                  }}
                >
                  {msg.content}
                  {msg.field_name && (
                    <div style={{ marginTop: 4, fontSize: '9px', color: 'var(--text-muted)', fontStyle: 'italic' }}>
                      /{msg.field_name}
                    </div>
                  )}
                </div>
                {msg.role === 'user' && (
                  <div
                    style={{
                      width: 24, height: 24,
                      background: 'var(--bg-elevated)',
                      border: '1px solid var(--border)',
                      borderRadius: '50%',
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      flexShrink: 0, marginTop: 2,
                    }}
                  >
                    <User size={11} style={{ color: 'var(--text-secondary)' }} />
                  </div>
                )}
              </div>
            ))}
            {isChatLoading && (
              <div className="flex gap-2 items-center">
                <div
                  style={{
                    width: 24, height: 24,
                    background: 'rgba(16,185,129,0.1)',
                    border: '1px solid rgba(16,185,129,0.25)',
                    borderRadius: '50%',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                  }}
                >
                  <Loader2 size={11} className="animate-spin" style={{ color: 'var(--emerald)' }} />
                </div>
                <div
                  style={{
                    padding: '8px 11px',
                    background: 'var(--bg-elevated)',
                    border: '1px solid var(--border)',
                    borderRadius: '2px 8px 8px 8px',
                  }}
                >
                  <div className="flex gap-1 items-center">
                    {[0, 1, 2].map((i) => (
                      <div
                        key={i}
                        style={{
                          width: 4, height: 4,
                          borderRadius: '50%',
                          background: 'var(--emerald)',
                          animation: 'pulse-amber 1.2s ease-in-out infinite',
                          animationDelay: `${i * 0.2}s`,
                        }}
                      />
                    ))}
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          {activeChatSession && (
            <div
              className="p-3 shrink-0"
              style={{ borderTop: '1px solid var(--border)' }}
            >
              <div className="flex items-end gap-2">
                <textarea
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Ask about this field… (↵ to send)"
                  rows={2}
                  style={{
                    flex: 1,
                    resize: 'none',
                    background: 'var(--bg-elevated)',
                    border: '1px solid var(--border-bright)',
                    borderRadius: 4,
                    padding: '7px 10px',
                    fontFamily: "'IBM Plex Mono', monospace",
                    fontSize: '11px',
                    color: 'var(--text-primary)',
                    outline: 'none',
                    transition: 'border-color 0.15s',
                  }}
                  onFocus={(e) => (e.currentTarget.style.borderColor = 'var(--emerald)')}
                  onBlur={(e) => (e.currentTarget.style.borderColor = 'var(--border-bright)')}
                />
                <button
                  onClick={handleSend}
                  disabled={!input.trim() || isChatLoading}
                  className="flex items-center justify-center transition-all"
                  style={{
                    width: 34, height: 34,
                    borderRadius: 4,
                    background: !input.trim() || isChatLoading ? 'var(--bg-elevated)' : 'var(--emerald)',
                    color: !input.trim() || isChatLoading ? 'var(--text-muted)' : '#04080f',
                    border: 'none',
                    cursor: !input.trim() || isChatLoading ? 'not-allowed' : 'pointer',
                    flexShrink: 0,
                  }}
                >
                  <Send size={13} />
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function PanelCloseBtn({ onClick }: { onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className="flex items-center justify-center transition-all"
      style={{
        width: 26, height: 26, borderRadius: 4,
        color: 'var(--text-muted)',
        border: '1px solid var(--border)',
        background: 'transparent',
      }}
      onMouseEnter={(e) => {
        (e.currentTarget as HTMLElement).style.color = 'var(--text-primary)';
        (e.currentTarget as HTMLElement).style.borderColor = 'var(--border-bright)';
      }}
      onMouseLeave={(e) => {
        (e.currentTarget as HTMLElement).style.color = 'var(--text-muted)';
        (e.currentTarget as HTMLElement).style.borderColor = 'var(--border)';
      }}
    >
      <X size={12} />
    </button>
  );
}
