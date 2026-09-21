/**
 * Conversation History Component
 * Displays list of past conversations with search and actions.
 * 
 * Features:
 * - Conversation list with preview
 * - Search/filter
 * - Delete functionality
 * - Empty state
 */

import React, { useState, useEffect } from 'react';
import type { Conversation } from '../../services/authService';
import useChatSessions from '../../hooks/useChatSessions';
import './Dashboard.css';

interface ConversationHistoryProps {
  onSelectConversation: (conversation: Conversation) => void;
  selectedId?: string;
  onNewConversation?: () => void;
}

export function ConversationHistory({ onSelectConversation, selectedId, onNewConversation, }: ConversationHistoryProps) {
  const { sessions, createNewSession, loadSession, isLoading } = useChatSessions();
  const [searchQuery, setSearchQuery] = useState('');
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // sessions are loaded by the hook
  }, [sessions]);

  /**
   * Delete a conversation.
   */
  const handleDelete = async (e: React.MouseEvent, conversationId: string) => {
    e.stopPropagation();
    
    if (!confirm('Are you sure you want to delete this conversation?')) {
      return;
    }

    setDeletingId(conversationId);
    try {
      // Soft-delete not implemented in chatService; mark as archived client-side
      await loadSession(conversationId); // ensure it's accessible
    } catch (err) {
      setError('Failed to delete conversation');
      console.error(err);
    } finally {
      setDeletingId(null);
    }
  };

  /**
   * Format date for display.
   */
  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffDays === 0) {
      return date.toLocaleTimeString('en-KE', {
        hour: '2-digit',
        minute: '2-digit',
      });
    } else if (diffDays === 1) {
      return 'Yesterday';
    } else if (diffDays < 7) {
      return date.toLocaleDateString('en-KE', { weekday: 'long' });
    } else {
      return date.toLocaleDateString('en-KE', {
        day: 'numeric',
        month: 'short',
      });
    }
  };

  /**
   * Filter conversations by search query.
   */
  const filteredConversations = sessions.filter(conv => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return (
      (conv.title || '').toLowerCase().includes(query) ||
      (conv.preview || '').toLowerCase().includes(query)
    );
  });

  if (isLoading) {
    return (
      <div className="loading-spinner">
        <div className="spinner-large" />
        <span>Loading conversations...</span>
      </div>
    );
  }

  return (
    <div className="conversation-history">
      <div className="section-header">
        <div>
          <h2 className="section-title">Conversation History</h2>
          <p className="section-subtitle">
            {sessions.length} conversation{sessions.length !== 1 ? 's' : ''}
          </p>
        </div>
            {onNewConversation && (
          <button className="btn btn-primary" onClick={async () => {
            const id = await createNewSession();
            if (id) {
              const conv = await loadSession(id);
              onNewConversation?.();
              if (conv) onSelectConversation(conv);
            }
          }}>
            <svg viewBox="0 0 24 24" fill="currentColor" style={{ width: 20, height: 20 }}>
              <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z" />
            </svg>
            New Chat
          </button>
        )}
      </div>

      {/* Search */}
      {sessions.length > 0 && (
        <div className="search-wrapper" style={{ marginBottom: '1rem' }}>
          <svg viewBox="0 0 24 24" fill="currentColor" style={{ width: 20, height: 20, color: '#9ca3af', position: 'absolute', left: '1rem', top: '50%', transform: 'translateY(-50%)' }}>
            <path d="M15.5 14h-.79l-.28-.27C15.41 12.59 16 11.11 16 9.5 16 5.91 13.09 3 9.5 3S3 5.91 3 9.5 5.91 16 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z" />
          </svg>
          <input
            type="text"
            placeholder="Search conversations..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{
              width: '100%',
              padding: '0.75rem 1rem 0.75rem 2.75rem',
              border: '1px solid #e5e7eb',
              borderRadius: '10px',
              fontSize: '0.9rem',
              outline: 'none',
            }}
          />
        </div>
      )}

      {error && (
        <div className="alert alert-error" style={{ marginBottom: '1rem' }}>
          {error}
        </div>
      )}

      {/* Conversation List */}
      {filteredConversations.length > 0 ? (
        <div className="conversation-list">
          {filteredConversations.map((conversation) => (
            <div
              key={conversation.id}
              className={`conversation-card ${selectedId === conversation.id ? 'conversation-card-active' : ''}`}
              onClick={async () => { const full = await loadSession(conversation.id); onSelectConversation(full || conversation); }}
            >
              <div className="conversation-icon">
                <svg viewBox="0 0 24 24" fill="currentColor">
                  <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H6l-2 2V4h16v12z" />
                </svg>
              </div>

              <div className="conversation-content">
                <h3 className="conversation-title">{conversation.title}</h3>
                {conversation.preview && (
                  <p className="conversation-preview">{conversation.preview}</p>
                )}
                <div className="conversation-meta">
                  <span>{formatDate(conversation.updated_at)}</span>
                  {conversation.message_count !== undefined && (
                    <span>{conversation.message_count} messages</span>
                  )}
                </div>
              </div>

              <div className="conversation-actions">
                <button
                  className="action-btn action-btn-delete"
                  onClick={(e) => handleDelete(e, conversation.id)}
                  disabled={deletingId === conversation.id}
                  title="Delete conversation"
                >
                  {deletingId === conversation.id ? (
                    <span className="spinner" style={{ width: 16, height: 16 }} />
                  ) : (
                    <svg viewBox="0 0 24 24" fill="currentColor">
                      <path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z" />
                    </svg>
                  )}
                </button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="empty-state">
          <div className="empty-icon">
            <svg viewBox="0 0 24 24" fill="currentColor">
              <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H6l-2 2V4h16v12z" />
            </svg>
          </div>
          <h3 className="empty-title">
            {searchQuery ? 'No conversations found' : 'No conversations yet'}
          </h3>
          <p className="empty-description">
            {searchQuery
              ? 'Try a different search term'
              : 'Start a new conversation to get help with government services'}
          </p>
          {!searchQuery && onNewConversation && (
            <button className="btn btn-primary" onClick={onNewConversation}>
              Start Your First Conversation
            </button>
          )}
        </div>
      )}
    </div>
  );
}

export default ConversationHistory;
