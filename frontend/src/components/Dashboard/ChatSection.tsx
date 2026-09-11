import React, { useCallback, useEffect, useRef, useState, type ReactNode } from 'react';
import { MessageSquareText, Mic, Plus, Send } from 'lucide-react';
import type { ElevenLabsRuntimeConfig } from '../../lib/elevenlabsAgent';

export type ChatBubble = {
  id: string;
  sender: 'user' | 'assistant';
  content: string;
  created_at?: string;
};

type SessionSummary = {
  id?: string;
  conversation_id?: string;
  title?: string;
  last_message_preview?: string;
  preview?: string;
  updated_at?: string;
};

interface ChatSectionProps {
  sessions: SessionSummary[];
  activeSessionId: string | null;
  messages: ChatBubble[];
  isSending: boolean;
  voiceConfig: ElevenLabsRuntimeConfig | null;
  composerValue: string;
  onComposerChange: (value: string) => void;
  onSend: () => void;
  onNewChat: () => void;
  onSelectSession: (id: string) => void;
  onOpenVoice: () => void;
  avatar: ReactNode;
}

function formatTime(value?: string): string {
  if (!value) return '';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '';
  return date.toLocaleTimeString('en-KE', { hour: '2-digit', minute: '2-digit' });
}

export function ChatSection({
  sessions,
  activeSessionId,
  messages,
  isSending,
  voiceConfig,
  composerValue,
  onComposerChange,
  onSend,
  onNewChat,
  onSelectSession,
  onOpenVoice,
  avatar,
}: ChatSectionProps) {
  const endRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const [mobileListOpen, setMobileListOpen] = useState(false);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isSending]);

  useEffect(() => {
    inputRef.current?.focus();
  }, [activeSessionId]);

  const handleKeyDown = useCallback(
    (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
      if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        onSend();
      }
    },
    [onSend]
  );

  const agentName = voiceConfig?.name || 'Rafiki';

  return (
    <section className="rd-chat" aria-label="Chat with Rafiki">
      <aside className={`rd-chat-sessions${mobileListOpen ? ' rd-chat-sessions--open' : ''}`}>
        <div className="rd-chat-sessions-head">
          <h2>History</h2>
          <button type="button" className="rd-chat-new" onClick={onNewChat}>
            <Plus size={16} strokeWidth={2} aria-hidden="true" />
            New
          </button>
        </div>
        {sessions.length === 0 ? (
          <p className="rd-chat-sessions-empty">No saved chats yet. Send a message to start one.</p>
        ) : (
          <ul className="rd-chat-session-list">
            {sessions.map((session, index) => {
              const id = session.id || session.conversation_id || `session-${index}`;
              const active = id === activeSessionId;
              return (
                <li key={id}>
                  <button
                    type="button"
                    className={`rd-chat-session${active ? ' rd-chat-session--active' : ''}`}
                    onClick={() => {
                      onSelectSession(id);
                      setMobileListOpen(false);
                    }}
                  >
                    <strong>{session.title || 'Conversation with Rafiki'}</strong>
                    <span>{session.last_message_preview || session.preview || 'No messages yet'}</span>
                  </button>
                </li>
              );
            })}
          </ul>
        )}
      </aside>

      <div className="rd-chat-thread">
        <header className="rd-chat-head">
          <button
            type="button"
            className="rd-chat-sessions-toggle"
            onClick={() => setMobileListOpen((open) => !open)}
          >
            History
          </button>
          <div className="rd-chat-head-copy">
            <h1>Chat with {agentName}</h1>
            <p>Type a message. Switch to Voice if you would rather talk.</p>
          </div>
          <div className="rd-mode-switch" role="tablist" aria-label="Choose Chat or Voice">
            <button type="button" role="tab" aria-selected={true} className="is-active">
              <MessageSquareText size={16} strokeWidth={2} aria-hidden="true" />
              Chat
            </button>
            <button type="button" role="tab" aria-selected={false} onClick={onOpenVoice}>
              <Mic size={16} strokeWidth={2} aria-hidden="true" />
              Voice
            </button>
          </div>
        </header>

        <div className="rd-chat-messages" role="log" aria-live="polite">
          {messages.length === 0 && !isSending && (
            <div className="rd-chat-empty">
              <p>Ask about a passport, NTSA licence, KRA PIN, lost ID, or any other government service.</p>
            </div>
          )}
          {messages.map((message) => (
            <article
              key={message.id}
              className={`rd-chat-bubble rd-chat-bubble--${message.sender}`}
            >
              <p>{message.content}</p>
              {message.created_at && (
                <time dateTime={message.created_at}>{formatTime(message.created_at)}</time>
              )}
            </article>
          ))}
          {isSending && (
            <article className="rd-chat-bubble rd-chat-bubble--assistant rd-chat-bubble--typing">
              <span />
              <span />
              <span />
            </article>
          )}
          <div ref={endRef} />
        </div>

        <form
          className="rd-chat-composer"
          onSubmit={(event) => {
            event.preventDefault();
            onSend();
          }}
        >
          <textarea
            ref={inputRef}
            className="rd-chat-input"
            rows={1}
            placeholder={`Type a message to ${agentName}…`}
            value={composerValue}
            onChange={(event) => onComposerChange(event.target.value)}
            onKeyDown={handleKeyDown}
            aria-label="Message Rafiki"
          />
          <button
            type="submit"
            className="rd-ask-btn rd-ask-send"
            disabled={!composerValue.trim() || isSending}
            aria-label="Send message"
          >
            <Send size={18} strokeWidth={1.75} aria-hidden="true" />
          </button>
        </form>
      </div>

      <aside className="rd-chat-stage" aria-label="Rafiki avatar">
        <div className="rd-chat-stage-avatar">{avatar}</div>
        <p>{agentName}</p>
      </aside>
    </section>
  );
}

export default ChatSection;
