/**
 * DashboardPage — Rafiki.ai signed-in shell.
 *
 * Layout: fixed left navigation, a content column with the greeting, ask bar
 * and service grid, a right rail carrying the assistant and recent activity,
 * and a full-bleed trust band across the bottom.
 *
 * Palette and type are the landing page's (styles/landing.css), so the signed
 * out and signed in halves of the product read as one thing.
 */

import React, { useState, useRef, useCallback, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useConversation, ConversationProvider } from '@elevenlabs/react';
import {
  LayoutDashboard,
  LayoutGrid,
  CalendarCheck,
  FileText,
  CreditCard,
  BarChart3,
  MessageSquareText,
  Settings as SettingsIcon,
  LogOut,
  Menu,
  Mic,
  Send,
  Car,
  Briefcase,
  ShieldCheck,
  BookUser,
  HeartPulse,
  MapPin,
  Receipt,
  Lock,
  Accessibility,
  Languages,
  Sparkles,
  CircleCheck,
} from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import type { Conversation } from '../../services/authService';
import { RafikiLogo } from '../RafikiLogo';
import LanguageSelector from '../LanguageSelector';
import { ConversationHistory } from './ConversationHistory';
import TranscriptDownload from './TranscriptDownload';
import useChatSessions from '../../hooks/useChatSessions';
import { RafikiTalkingAvatar } from '../avatar';
import { useAudioAnalyzer } from '../../hooks/useAudioAnalyzer';
import type { AvatarState } from '../../types/avatar.types';
import '../../styles/dashboard.css';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const ELEVENLABS_AGENT_ID = import.meta.env.VITE_ELEVENLABS_AGENT_ID || '';

/* ------------------------------------------------------------------ *
 * Navigation
 * ------------------------------------------------------------------ */

type NavId =
  | 'dashboard'
  | 'services'
  | 'appointments'
  | 'documents'
  | 'payments'
  | 'reports'
  | 'feedback'
  | 'settings';

/** `history` is reachable from the rail's "View All", not from the nav. */
type ViewId = NavId | 'history';

const NAV_ITEMS: Array<{ id: NavId; label: string; icon: React.ElementType }> = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { id: 'services', label: 'My Services', icon: LayoutGrid },
  { id: 'appointments', label: 'Appointments', icon: CalendarCheck },
  { id: 'documents', label: 'My Documents', icon: FileText },
  { id: 'payments', label: 'Payments', icon: CreditCard },
  { id: 'reports', label: 'Reports', icon: BarChart3 },
  { id: 'feedback', label: 'Feedback', icon: MessageSquareText },
  { id: 'settings', label: 'Settings', icon: SettingsIcon },
];

/* ------------------------------------------------------------------ *
 * Services — one card per agency the workflow engine actually handles,
 * so every card starts a conversation that can complete.
 * ------------------------------------------------------------------ */

interface ServiceCard {
  id: string;
  name: string;
  desc: string;
  icon: React.ElementType;
  message: string;
}

const SERVICES: ServiceCard[] = [
  {
    id: 'kra',
    name: 'KRA Services',
    desc: 'PIN, returns, compliance',
    icon: Receipt,
    message: 'I need help with KRA services',
  },
  {
    id: 'ntsa',
    name: 'NTSA Services',
    desc: 'Licence, renewals, tests',
    icon: Car,
    message: 'I need help with NTSA services',
  },
  {
    id: 'brs',
    name: 'BRS Services',
    desc: 'Register a business',
    icon: Briefcase,
    message: 'I need help with BRS business registration',
  },
  {
    id: 'dci',
    name: 'DCI Services',
    desc: 'Good conduct certificate',
    icon: ShieldCheck,
    message: 'I need a certificate of good conduct from DCI',
  },
  {
    id: 'immigration',
    name: 'Immigration',
    desc: 'Passport, permits, passes',
    icon: BookUser,
    message: 'I need help with Immigration services',
  },
  {
    id: 'health',
    name: 'Ministry of Health',
    desc: 'NHIF, appointments',
    icon: HeartPulse,
    message: 'I need help with Ministry of Health services',
  },
  {
    id: 'huduma',
    name: 'Huduma Centres',
    desc: 'Find your nearest centre',
    icon: MapPin,
    message: 'Find me the nearest Huduma Centre',
  },
  {
    id: 'more',
    name: 'More Services',
    desc: 'All government agencies',
    icon: LayoutGrid,
    message: 'Show me all the agencies you support',
  },
];

