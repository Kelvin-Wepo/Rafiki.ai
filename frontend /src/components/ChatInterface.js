/**
 * Chat Interface Component
 * Accessible chat display with keyboard navigation
 * Uses ElevenLabs for text-to-speech
 */

import React, { useEffect, useRef, useState } from 'react';
import { useSession } from '../context/SessionContext';
import { useAccessibility } from '../context/AccessibilityContext';
import { useElevenLabs } from '../context/ElevenLabsContext';
import api from '../services/api';
import toast from 'react-hot-toast';

function ChatInterface({ onResponse }) {
  const { conversationHistory, sessionId, addMessage } = useSession();
  const { settings, announce } = useAccessibility();
  const { speak: elevenLabsSpeak } = useElevenLabs();
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // Scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [conversationHistory]);

  // Announce new messages for screen readers
  useEffect(() => {
    if (conversationHistory.length > 0) {
      const lastMessage = conversationHistory[conversationHistory.length - 1];
      if (lastMessage.role === 'assistant') {
        announce(`Assistant says: ${lastMessage.content.substring(0, 100)}`);
      }
    }
  }, [conversationHistory, announce]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!inputText.trim() || !sessionId || isLoading) return;

    const text = inputText.trim();
    setInputText('');
    setIsLoading(true);

    // Add user message
    addMessage({
      role: 'user',
      content: text,
      type: 'text',
    });

    try {
      // Determine language code for API: sw-KE for Kiswahili, en-KE for English
      const languageCode = settings.language === 'sw' ? 'sw-KE' : 'en-KE';
      
      const response = await api.processVoiceInput({
        text_input: text,
        session_id: sessionId,
        input_mode: 'text',
        language: languageCode,
      });

      // Add assistant response
      addMessage({
        role: 'assistant',
        content: response.text,
        intent: response.intent,
        entities: response.entities,
        suggestedActions: response.suggested_actions,
      });

      // Speak response using ElevenLabs TTS if enabled
      if (settings.voiceEnabled && settings.autoSpeak) {
        elevenLabsSpeak(response.text);
      }

      // Notify parent
      if (onResponse) {
        onResponse(response);
      }
    } catch (error) {
      console.error('Error sending message:', error);
      toast.error('Failed to send message. Please try again.');
      
      addMessage({
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        isError: true,
      });
    } finally {
      setIsLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleSuggestedAction = (action) => {
    setInputText(action);
    inputRef.current?.focus();
  };

  return (
    <div 
      className="chat-container card"
      role="log"
      aria-label="Conversation with assistant"
      aria-live="polite"
    >
      {/* Messages Area */}
      <div 
        className="chat-messages"
        role="list"
        aria-label="Messages"
      >
        {conversationHistory.length === 0 ? (
          <div className="chat-empty" style={{ textAlign: 'center', padding: 'var(--spacing-xl)' }}>
            <p style={{ color: 'var(--color-text-secondary)' }}>
              Start a conversation by typing a message or using voice input.
            </p>
            <p style={{ color: 'var(--color-text-muted)', fontSize: 'var(--font-size-sm)', marginTop: 'var(--spacing-sm)' }}>
              Try saying "Hello" or "I want to book an appointment"
            </p>
          </div>
        ) : (
          conversationHistory.map((message, index) => (
            <div
              key={message.id || index}
              className={`chat-message ${message.role}`}
              role="listitem"
              aria-label={`${message.role === 'user' ? 'You' : 'Assistant'}: ${message.content}`}
            >
              <div className={`chat-bubble ${message.isError ? 'error' : ''}`}>
                <span className="sr-only">
                  {message.role === 'user' ? 'You said:' : 'Assistant replied:'}
                </span>
                <p>{message.content}</p>
                
                {/* Suggested Actions */}
                {message.suggestedActions && message.suggestedActions.length > 0 && (
                  <div 
                    className="suggested-actions"
                    style={{ 
                      marginTop: 'var(--spacing-md)',
                      display: 'flex',
                      flexWrap: 'wrap',
                      gap: 'var(--spacing-sm)'
                    }}
                  >
                    {message.suggestedActions.map((action, actionIndex) => (
                      <button
                        key={actionIndex}
                        className="btn btn-secondary"
                        onClick={() => handleSuggestedAction(action)}
                        style={{ 
                          padding: 'var(--spacing-xs) var(--spacing-sm)',
                          fontSize: 'var(--font-size-sm)',
                          minHeight: '36px'
                        }}
                      >
                        {action}
                      </button>
                    ))}
                  </div>
                )}
              </div>
              
              {/* Message timestamp (hidden but available for screen readers) */}
              <span className="sr-only">
                Sent at {new Date(message.timestamp).toLocaleTimeString()}
              </span>
            </div>
          ))
        )}
        
        {/* Loading indicator */}
        {isLoading && (
          <div className="chat-message assistant" role="listitem">
            <div className="chat-bubble">
              <span className="loading-spinner" aria-label="Assistant is typing" />
              <span className="sr-only">Assistant is thinking...</span>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <form 
        className="chat-input-container"
        onSubmit={handleSubmit}
        role="search"
        aria-label="Send a message"
      >
        <label htmlFor="chat-input" className="sr-only">
          Type your message
        </label>
        <input
          ref={inputRef}
          id="chat-input"
          type="text"
          className="form-input chat-input"
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Type your message..."
          disabled={isLoading}
          aria-describedby="chat-input-help"
          autoComplete="off"
        />
        <span id="chat-input-help" className="sr-only">
          Press Enter to send your message
        </span>
        
        <button
          type="submit"
          className="btn btn-primary"
          disabled={!inputText.trim() || isLoading}
          aria-label="Send message"
        >
          {isLoading ? (
            <span className="loading-spinner" aria-hidden="true" />
          ) : (
            <svg 
              width="24" 
              height="24" 
              viewBox="0 0 24 24" 
              fill="currentColor"
              aria-hidden="true"
            >
              <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
            </svg>
          )}
          <span className="sr-only">Send</span>
        </button>
      </form>
    </div>
  );
}

export default ChatInterface;
