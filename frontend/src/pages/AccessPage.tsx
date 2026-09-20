/**
 * Rafiki Access — a high-contrast talking keypad for low-vision users.
 * One action at a time. Number keys 1–9. Optional read-aloud.
 */

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { useConversation, ConversationProvider } from '@elevenlabs/react';
import { useAuth } from '../contexts/AuthContext';
import { useAccessMode } from '../contexts/AccessModeContext';
import { useChatSessions } from '../hooks/useChatSessions';
import {
  continueAgencyChat,
  readAgencySessionId,
  startAgencyService,
  writeAgencySessionId,
} from '../lib/agencyWorkflow';
import {
  agentMessageText,
  readConversationToken,
} from '../lib/elevenlabsAgent';
import { playElevenLabsBase64 } from '../lib/elevenlabsAudio';
import {
  isGuidedServiceSlug,
  rememberPendingService,
  titleForService,
  type GuidedServiceSlug,
} from '../lib/guidedServices';
import '../styles/access.css';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

type View = 'home' | 'talk' | 'type' | 'services';

type Bubble = { id: string; sender: 'user' | 'assistant'; content: string };

const SERVICES: { slug: GuidedServiceSlug; en: string; sw: string }[] = [
  { slug: 'ntsa-renew', en: 'Renew a driving licence', sw: 'Fanya upya leseni ya udereva' },
  { slug: 'passport-apply', en: 'Apply for a passport', sw: 'Omba pasipoti' },
  { slug: 'id-replace', en: 'Replace a lost ID', sw: 'Badilisha kitambulisho kilichopotea' },
  { slug: 'kra-pin', en: 'Get a KRA PIN', sw: 'Pata PIN ya KRA' },
  { slug: 'dci-good-conduct', en: 'Police clearance certificate', sw: 'Cheti cha mwenendo mzuri' },
  { slug: 'ncpwd', en: 'NCPWD disability services', sw: 'Huduma za NCPWD' },
];

const COPY = {
  en: {
    brand: 'Rafiki Access',
    tag: 'Talking keypad for government services',
    skip: 'Skip to actions',
    kicker: 'Accessibility layer',
    title: 'Press a number. Rafiki will help.',
    lede: 'This screen is built for low vision: large green type, one step at a time. Listen, then choose.',
    talk: 'Talk to Rafiki',
    talkSub: 'Microphone. Rafiki listens and speaks.',
    type: 'Type to Rafiki',
    typeSub: 'Large keyboard. Rafiki replies in this window.',
    services: 'Government services',
    servicesSub: 'Licence, passport, ID, KRA, and more.',
    signIn: 'Sign in',
    signInSub: 'Continue with your Rafiki account.',
    signUp: 'Create account',
    signUpSub: 'New here? We will set Access mode for you.',
    standard: 'Standard dashboard',
    standardSub: 'Leave Access and use the usual layout.',
    lang: 'Kiswahili',
    speakOn: 'Read aloud on',
    speakOff: 'Read aloud off',
    hint: 'Keyboard: press 1, 2 or 3. Escape goes back.',
    back: 'Back to keypad',
    say: 'Rafiki is saying',
    talkTitle: 'Talk to Rafiki',
    talkReady: 'Press 1 or the green button to start. Speak after you hear the tone.',
    start: 'Start listening',
    stop: 'Stop listening',
    listening: 'Listening',
    speaking: 'Speaking',
    ready: 'Ready',
    typeTitle: 'Type to Rafiki',
    typePlaceholder: 'What do you need help with?',
    send: 'Send',
    servicesTitle: 'Choose a service',
    needAccount: 'Sign in first so Rafiki can start this service for you.',
    gate: 'Sign in to talk, type, or start a service.',
  },
  sw: {
    brand: 'Rafiki Ufikivu',
    tag: 'Kibodi ya sauti kwa huduma za serikali',
    skip: 'Ruka kwenda vitendo',
    kicker: 'Safu ya ufikivu',
    title: 'Bonyeza nambari. Rafiki atakusaidia.',
    lede: 'Skrini hii ni kwa watu wenye uoni hafifu: maandishi makubwa ya kijani, hatua moja. Sikiliza, kisha chagua.',
    talk: 'Ongea na Rafiki',
    talkSub: 'Maikrofoni. Rafiki husikiliza na kuongea.',
    type: 'Andika kwa Rafiki',
    typeSub: 'Kitufe kikubwa. Rafiki hujibu hapa.',
    services: 'Huduma za serikali',
    servicesSub: 'Leseni, pasipoti, kitambulisho, KRA, na zaidi.',
    signIn: 'Ingia',
    signInSub: 'Endelea na akaunti yako ya Rafiki.',
    signUp: 'Fungua akaunti',
    signUpSub: 'Mgeni? Tutawasha hali ya Ufikivu.',
    standard: 'Dashibodi ya kawaida',
    standardSub: 'Toka Ufikivu, tumia muundo wa kawaida.',
    lang: 'English',
    speakOn: 'Soma kwa sauti imewashwa',
    speakOff: 'Soma kwa sauti imezimwa',
    hint: 'Kitufe: bonyeza 1, 2 au 3. Escape inarudi.',
    back: 'Rudi kwenye kibodi',
    say: 'Rafiki anasema',
    talkTitle: 'Ongea na Rafiki',
    talkReady: 'Bonyeza 1 au kitufe cha kijani kuanza. Ongea baada ya sauti.',
    start: 'Anza kusikiliza',
    stop: 'Acha kusikiliza',
    listening: 'Anasikiliza',
    speaking: 'Anaongea',
    ready: 'Tayari',
    typeTitle: 'Andika kwa Rafiki',
    typePlaceholder: 'Unahitaji msaada gani?',
    send: 'Tuma',
    servicesTitle: 'Chagua huduma',
    needAccount: 'Ingia kwanza ili Rafiki aanze huduma hii.',
    gate: 'Ingia ili kuongea, kuandika, au kuanza huduma.',
  },
};