const TRUST_ITEMS = [
  {
    icon: ShieldCheck,
    title: 'Security First',
    sub: 'Encrypted sessions, hash-chained audit logs',
  },
  {
    icon: Lock,
    title: 'Privacy by Design',
    sub: 'Consent-based, data minimisation, PII redaction',
  },
  {
    icon: Accessibility,
    title: 'Accessibility',
    sub: 'WCAG 2.1 AA, voice and text for all',
  },
  {
    icon: Languages,
    title: 'Bilingual',
    sub: 'English and Kiswahili, everywhere',
  },
];

/** Sections without a screen of their own yet, with the prompt each hands to Rafiki. */
const PLACEHOLDERS: Record<
  'appointments' | 'payments' | 'reports' | 'feedback',
  { title: string; text: string; icon: React.ElementType; message: string; cta: string }
> = {
  appointments: {
    title: 'Appointments',
    text: 'Booked appointments will be listed here. For now, Rafiki can book one for you and send the confirmation by SMS.',
    icon: CalendarCheck,
    message: 'I want to book an appointment',
    cta: 'Book an appointment',
  },
  payments: {
    title: 'Payments',
    text: 'Your M-PESA receipts will be listed here. Rafiki can start a payment for any service that has a government fee.',
    icon: CreditCard,
    message: 'What government service fees can I pay through you?',
    cta: 'Ask about fees',
  },
  reports: {
    title: 'Reports',
    text: 'Summaries of your applications will appear here. In the meantime, Rafiki can check the status of anything you have filed.',
    icon: BarChart3,
    message: 'Check the status of my application',
    cta: 'Check a status',
  },
  feedback: {
    title: 'Feedback',
    text: 'Tell us how Rafiki is working for you. You can send feedback anonymously, and it goes straight to the service team.',
    icon: MessageSquareText,
    message: 'I want to submit feedback',
    cta: 'Send feedback',
  },
};

/* ------------------------------------------------------------------ *
 * Helpers
 * ------------------------------------------------------------------ */

/** Only the fields of a chat session this screen reads. */
interface SessionSummary {
  id?: string;
  conversation_id?: string;
  title?: string;
  preview?: string;
  created_at?: string;
  updated_at?: string;
}

function firstNameOf(fullName?: string): string {
  const stored = localStorage.getItem('rafiki_last_user') || '';
  const source = (fullName || stored).trim();
  if (!source) return 'there';
  return source.split(/\s+/)[0];
}

function initialsOf(fullName?: string): string {
  const stored = localStorage.getItem('rafiki_last_user') || '';
  const parts = (fullName || stored).trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return 'R';
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

function formatActivityDate(value?: string): string {
  if (!value) return '';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '';
  return date.toLocaleDateString('en-GB', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  });
}

/* ------------------------------------------------------------------ *
 * Component
 * ------------------------------------------------------------------ */

export function Dashboard() {
  return (
    <ConversationProvider>
      <DashboardInner />
    </ConversationProvider>
  );
}

