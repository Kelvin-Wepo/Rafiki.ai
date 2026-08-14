/**
 * DashboardPage - Rafiki.ai
 * Main dashboard component matching the design mockup exactly.
 * Features: sidebar navigation, avatar card, quick actions, voice input
 */

import React, { useState, useRef, useCallback, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import {
  PlusIcon,
  ClockIcon,
  DocumentTextIcon,
  EnvelopeIcon,
  PowerIcon,
  MicrophoneIcon,
  PaperAirplaneIcon,
  IdentificationIcon,
  TruckIcon,
  DocumentCheckIcon,
  BuildingLibraryIcon,
  ExclamationTriangleIcon,
  MegaphoneIcon,
} from '@heroicons/react/24/outline';
import LanguageSelector from '../LanguageSelector';
import { ConversationHistory } from './ConversationHistory';
import TranscriptDownload from './TranscriptDownload';
import '../../styles/dashboard.css';
import useChatSessions from '../../hooks/useChatSessions';
import { RafikiTalkingAvatar } from '../avatar';
import { useAudioAnalyzer } from '../../hooks/useAudioAnalyzer';
import type { AvatarState } from '../../types/avatar.types';

// Types
interface QuickAction {
  id: string;
  title: string;
  desc: string;
  message: string;
  icon: React.ReactNode;
}

// Simplified Speech Recognition type (use any for browser compatibility)
type SpeechRecognitionInstance = {
  lang: string;
  continuous: boolean;
  interimResults: boolean;
  onresult: ((event: { results: { [index: number]: { [index: number]: { transcript: string } } } }) => void) | null;
  onerror: ((event: Event) => void) | null;
  onend: (() => void) | null;
  start(): void;
  stop(): void;
};

// API Base URL
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Quick Actions Data
const QUICK_ACTIONS: QuickAction[] = [
  {
    id: 'check-id',
    title: 'Check ID',
    desc: 'Check the status of your National ID card application.',
    message: 'I want to check the status of my National ID application',
    icon: <IdentificationIcon />,
  },
  {
    id: 'renew-license',
    title: 'Renew Driving License',
    desc: 'Renew your Kenyan driving license online.',
    message: 'I want to renew my driving license',
    icon: <TruckIcon />,
  },
  {
    id: 'kra-services',
    title: 'KRA Services',
    desc: 'Access KRA services for taxes and PIN.',
    message: 'I need help with KRA services',
    icon: <DocumentCheckIcon />,
  },
  {
    id: 'huduma-centre',
    title: 'Find Huduma Centre',
    desc: 'Locate and get directions to Huduma Centres.',
    message: 'Find me the nearest Huduma Centre',
    icon: <BuildingLibraryIcon />,
  },
  {
    id: 'emergency',
    title: 'Report Emergency',
    desc: 'Contact the emergency services hotline.',
    message: 'I need to report an emergency',
    icon: <ExclamationTriangleIcon />,
  },
  {
    id: 'corruption',
    title: 'Report Corruption',
    desc: 'Report incidents of corruption to authorities.',
    message: 'I want to report a corruption incident',
    icon: <MegaphoneIcon />,
  },
];

// Nav items
type NavSection = 'chat' | 'history' | 'transcripts';

export function Dashboard() {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const {
    transcripts,
    activeSessionId,
    createNewSession,
    loadSession,
  } = useChatSessions();
  
  // State
  const [activeNav, setActiveNav] = useState<NavSection>('chat');
  const [chatInput, setChatInput] = useState('');
  const [isListening, setIsListening] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [selectedConversation, setSelectedConversation] = useState<any | null>(null);
  const [, setLanguage] = useState<'en' | 'sw' | null>(null);
  const [showLanguageSelector, setShowLanguageSelector] = useState(!import.meta.env.VITE_DEV_SCREENSHOT);
  const [isLanguageLoading, setIsLanguageLoading] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);

  // Refs
  const inputRef = useRef<HTMLInputElement>(null);
  const recognitionRef = useRef<SpeechRecognitionInstance | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  // Drives real mouth/viseme animation on the talking avatar from actual TTS audio
  const { audioData: avatarAudioData, analyzeAudioElement, stopAnalyzing: stopAvatarAnalyzing } = useAudioAnalyzer();

  const avatarState: AvatarState = isSpeaking ? 'speaking' : isListening ? 'listening' : 'idle';

  // Play audio from base64 string
  const playAudio = useCallback((audioBase64: string, mimeType: string = 'audio/mpeg') => {
    try {
      // Stop any currently playing audio
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }

      const audio = new Audio(`data:${mimeType};base64,${audioBase64}`);
      audioRef.current = audio;

      audio.onplay = () => {
        setIsSpeaking(true);
        analyzeAudioElement(audio);
      };
      audio.onended = () => {
        setIsSpeaking(false);
        stopAvatarAnalyzing();
      };
      audio.onerror = () => {
        setIsSpeaking(false);
        stopAvatarAnalyzing();
      };

      audio.play().catch(err => console.error('Audio playback error:', err));
    } catch (err) {
      console.error('Failed to play audio:', err);
    }
  }, [analyzeAudioElement, stopAvatarAnalyzing]);

  // Handle language selection and start session
  const handleLanguageSelect = useCallback(async (selectedLang: 'en' | 'sw') => {
    setIsLanguageLoading(true);
    try {
      // First, start a new chat session
      const startRes = await fetch(`${API_BASE}/api/agencies/chat/start`, { method: 'POST' });
      const startData = await startRes.json();
      setSessionId(startData.session_id);
      
      // Play the greeting audio if available
      if (startData.audio_base64) {
        playAudio(startData.audio_base64, startData.audio_mime || 'audio/mpeg');
      }
      
      // Now send the language selection
      const langRes = await fetch(`${API_BASE}/api/agencies/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: startData.session_id,
          message: selectedLang === 'en' ? '1' : '2',
        }),
      });
      const langData = await langRes.json();
      
      // Play the welcome audio
      if (langData.audio_base64) {
        playAudio(langData.audio_base64, langData.audio_mime || 'audio/mpeg');
      }
      
      setLanguage(selectedLang);
      setShowLanguageSelector(false);
      console.log('Session started with language:', selectedLang);
      console.log('Rafiki says:', langData.response);
    } catch (err) {
      console.error('Failed to start session:', err);
    } finally {
      setIsLanguageLoading(false);
    }
  }, [playAudio]);

  // Get masked user data
  const phone = user?.phone_masked || '+254 7** **045';
  const email = user?.email_masked || 'user@example.com';

  // Handle logout
  const handleLogout = useCallback(async () => {
    localStorage.removeItem('rafiki_session_id');
    localStorage.removeItem('rafiki_last_user');
    await logout();
    navigate('/login');
  }, [logout, navigate]);

  // Send message to backend
  const sendMessage = useCallback(async (message: string) => {
    if (!message.trim()) return;
    setChatInput('');

    try {
      const res = await fetch(`${API_BASE}/api/agencies/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          message: message,
        }),
      });
      const data = await res.json();
      
      // Log the response
      console.log('Assistant response:', data.response || data.message);
      
      // Play audio response if available
      if (data.audio_base64) {
        playAudio(data.audio_base64, data.audio_mime || 'audio/mpeg');
      }
    } catch (err) {
      console.error('Failed to send message:', err);
    }
  }, [sessionId, playAudio]);

  // Handle quick action
  const handleQuickAction = useCallback((action: QuickAction) => {
    setChatInput(action.message);
    sendMessage(action.message);
  }, [sendMessage]);

  // Handle mic toggle for speech recognition
  const handleMicToggle = useCallback(() => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const win = window as any;
    
    if (!win.webkitSpeechRecognition && !win.SpeechRecognition) {
      alert('Voice input is not supported in your browser. Please use Chrome.');
      return;
    }

    if (isListening) {
      recognitionRef.current?.stop();
      setIsListening(false);
      return;
    }

    const SpeechRecognitionClass = win.SpeechRecognition || win.webkitSpeechRecognition;
    const recognition = new SpeechRecognitionClass() as SpeechRecognitionInstance;
    recognition.lang = 'en-KE';
    recognition.continuous = false;
    recognition.interimResults = false;

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      setChatInput(transcript);
      setIsListening(false);
      // Auto-send after voice input
      sendMessage(transcript);
    };

    recognition.onerror = () => setIsListening(false);
    recognition.onend = () => setIsListening(false);

    recognition.start();
    recognitionRef.current = recognition;
    setIsListening(true);
  }, [isListening, sendMessage]);

  // Handle send
  const handleSend = useCallback(() => {
    if (chatInput.trim()) {
      sendMessage(chatInput);
    }
  }, [chatInput, sendMessage]);

  // Handle key press
  const handleKeyDown = useCallback((e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }, [handleSend]);

  // Handle nav click
  const handleNavClick = useCallback((section: NavSection) => {
    setActiveNav(section);
  }, []);

  useEffect(() => {
    const restore = async () => {
      if (activeSessionId && !sessionId) {
        const restored = await loadSession(activeSessionId);
        if (restored?.id || restored?.conversation_id) {
          setSessionId(restored.id || restored.conversation_id || activeSessionId);
          setSelectedConversation(restored);
        } else {
          setSessionId(activeSessionId);
        }
      }
    };
    restore();
  }, [activeSessionId, loadSession, sessionId]);

  return (
    <>
      {/* Language Selector Modal */}
      {showLanguageSelector && (
        <LanguageSelector
          onSelectLanguage={handleLanguageSelect}
          isLoading={isLanguageLoading}
        />
      )}
      
    <div className="dashboard-root">
      {/* ============ ZONE 1: LEFT SIDEBAR ============ */}
      <aside className="sidebar">
        {/* Logo / Brand Block */}
        <div className="sidebar-brand">
          <div className="brand-logo">
            <span>R</span>
          </div>
          <div className="brand-text">
            <span className="brand-name">RAFIKI</span>
            <span className="brand-sub">AI ASSISTANT</span>
          </div>
        </div>

        {/* Navigation Items */}
        <nav className="sidebar-nav">
          <button
            className={`nav-item ${activeNav === 'chat' ? 'nav-item--active' : ''}`}
            onClick={() => handleNavClick('chat')}
            aria-current={activeNav === 'chat' ? 'page' : undefined}
          >
            <PlusIcon aria-hidden="true" />
            <span>New Chat</span>
          </button>
          <button
            className={`nav-item ${activeNav === 'history' ? 'nav-item--active' : ''}`}
            onClick={() => handleNavClick('history')}
            aria-current={activeNav === 'history' ? 'page' : undefined}
          >
            <ClockIcon aria-hidden="true" />
            <span>History</span>
          </button>
          <button
            className={`nav-item ${activeNav === 'transcripts' ? 'nav-item--active' : ''}`}
            onClick={() => handleNavClick('transcripts')}
            aria-current={activeNav === 'transcripts' ? 'page' : undefined}
          >
            <DocumentTextIcon aria-hidden="true" />
            <span>Transcripts</span>
            <span className="nav-badge">{transcripts.length}</span>
          </button>
        </nav>

        {/* User Info Block */}
        <div className="sidebar-user">
          <div className="user-info-row">
            <span className="flag-icon" aria-label="Kenya">🇰🇪</span>
            <span className="user-phone">{phone}</span>
          </div>
          <div className="user-info-row">
            <EnvelopeIcon aria-hidden="true" />
            <span className="user-email">{email}</span>
          </div>
        </div>

        {/* Logout Button */}
        <div className="sidebar-footer">
          <button className="logout-btn" onClick={handleLogout}>
            <PowerIcon aria-hidden="true" />
            <span>Log out</span>
          </button>
        </div>
      </aside>

      {/* ============ ZONE 2: MAIN CONTENT AREA ============ */}
      <main className="main-content">
        {activeNav === 'chat' ? (
          <>
            {/* Avatar Card */}
            <div className="avatar-card">
              {/* Talking avatar - animated, reacts to listening/speaking state */}
              <div className="avatar-wrapper">
                <RafikiTalkingAvatar
                  state={avatarState}
                  audioData={avatarState === 'speaking' ? avatarAudioData : undefined}
                  size="100%"
                  accessible
                  showParticles={false}
                  showWaveform={false}
                />
                <div className="avatar-glow-ring" aria-hidden="true" />
              </div>

              {/* Ready status badge */}
              <div className="status-badge" role="status">
                <span className="status-dot" aria-hidden="true" />
                <span>Ready</span>
              </div>

              {/* Heading */}
              <h1 className="avatar-heading">How can I assist you today?</h1>

              {/* Microphone button */}
              <div className="mic-container">
                <button
                  className={`mic-btn ${isListening ? 'mic-btn--listening' : ''}`}
                  onClick={handleMicToggle}
                  aria-label={isListening ? 'Stop listening' : 'Tap to speak'}
                >
                  {/* Pulse rings — animated when listening */}
                  <span className="mic-pulse mic-pulse--1" aria-hidden="true" />
                  <span className="mic-pulse mic-pulse--2" aria-hidden="true" />
                  <MicrophoneIcon aria-hidden="true" />
                  <span className="mic-label">Tap to Speak</span>
                </button>
              </div>

              {/* Instruction text */}
              <p className="avatar-instruction">Tap to Speak or Type Below</p>
            </div>

            {/* Quick Actions Section */}
            <section className="quick-actions" aria-labelledby="quick-actions-title">
              <h2 id="quick-actions-title" className="quick-actions-title">Quick Actions</h2>
              <div className="actions-grid">
                {QUICK_ACTIONS.map((action) => (
                  <button
                    key={action.id}
                    className="action-card"
                    onClick={() => handleQuickAction(action)}
                    aria-label={`${action.title}: ${action.desc}`}
                  >
                    <div className="action-icon-wrap" aria-hidden="true">
                      {action.icon}
                    </div>
                    <div className="action-text">
                      <span className="action-title">{action.title}</span>
                      <span className="action-desc">{action.desc}</span>
                    </div>
                  </button>
                ))}
              </div>
            </section>

            {/* Footer */}
            <footer className="main-footer">
              <span>🔒 Secure</span>
              <span className="footer-divider" aria-hidden="true">|</span>
              <span>End-to-End Encrypted</span>
              <span className="footer-divider" aria-hidden="true">|</span>
              <span>Powered by Kenyan AI</span>
              <button className="footer-dropdown" aria-label="More info">▾</button>
            </footer>
          </>
        ) : activeNav === 'history' ? (
          <div className="history-view">
            <ConversationHistory
              onSelectConversation={(conversation) => {
                setSelectedConversation(conversation);
                setActiveNav('chat');
              }}
              selectedId={selectedConversation?.id}
              onNewConversation={async () => {
                const id = await createNewSession();
                if (id) {
                  const conv = await loadSession(id);
                  setSelectedConversation(conv || null);
                  setActiveNav('chat');
                }
              }}
            />
          </div>
        ) : (
          <div className="transcripts-view">
            <TranscriptDownload preSelectedConversation={selectedConversation} />
          </div>
        )}
      </main>

      {/* ============ ZONE 3: BOTTOM INPUT BAR ============ */}
      {activeNav === 'chat' && (
        <div className="input-bar">
          {/* Voice toggle button */}
          <button
            className={`input-mic-btn ${isListening ? 'input-mic-btn--active' : ''}`}
            onClick={handleMicToggle}
            aria-label="Voice input"
          >
            <MicrophoneIcon aria-hidden="true" />
          </button>

          {/* Text input */}
          <input
            ref={inputRef}
            type="text"
            className="input-field"
            placeholder="Type your message..."
            value={chatInput}
            onChange={e => setChatInput(e.target.value)}
            onKeyDown={handleKeyDown}
            aria-label="Chat message input"
          />

          {/* Send button */}
          <button
            className="input-send-btn"
            onClick={handleSend}
            disabled={!chatInput.trim() && !isListening}
            aria-label="Send message"
          >
            <PaperAirplaneIcon aria-hidden="true" />
          </button>
        </div>
      )}
    </div>
    </>
  );
}

export default Dashboard;