function AccessInner() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { isAuthenticated } = useAuth();
  const { enable, disable, language, setLanguage, speakOn, setSpeakOn, speak, stopSpeaking } =
    useAccessMode();
  const { activeSessionId, createNewSession, persistMessage, sendTurn } = useChatSessions();
  const t = COPY[language];

  const [view, setView] = useState<View>('home');
  const [announcement, setAnnouncement] = useState(t.lede);
  const [draft, setDraft] = useState('');
  const [messages, setMessages] = useState<Bubble[]>([]);
  const [sending, setSending] = useState(false);
  const [agencySessionId, setAgencySessionId] = useState<string | null>(() => readAgencySessionId());
  const [error, setError] = useState<string | null>(null);
  const startedService = useRef<string | null>(null);

  const conversation = useConversation({
    onMessage: (message: unknown) => {
      const parsed = agentMessageText(message);
      if (!parsed?.text) return;
      if (parsed.source !== 'user') {
        setAnnouncement(parsed.text);
      }
    },
  });
  const connected = conversation.status === 'connected';
  const voiceLive = connected || conversation.isSpeaking;

  useEffect(() => {
    enable();
  }, [enable]);

  const announce = useCallback(
    (text: string) => {
      setAnnouncement(text);
      speak(text);
    },
    [speak]
  );

  useEffect(() => {
    if (view === 'talk') {
      stopSpeaking();
      return;
    }
    const intro =
      view === 'home'
        ? `${t.title} ${t.lede}`
        : view === 'type'
          ? t.typeTitle
          : t.servicesTitle;
    announce(intro);
    // Speak once per view/language, not on every announce identity change.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [view, language]);

  const rememberAgency = useCallback((id: string | null) => {
    setAgencySessionId(id);
    writeAgencySessionId(id);
  }, []);

  const requireAuth = useCallback(
    (nextView: View) => {
      if (isAuthenticated) {
        setView(nextView);
        return;
      }
      enable();
      announce(t.needAccount);
      navigate(`/login?next=/access`);
    },
    [announce, enable, isAuthenticated, navigate, t.needAccount]
  );

  const startVoice = useCallback(async () => {
    if (!isAuthenticated) {
      requireAuth('talk');
      return;
    }
    if (connected) {
      await conversation.endSession();
      announce(t.ready);
      return;
    }
    stopSpeaking();
    try {
      const tokenRes = await fetch(`${API_BASE}/elevenlabs/conversation-token`);
      let conversationToken = '';
      if (tokenRes.ok) {
        const data = await tokenRes.json();
        conversationToken = readConversationToken(data);
      }
      if (!conversationToken) {
        setError(language === 'sw' ? 'Sikuweza kuanza sauti.' : 'Could not start voice.');
        return;
      }
      await conversation.startSession({
        conversationToken,
        connectionType: 'webrtc',
      });
    } catch (err) {
      console.error(err);
      setError(language === 'sw' ? 'Sikuweza kuanza sauti.' : 'Could not start voice.');
    }
  }, [connected, conversation, isAuthenticated, language, requireAuth, announce, stopSpeaking, t.ready]);

  const sendTyped = useCallback(async () => {
    const text = draft.trim();
    if (!text || sending) return;
    if (!isAuthenticated) {
      requireAuth('type');
      return;
    }
    setSending(true);
    setError(null);
    setDraft('');
    setMessages((prev) => [...prev, { id: `u-${Date.now()}`, sender: 'user', content: text }]);
    try {
      if (agencySessionId) {
        await persistMessage('user', text);
        const data = await continueAgencyChat(agencySessionId, text, activeSessionId);
        if (data.session_id) rememberAgency(data.session_id);
        if (data.response) {
          setMessages((prev) => [
            ...prev,
            { id: `a-${Date.now()}`, sender: 'assistant', content: data.response },
          ]);
          if (data.audio_base64) {
            stopSpeaking();
            void playElevenLabsBase64(data.audio_base64, data.audio_mime || 'audio/mpeg');
          } else {
            announce(data.response);
          }
          await persistMessage('assistant', data.response);
        }
      } else {
        const updated = await sendTurn(text, language);
        const msgs = updated?.messages || [];
        const last = msgs.length ? msgs[msgs.length - 1] : null;
        const reply =
          last?.content ||
          last?.text ||
          (typeof last === 'string' ? last : '');
        if (reply) {
          setMessages((prev) => [
            ...prev,
            { id: `a-${Date.now()}`, sender: 'assistant', content: String(reply) },
          ]);
          announce(String(reply));
        }
      }
    } catch (err) {
      console.error(err);
      setError(language === 'sw' ? 'Ujumbe haukutumwa.' : 'Message was not sent.');
    } finally {
      setSending(false);
    }
  }, [
    activeSessionId,
    agencySessionId,
    announce,
    draft,
    isAuthenticated,
    language,
    persistMessage,
    rememberAgency,
    requireAuth,
    sendTurn,
    sending,
    stopSpeaking,
  ]);

  const startService = useCallback(
    async (slug: GuidedServiceSlug) => {
      rememberPendingService(slug);
      if (!isAuthenticated) {
        navigate(`/login?next=/access&service=${slug}`);
        return;
      }
      setView('type');
      setError(null);
      try {
        let chatId = activeSessionId;
        if (!chatId) chatId = await createNewSession();
        const data = await startAgencyService(slug, language, chatId);
        if (data.session_id) rememberAgency(data.session_id);
        if (data.response) {
          setMessages([
            { id: `a-${Date.now()}`, sender: 'assistant', content: data.response },
          ]);
          if (data.audio_base64) {
            stopSpeaking();
            void playElevenLabsBase64(data.audio_base64, data.audio_mime || 'audio/mpeg');
          } else {
            announce(data.response);
          }
          await persistMessage('assistant', data.response);
        }
      } catch (err) {
        console.error(err);
        setError(
          language === 'sw'
            ? `Sikuweza kuanza ${titleForService(slug)}.`
            : `Could not start ${titleForService(slug)}.`
        );
      }
    },
    [
      activeSessionId,
      announce,
      createNewSession,
      isAuthenticated,
      language,
      navigate,
      persistMessage,
      rememberAgency,
      stopSpeaking,
    ]
  );

  useEffect(() => {
    const slug = searchParams.get('service');
    if (!isAuthenticated || !isGuidedServiceSlug(slug)) return;
    if (startedService.current === slug) return;
    startedService.current = slug;
    void startService(slug);
  }, [isAuthenticated, searchParams, startService]);

  const leaveAccess = useCallback(() => {
    stopSpeaking();
    disable();
    navigate(isAuthenticated ? '/chat' : '/');
  }, [disable, isAuthenticated, navigate, stopSpeaking]);

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      const target = event.target as HTMLElement | null;
      if (target && (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA')) {
        if (event.key === 'Escape') {
          setView('home');
        }
        return;
      }
      if (event.key === 'Escape' || event.key === '0') {
        if (view !== 'home') setView('home');
        return;
      }
      if (view === 'home') {
        if (event.key === '1') isAuthenticated ? setView('talk') : navigate('/login?next=/access');
        if (event.key === '2') isAuthenticated ? setView('type') : navigate('/signup?next=/access');
        if (event.key === '3') isAuthenticated ? setView('services') : setView('services');
        if (event.key === '4') leaveAccess();
      } else if (view === 'talk' && event.key === '1') {
        void startVoice();
      } else if (view === 'services' && /^[1-6]$/.test(event.key)) {
        const item = SERVICES[Number(event.key) - 1];
        if (item) void startService(item.slug);
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [isAuthenticated, leaveAccess, navigate, startService, startVoice, view]);

  const homeKeys = useMemo(() => {
    if (!isAuthenticated) {
      return [
        { n: '1', label: t.signIn, sub: t.signInSub, primary: true, onClick: () => navigate('/login?next=/access') },
        { n: '2', label: t.signUp, sub: t.signUpSub, onClick: () => navigate('/signup?next=/access') },
        { n: '3', label: t.services, sub: t.servicesSub, onClick: () => setView('services') },
        { n: '4', label: language === 'sw' ? 'Tovuti ya kawaida' : 'Standard website', sub: t.standardSub, onClick: leaveAccess },
      ];
    }
    return [
      { n: '1', label: t.talk, sub: t.talkSub, primary: true, onClick: () => setView('talk') },
      { n: '2', label: t.type, sub: t.typeSub, onClick: () => setView('type') },
      { n: '3', label: t.services, sub: t.servicesSub, onClick: () => setView('services') },
      { n: '4', label: t.standard, sub: t.standardSub, onClick: leaveAccess },
    ];
  }, [isAuthenticated, language, leaveAccess, navigate, t]);

  const voiceStatus = conversation.isSpeaking ? t.speaking : connected ? t.listening : t.ready;

  return (
    <div className="ra-page">
      <a className="ra-skip" href="#ra-actions">
        {t.skip}
      </a>
      <div className="ra-flag" aria-hidden="true">
        <span />
        <span />
        <span />
      </div>
      <header className="ra-header">
        <Link to="/access" className="ra-brand" onClick={() => setView('home')}>
          <span className="ra-brand-name">{t.brand}</span>
          <span className="ra-brand-tag">{t.tag}</span>
        </Link>
        <div className="ra-header-actions">
          <button
            type="button"
            className="ra-chip"
            onClick={() => setLanguage(language === 'en' ? 'sw' : 'en')}
          >
            {t.lang}
          </button>
          <button
            type="button"
            className={`ra-chip${speakOn ? ' is-on' : ''}`}
            aria-pressed={speakOn}
            onClick={() => setSpeakOn(!speakOn)}
          >
            {speakOn ? t.speakOn : t.speakOff}
          </button>
        </div>
      </header>

      <main className="ra-main" id="ra-actions">
        {view !== 'home' && (
          <button type="button" className="ra-chip ra-back" onClick={() => setView('home')}>
            0 · {t.back}
          </button>
        )}

        {view === 'home' && (
          <>
            <p className="ra-kicker">{t.kicker}</p>
            <h1 className="ra-title">{t.title}</h1>
            <p className="ra-lede">{t.lede}</p>
            <div className="ra-keys" role="list">
              {homeKeys.map((key) => (
                <button
                  key={key.n}
                  type="button"
                  className={`ra-key${key.primary ? ' ra-key--primary' : ''}`}
                  onClick={key.onClick}
                >
                  <span className="ra-key-num" aria-hidden="true">
                    {key.n}
                  </span>
                  <span className="ra-key-copy">
                    <span>{key.label}</span>
                    <span className="ra-key-sub">{key.sub}</span>
                  </span>
                </button>
              ))}
            </div>
            <p className="ra-hint">{t.hint}</p>
          </>
        )}

        {view === 'talk' && (
          <section className="ra-stage" aria-labelledby="ra-talk-title">
            <h1 id="ra-talk-title" className="ra-title">
              {t.talkTitle}
            </h1>
            <p className={`ra-status${voiceLive ? ' is-live' : ''}`} role="status">
              <span className="ra-dot" aria-hidden="true" />
              {voiceStatus}
            </p>
            <p className="ra-transcript">{announcement || t.talkReady}</p>
            <button type="button" className="ra-key ra-key--primary" onClick={() => void startVoice()}>
              <span className="ra-key-num" aria-hidden="true">
                1
              </span>
              <span className="ra-key-copy">
                <span>{connected ? t.stop : t.start}</span>
                <span className="ra-key-sub">{t.talkSub}</span>
              </span>
            </button>
            {!isAuthenticated && <p className="ra-hint">{t.gate}</p>}
          </section>
        )}

        {view === 'type' && (
          <section className="ra-stage" aria-labelledby="ra-type-title">
            <h1 id="ra-type-title" className="ra-title">
              {t.typeTitle}
            </h1>
            <div className="ra-log" aria-live="polite">
              {messages.length === 0 && <p className="ra-hint">{t.typePlaceholder}</p>}
              {messages.map((msg) => (
                <article
                  key={msg.id}
                  className={`ra-bubble ra-bubble--${msg.sender}`}
                >
                  {msg.content}
                </article>
              ))}
            </div>
            <form
              className="ra-composer-row"
              onSubmit={(event) => {
                event.preventDefault();
                void sendTyped();
              }}
            >
              <label className="sr-only" htmlFor="ra-composer">
                {t.typePlaceholder}
              </label>
              <textarea
                id="ra-composer"
                className="ra-composer"
                rows={2}
                value={draft}
                onChange={(event) => setDraft(event.target.value)}
                placeholder={t.typePlaceholder}
              />
              <button type="submit" className="ra-key ra-key--primary" disabled={sending}>
                {t.send}
              </button>
            </form>
          </section>
        )}

        {view === 'services' && (
          <section className="ra-stage" aria-labelledby="ra-services-title">
            <h1 id="ra-services-title" className="ra-title">
              {t.servicesTitle}
            </h1>
            <div className="ra-keys" role="list">
              {SERVICES.map((service, index) => (
                <button
                  key={service.slug}
                  type="button"
                  className="ra-key"
                  onClick={() => void startService(service.slug)}
                >
                  <span className="ra-key-num" aria-hidden="true">
                    {index + 1}
                  </span>
                  <span className="ra-key-copy">
                    <span>{language === 'sw' ? service.sw : service.en}</span>
                  </span>
                </button>
              ))}
            </div>
          </section>
        )}

        {error && (
          <p className="ra-error" role="alert">
            {error}
          </p>
        )}
      </main>

      <aside className="ra-say" aria-live="polite">
        <p className="ra-say-label">{t.say}</p>
        <p className="ra-say-text">{announcement}</p>
      </aside>
    </div>
  );
}

export function AccessPage() {
  return (
    <ConversationProvider>
      <AccessInner />
    </ConversationProvider>
  );
}

export default AccessPage;