function DashboardInner() {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const { sessions, transcripts, activeSessionId, createNewSession, loadSession } =
    useChatSessions();

  const [view, setView] = useState<ViewId>('dashboard');
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [chatInput, setChatInput] = useState('');
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [selectedConversation, setSelectedConversation] = useState<Conversation | null>(
    null
  );
  const [language, setLanguage] = useState<'en' | 'sw' | null>(null);
  const [showLanguageSelector, setShowLanguageSelector] = useState(
    !import.meta.env.VITE_DEV_SCREENSHOT
  );
  const [isLanguageLoading, setIsLanguageLoading] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [lastReply, setLastReply] = useState<string | null>(null);

  const inputRef = useRef<HTMLInputElement>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  // Drives the avatar's animation from the actual TTS audio.
  const {
    audioData: avatarAudioData,
    analyzeAudioElement,
    stopAnalyzing: stopAvatarAnalyzing,
  } = useAudioAnalyzer();

  // ElevenLabs agent — handles STT, reasoning and TTS for voice mode.
  const conversation = useConversation({
    onConnect: () => console.log('Voice agent connected'),
    onDisconnect: () => setIsListening(false),
    onMessage: (message: unknown) => console.log('Voice agent message:', message),
    onError: (error: unknown) => {
      console.error('Voice agent error:', error);
      setIsListening(false);
    },
  });

  const isVoiceConnected = conversation.status === 'connected';

  const avatarState: AvatarState = conversation.isSpeaking
    ? 'speaking'
    : isVoiceConnected
      ? 'listening'
      : isSpeaking
        ? 'speaking'
        : isListening
          ? 'listening'
          : 'idle';

  const playAudio = useCallback(
    (audioBase64: string, mimeType: string = 'audio/mpeg') => {
      try {
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

        audio.play().catch((err) => console.error('Audio playback error:', err));
      } catch (err) {
        console.error('Failed to play audio:', err);
      }
    },
    [analyzeAudioElement, stopAvatarAnalyzing]
  );

  const handleLanguageSelect = useCallback(
    async (selectedLang: 'en' | 'sw') => {
      setIsLanguageLoading(true);
      try {
        const startRes = await fetch(`${API_BASE}/api/agencies/chat/start`, {
          method: 'POST',
        });
        const startData = await startRes.json();
        setSessionId(startData.session_id);

        if (startData.audio_base64) {
          playAudio(startData.audio_base64, startData.audio_mime || 'audio/mpeg');
        }

        const langRes = await fetch(`${API_BASE}/api/agencies/chat`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            session_id: startData.session_id,
            message: selectedLang === 'en' ? '1' : '2',
          }),
        });
        const langData = await langRes.json();

        if (langData.audio_base64) {
          playAudio(langData.audio_base64, langData.audio_mime || 'audio/mpeg');
        }

        setLastReply(langData.response || null);
        setLanguage(selectedLang);
        setShowLanguageSelector(false);
      } catch (err) {
        console.error('Failed to start session:', err);
      } finally {
        setIsLanguageLoading(false);
      }
    },
    [playAudio]
  );

  const sendMessage = useCallback(
    async (message: string) => {
      if (!message.trim()) return;
      setChatInput('');

      try {
        const res = await fetch(`${API_BASE}/api/agencies/chat`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ session_id: sessionId, message }),
        });
        const data = await res.json();

        setLastReply(data.response || data.message || null);

        if (data.audio_base64) {
          playAudio(data.audio_base64, data.audio_mime || 'audio/mpeg');
        }
      } catch (err) {
        console.error('Failed to send message:', err);
      }
    },
    [sessionId, playAudio]
  );

  /** Sends a prompt and returns the user to the dashboard so they see the reply. */
  const askRafiki = useCallback(
    (message: string) => {
      setView('dashboard');
      setDrawerOpen(false);
      sendMessage(message);
    },
    [sendMessage]
  );

  const handleMicToggle = useCallback(async () => {
    if (isVoiceConnected) {
      await conversation.endSession();
      setIsListening(false);
      return;
    }

    try {
      await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch (err) {
      console.error('Microphone permission denied:', err);
      alert(
        'Microphone access is required for voice mode. Please allow microphone permissions.'
      );
      setIsListening(false);
      return;
    }

    // Preferred path: the backend mints a token, so the agent can stay private
    // and the API key never reaches the browser.
    let conversationToken: string | null = null;
    try {
      const res = await fetch(`${API_BASE}/elevenlabs/conversation-token`);
      if (res.ok) {
        const data = await res.json();
        if (data.success && data.token) conversationToken = data.token;
        else console.warn('Conversation token unavailable:', data.error);
      }
    } catch (err) {
      console.warn('Could not reach the conversation-token endpoint:', err);
    }

    if (!conversationToken && !ELEVENLABS_AGENT_ID) {
      alert(
        'Voice mode is not configured. Set ELEVENLABS_API_KEY on the server, or VITE_ELEVENLABS_AGENT_ID for a public agent.'
      );
      return;
    }

    try {
      await conversation.startSession(
        conversationToken
          ? { conversationToken, connectionType: 'webrtc' }
          : { agentId: ELEVENLABS_AGENT_ID, connectionType: 'webrtc' }
      );
      setIsListening(true);
    } catch (err) {
      console.error('Failed to start voice conversation:', err);
      alert('Could not start voice mode. Please try again.');
      setIsListening(false);
    }
  }, [conversation, isVoiceConnected]);

  const handleSend = useCallback(() => {
    if (chatInput.trim()) sendMessage(chatInput);
  }, [chatInput, sendMessage]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLInputElement>) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSend();
      }
    },
    [handleSend]
  );

  const handleLogout = useCallback(async () => {
    localStorage.removeItem('rafiki_session_id');
    localStorage.removeItem('rafiki_last_user');
    await logout();
    navigate('/login');
  }, [logout, navigate]);

  const handleNavClick = useCallback((id: NavId) => {
    setView(id);
    setDrawerOpen(false);
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

  // Close the mobile drawer with Escape.
  useEffect(() => {
    if (!drawerOpen) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setDrawerOpen(false);
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [drawerOpen]);

  const firstName = firstNameOf(user?.full_name);
  const initials = initialsOf(user?.full_name);

  /** Real conversations, newest first — no invented activity. */
  const recentActivity = useMemo(
    () =>
      ((sessions || []) as SessionSummary[])
        .slice()
        .sort((a, b) => {
          const at = new Date(a?.updated_at || a?.created_at || 0).getTime();
          const bt = new Date(b?.updated_at || b?.created_at || 0).getTime();
          return bt - at;
        })
        .slice(0, 4)
        .map((s, i) => ({
          id: s?.id || s?.conversation_id || `activity-${i}`,
          label: s?.title || s?.preview || 'Conversation with Rafiki',
          date: formatActivityDate(s?.updated_at || s?.created_at),
        })),
    [sessions]
  );

  const showRail = view === 'dashboard';

  return (
    <>
      {showLanguageSelector && (
        <LanguageSelector
          onSelectLanguage={handleLanguageSelect}
          isLoading={isLanguageLoading}
        />
      )}

      <div className={`rd-app${drawerOpen ? ' rd-app--drawer' : ''}`}>
        {/* ---------------- Sidebar ---------------- */}
        <aside className="rd-sidebar" aria-label="Main navigation">
          <div className="rd-brand">
            <RafikiLogo size={28} />
          </div>

          <nav className="rd-nav" aria-label="Sections">
            {NAV_ITEMS.map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                type="button"
                className={`rd-nav-item${view === id ? ' rd-nav-item--active' : ''}`}
                onClick={() => handleNavClick(id)}
                aria-current={view === id ? 'page' : undefined}
              >
                <Icon size={19} strokeWidth={1.75} aria-hidden="true" />
                <span>{label}</span>
                {id === 'documents' && transcripts.length > 0 && (
                  <span className="rd-nav-count">{transcripts.length}</span>
                )}
              </button>
            ))}
          </nav>

          <div className="rd-sidebar-foot">
            <div className="rd-user">
              <span className="rd-user-avatar" aria-hidden="true">
                {initials}
              </span>
              <span className="rd-user-copy">
                <span className="rd-user-name">{user?.full_name || 'Your account'}</span>
                <span className="rd-user-role">
                  {user?.phone_masked || user?.email_masked || 'Signed in'}
                </span>
              </span>
            </div>
            <button type="button" className="rd-signout" onClick={handleLogout}>
              <LogOut size={17} strokeWidth={1.75} aria-hidden="true" />
              <span>Sign out</span>
            </button>
          </div>
        </aside>

        {drawerOpen && (
          <button
            type="button"
            className="rd-backdrop"
            aria-label="Close navigation"
            onClick={() => setDrawerOpen(false)}
          />
        )}

        {/* ---------------- Main ---------------- */}
        <div className={`rd-main${showRail ? '' : ' rd-main--full'}`}>
          <div className="rd-content">
            <div className="rd-topbar">
              <button
                type="button"
                className="rd-menu-btn"
                onClick={() => setDrawerOpen((open) => !open)}
                aria-label="Open navigation"
                aria-expanded={drawerOpen}
              >
                <Menu size={20} aria-hidden="true" />
              </button>
            </div>

            {view === 'dashboard' && (
              <>
                <h1 className="rd-greeting">
                  Hello, {firstName}
                  <span className="rd-greeting-wave" aria-hidden="true">
                    👋
                  </span>
                </h1>
                <p className="rd-subgreeting">How can I help you today?</p>

                <div className="rd-ask">
                  <button
                    type="button"
                    className={`rd-ask-btn rd-ask-mic${isVoiceConnected ? ' rd-ask-mic--on' : ''}`}
                    onClick={handleMicToggle}
                    aria-label={isVoiceConnected ? 'End voice chat' : 'Start voice chat'}
                  >
                    <Mic size={19} strokeWidth={1.75} aria-hidden="true" />
                  </button>
                  <input
                    ref={inputRef}
                    type="text"
                    className="rd-ask-input"
                    placeholder="e.g. Renew driving licence, KRA PIN, Business registration…"
                    value={chatInput}
                    onChange={(e) => setChatInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    aria-label="Ask Rafiki"
                  />
                  <button
                    type="button"
                    className="rd-ask-btn rd-ask-send"
                    onClick={handleSend}
                    disabled={!chatInput.trim()}
                    aria-label="Send"
                  >
                    <Send size={18} strokeWidth={1.75} aria-hidden="true" />
                  </button>
                </div>

                <h2 className="rd-section-title">Popular Services</h2>
                <ServiceGrid onSelect={askRafiki} />
              </>
            )}

            {view === 'services' && (
              <section className="rd-panel" aria-labelledby="services-heading">
                <div className="rd-panel-head">
                  <h1 id="services-heading" className="rd-panel-title">
                    My Services
                  </h1>
                  <p className="rd-panel-sub">
                    Every agency Rafiki can take you through end to end. Pick one to
                    start.
                  </p>
                </div>
                <div style={{ marginTop: 18 }}>
                  <ServiceGrid onSelect={askRafiki} />
                </div>
              </section>
            )}

            {view === 'documents' && (
              <section className="rd-panel">
                <TranscriptDownload preSelectedConversation={selectedConversation} />
              </section>
            )}

            {view === 'history' && (
              <section className="rd-panel">
                <ConversationHistory
                  onSelectConversation={(conversation) => {
                    setSelectedConversation(conversation);
                    setView('dashboard');
                  }}
                  selectedId={selectedConversation?.id}
                  onNewConversation={async () => {
                    const id = await createNewSession();
                    if (id) {
                      const conv = await loadSession(id);
                      setSelectedConversation(conv || null);
                      setView('dashboard');
                    }
                  }}
                />
              </section>
            )}

            {view === 'settings' && (
              <SettingsPanel
                language={language}
                voiceConfigured={Boolean(ELEVENLABS_AGENT_ID)}
                voiceConnected={isVoiceConnected}
                phone={user?.phone_masked}
                email={user?.email_masked}
                onChangeLanguage={() => setShowLanguageSelector(true)}
                onToggleVoice={handleMicToggle}
                onSignOut={handleLogout}
              />
            )}

            {(view === 'appointments' ||
              view === 'payments' ||
              view === 'reports' ||
              view === 'feedback') && (
              <PlaceholderPanel spec={PLACEHOLDERS[view]} onAsk={askRafiki} />
            )}
          </div>

          {/* ---------------- Right rail ---------------- */}
          {showRail && (
            <aside className="rd-rail" aria-label="Assistant and recent activity">
              <section className="rd-card">
                <div className="rd-card-head">
                  <Sparkles
                    size={17}
                    strokeWidth={1.75}
                    aria-hidden="true"
                    color="#15803d"
                  />
                  <h2 className="rd-card-title">Rafiki Assistant</h2>
                </div>
                <div className="rd-card-body">
                  <div className="rd-assistant-figure">
                    <RafikiTalkingAvatar
                      state={avatarState}
                      audioData={avatarState === 'speaking' ? avatarAudioData : undefined}
                      size="100%"
                      accessible
                      showParticles={false}
                      showWaveform={false}
                    />
                  </div>

                  <div
                    className={`rd-assistant-state${
                      isVoiceConnected || isSpeaking ? ' rd-assistant-state--live' : ''
                    }`}
                    role="status"
                  >
                    <span className="rd-assistant-dot" aria-hidden="true" />
                    <span>
                      {conversation.isSpeaking || isSpeaking
                        ? 'Speaking'
                        : isVoiceConnected
                          ? 'Listening'
                          : 'Ready'}
                    </span>
                  </div>

                  <p className="rd-assistant-copy">
                    {lastReply
                      ? lastReply.length > 150
                        ? `${lastReply.slice(0, 150)}…`
                        : lastReply
                      : "I'm here to help you access government services easily."}
                  </p>

                  <button type="button" className="rd-btn-primary" onClick={handleMicToggle}>
                    <Mic size={17} strokeWidth={1.75} aria-hidden="true" />
                    {isVoiceConnected ? 'End Voice Chat' : 'Start Chat'}
                  </button>
                </div>
              </section>

              <section className="rd-card">
                <div className="rd-card-head">
                  <h2 className="rd-card-title">Recent Activities</h2>
                </div>

                {recentActivity.length > 0 ? (
                  <ul className="rd-activity">
                    {recentActivity.map((item) => (
                      <li key={item.id} className="rd-activity-item">
                        <span className="rd-activity-icon" aria-hidden="true">
                          <CircleCheck size={15} strokeWidth={2} />
                        </span>
                        <span className="rd-activity-label">{item.label}</span>
                        {item.date && <span className="rd-activity-date">{item.date}</span>}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="rd-activity-empty">
                    No activity yet. Anything you do with Rafiki will show up here.
                  </p>
                )}

                <div className="rd-card-foot">
                  <button
                    type="button"
                    className="rd-link-btn"
                    onClick={() => setView('history')}
                  >
                    View All
                  </button>
                </div>
              </section>
            </aside>
          )}
        </div>

        {/* ---------------- Trust band ---------------- */}
        <footer className="rd-trust">
          <ul className="rd-trust-list">
            {TRUST_ITEMS.map(({ icon: Icon, title, sub }) => (
              <li key={title} className="rd-trust-item">
                <span className="rd-trust-icon" aria-hidden="true">
                  <Icon size={22} strokeWidth={1.75} />
                </span>
                <span className="rd-trust-copy">
                  <span className="rd-trust-title">{title}</span>
                  <span className="rd-trust-sub">{sub}</span>
                </span>
              </li>
            ))}
          </ul>
        </footer>
      </div>
    </>
  );
}

/* ------------------------------------------------------------------ *
 * Sub-components
 * ------------------------------------------------------------------ */

function ServiceGrid({ onSelect }: { onSelect: (message: string) => void }) {
  return (
    <ul className="rd-services">
      {SERVICES.map(({ id, name, desc, icon: Icon, message }) => (
        <li key={id}>
          <button
            type="button"
            className="rd-service"
            onClick={() => onSelect(message)}
            aria-label={`${name}: ${desc}`}
          >
            <span className="rd-service-icon" aria-hidden="true">
              <Icon size={22} strokeWidth={1.75} />
            </span>
            <span>
              <span className="rd-service-name">{name}</span>
              <span className="rd-service-desc">{desc}</span>
            </span>
          </button>
        </li>
      ))}
    </ul>
  );
}

function PlaceholderPanel({
  spec,
  onAsk,
}: {
  spec: (typeof PLACEHOLDERS)[keyof typeof PLACEHOLDERS];
  onAsk: (message: string) => void;
}) {
  const Icon = spec.icon;
  return (
    <section className="rd-panel">
      <div className="rd-placeholder">
        <span className="rd-placeholder-icon" aria-hidden="true">
          <Icon size={28} strokeWidth={1.75} />
        </span>
        <h1 className="rd-placeholder-title">{spec.title}</h1>
        <p className="rd-placeholder-text">{spec.text}</p>
        <button
          type="button"
          className="rd-btn-secondary"
          onClick={() => onAsk(spec.message)}
        >
          <Mic size={17} strokeWidth={1.75} aria-hidden="true" />
          {spec.cta}
        </button>
      </div>
    </section>
  );
}

function SettingsPanel({
  language,
  voiceConfigured,
  voiceConnected,
  phone,
  email,
  onChangeLanguage,
  onToggleVoice,
  onSignOut,
}: {
  language: 'en' | 'sw' | null;
  voiceConfigured: boolean;
  voiceConnected: boolean;
  phone?: string;
  email?: string;
  onChangeLanguage: () => void;
  onToggleVoice: () => void;
  onSignOut: () => void;
}) {
  return (
    <section className="rd-panel" aria-labelledby="settings-heading">
      <div className="rd-panel-head">
        <h1 id="settings-heading" className="rd-panel-title">
          Settings
        </h1>
        <p className="rd-panel-sub">Your language, voice and account preferences.</p>
      </div>

      <div style={{ marginTop: 8 }}>
        <div className="rd-setting">
          <span className="rd-setting-copy">
            <span className="rd-setting-name">Conversation language</span>
            <span className="rd-setting-desc">
              {language === 'sw'
                ? 'Kiswahili'
                : language === 'en'
                  ? 'English'
                  : 'Not selected yet'}
            </span>
          </span>
          <button type="button" className="rd-btn-secondary" onClick={onChangeLanguage}>
            Change
          </button>
        </div>

        <div className="rd-setting">
          <span className="rd-setting-copy">
            <span className="rd-setting-name">Voice mode</span>
            <span className="rd-setting-desc">
              {!voiceConfigured
                ? 'Not configured on this deployment'
                : voiceConnected
                  ? 'Connected — Rafiki is listening'
                  : 'Speak to Rafiki instead of typing'}
            </span>
          </span>
          <button
            type="button"
            className="rd-btn-secondary"
            onClick={onToggleVoice}
            disabled={!voiceConfigured}
          >
            {voiceConnected ? 'End' : 'Start'}
          </button>
        </div>

        <div className="rd-setting">
          <span className="rd-setting-copy">
            <span className="rd-setting-name">Account</span>
            <span className="rd-setting-desc">
              {[phone, email].filter(Boolean).join(' · ') || 'Signed in'}
            </span>
          </span>
          <button type="button" className="rd-btn-secondary" onClick={onSignOut}>
            <LogOut size={16} strokeWidth={1.75} aria-hidden="true" />
            Sign out
          </button>
        </div>
      </div>
    </section>
  );
}

export default Dashboard;
