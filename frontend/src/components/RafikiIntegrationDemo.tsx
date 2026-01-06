/**
 * RafikiIntegrationDemo - Full Backend-Frontend Integration Demo
 * 
 * Demonstrates the complete flow:
 * 1. User enters text or speaks
 * 2. Text is sent to backend
 * 3. Backend generates TTS audio + SadTalker video
 * 4. Frontend displays lip-synced avatar video
 * 5. Falls back to animated avatar if backend unavailable
 */

import React, { useState, useCallback } from 'react';
import { RafikiSadTalkerAvatar } from './avatar';
import { useSadTalker } from '../hooks';
import type { Emotion } from '../hooks/useEmotions';
import './RafikiIntegrationDemo.css';

// Demo messages
const DEMO_MESSAGES = [
  "Hello! I'm Rafiki, your government AI assistant. How may I help you today?",
  "I can help you with ID applications, passport renewals, and other government services.",
  "Let me check that information for you. One moment please.",
  "Your appointment has been scheduled. You will receive an SMS confirmation.",
  "Is there anything else I can assist you with today?"
];

type Status = 'idle' | 'listening' | 'speaking' | 'thinking' | 'error';

const RafikiIntegrationDemo: React.FC = () => {
  // State
  const [inputText, setInputText] = useState('');
  const [status, setStatus] = useState<Status>('idle');
  const [emotion, setEmotion] = useState<Emotion>('neutral');
  const [messages, setMessages] = useState<Array<{ role: 'user' | 'assistant'; text: string }>>([]);
  const [selectedAvatar, setSelectedAvatar] = useState('habari');
  
  // SadTalker hook
  const {
    isGenerating,
    currentJob,
    currentVideoUrl,
    currentAudioUrl,
    isFallbackMode,
    isBackendAvailable,
    isSadTalkerAvailable,
    availableAvatars,
    error,
    generateFromText,
    cancel,
    revokeCurrentVideo
  } = useSadTalker({
    backendUrl: import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000',
    avatarId: selectedAvatar,
    onProgress: (progress: number, message: string) => {
      console.log(`Progress: ${Math.round(progress * 100)}% - ${message}`);
    },
    onComplete: (_mediaUrl: string) => {
      console.log('Media ready, fallback:', isFallbackMode);
      setStatus('speaking');
      setEmotion('confident');
    },
    onError: (err: string) => {
      console.error('SadTalker error:', err);
      setStatus('error');
      setEmotion('apologetic');
    }
  });

  // Handle text submission
  const handleSubmit = useCallback(async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    
    const text = inputText.trim();
    if (!text) return;
    
    // Add user message
    setMessages(prev => [...prev, { role: 'user', text }]);
    setInputText('');
    setStatus('thinking');
    setEmotion('attentive');
    
    // Simulate AI response (in production, call your AI backend)
    const responseText = DEMO_MESSAGES[Math.floor(Math.random() * DEMO_MESSAGES.length)];
    
    // Generate video with SadTalker
    const videoUrl = await generateFromText(responseText);
    
    // Add assistant message
    setMessages(prev => [...prev, { role: 'assistant', text: responseText }]);
    
    if (!videoUrl) {
      // Fallback: just show the message without video
      setStatus('speaking');
      setTimeout(() => {
        setStatus('idle');
        setEmotion('neutral');
      }, 3000);
    }
  }, [inputText, generateFromText]);

  // Handle demo button click
  const handleDemoClick = useCallback(async (text: string) => {
    setStatus('thinking');
    setEmotion('attentive');
    setMessages(prev => [...prev, { role: 'assistant', text }]);
    
    const videoUrl = await generateFromText(text);
    
    if (!videoUrl) {
      setStatus('speaking');
      setTimeout(() => {
        setStatus('idle');
        setEmotion('neutral');
      }, 3000);
    }
  }, [generateFromText]);

  // Handle video end
  const handleVideoEnd = useCallback(() => {
    setStatus('idle');
    setEmotion('happy');
    revokeCurrentVideo();
    
    // Reset emotion after a moment
    setTimeout(() => setEmotion('neutral'), 1500);
  }, [revokeCurrentVideo]);

  // Handle cancel
  const handleCancel = useCallback(() => {
    cancel();
    setStatus('idle');
    setEmotion('neutral');
  }, [cancel]);

  return (
    <div className="rafiki-integration-demo">
      {/* Header */}
      <header className="demo-header">
        <h1>Rafiki AI Assistant</h1>
        <p>Government Services Voice Interface with SadTalker Lip-Sync</p>
        
        <div className="backend-status">
          <span className={`status-dot ${isBackendAvailable ? 'online' : isBackendAvailable === false ? 'offline' : 'checking'}`} />
          <span>
            Backend: {isBackendAvailable === null ? 'Checking...' : isBackendAvailable ? 'Online' : 'Offline'}
          </span>
          {isBackendAvailable && (
            <>
              <span className="separator">|</span>
              <span className={`status-dot ${isSadTalkerAvailable ? 'online' : 'offline'}`} />
              <span>
                SadTalker: {isSadTalkerAvailable ? 'Available' : 'Unavailable (audio mode)'}
              </span>
            </>
          )}
        </div>
      </header>

      <div className="demo-content">
        {/* Avatar Section */}
        <div className="avatar-section">
          <RafikiSadTalkerAvatar
            size={400}
            status={status}
            videoUrl={currentVideoUrl}
            audioUrl={currentAudioUrl}
            isFallbackMode={isFallbackMode}
            isGenerating={isGenerating}
            progress={currentJob?.progress || 0}
            progressMessage={currentJob?.status === 'processing' ? 'Generating lip-synced video...' : ''}
            onVideoEnd={handleVideoEnd}
            onAudioEnd={handleVideoEnd}
            enableGlow={true}
            showParticles={true}
            emotion={emotion}
          />
          
          {/* Avatar selector */}
          {availableAvatars.length > 1 && (
            <div className="avatar-selector">
              <label>Avatar:</label>
              <select 
                value={selectedAvatar} 
                onChange={(e) => setSelectedAvatar(e.target.value)}
                disabled={isGenerating}
              >
                {availableAvatars.map((avatar: { id: string; name: string }) => (
                  <option key={avatar.id} value={avatar.id}>
                    {avatar.name}
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Status display */}
          <div className="status-display">
            <span className={`status-badge ${status}`}>
              {status.charAt(0).toUpperCase() + status.slice(1)}
            </span>
            {isGenerating && (
              <button className="cancel-button" onClick={handleCancel}>
                Cancel
              </button>
            )}
          </div>

          {/* Error display */}
          {error && (
            <div className="error-message">
              <strong>Error:</strong> {error}
            </div>
          )}
        </div>

        {/* Chat Section */}
        <div className="chat-section">
          {/* Messages */}
          <div className="messages-container">
            {messages.length === 0 ? (
              <div className="empty-state">
                <p>Start a conversation with Rafiki</p>
                <p className="hint">
                  {isBackendAvailable 
                    ? 'Type a message or try a demo below'
                    : 'Backend offline - using animated avatar fallback'}
                </p>
              </div>
            ) : (
              messages.map((msg, idx) => (
                <div key={idx} className={`message ${msg.role}`}>
                  <div className="message-content">{msg.text}</div>
                </div>
              ))
            )}
          </div>

          {/* Input */}
          <form className="input-section" onSubmit={handleSubmit}>
            <input
              type="text"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              placeholder="Type your message..."
              disabled={isGenerating}
            />
            <button 
              type="submit" 
              disabled={!inputText.trim() || isGenerating}
              className="send-button"
            >
              Send
            </button>
          </form>

          {/* Demo buttons */}
          <div className="demo-buttons">
            <p>Quick demos:</p>
            <div className="button-grid">
              {DEMO_MESSAGES.slice(0, 3).map((text, idx) => (
                <button
                  key={idx}
                  onClick={() => handleDemoClick(text)}
                  disabled={isGenerating}
                  className="demo-button"
                >
                  {text.substring(0, 40)}...
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Tech info */}
      <footer className="demo-footer">
        <div className="tech-info">
          <h3>Integration Details</h3>
          <ul>
            <li><strong>Frontend:</strong> React + TypeScript + Vite</li>
            <li><strong>Backend:</strong> FastAPI + SadTalker</li>
            <li><strong>TTS:</strong> ElevenLabs / Google TTS</li>
            <li><strong>Lip-Sync:</strong> SadTalker neural network</li>
            <li><strong>Fallback:</strong> Animated avatar with eye tracking</li>
          </ul>
        </div>
        
        <div className="api-endpoints">
          <h3>API Endpoints</h3>
          <code>POST /api/avatar/text-to-video</code>
          <code>POST /api/avatar/animate</code>
          <code>GET /api/avatar/avatars</code>
          <code>GET /api/avatar/health</code>
        </div>
      </footer>
    </div>
  );
};

export default RafikiIntegrationDemo;
