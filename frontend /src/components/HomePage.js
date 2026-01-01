import React, { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAccessibility } from '../context/AccessibilityContext';
import { useSession } from '../context/SessionContext';
import { useElevenLabs } from '../context/ElevenLabsContext';
import VoiceInterface from './VoiceInterface';
import ChatInterface from './ChatInterface';
import ServiceCard from './ServiceCard';
import api from '../services/api';
import toast from 'react-hot-toast';
import './HomePage.css';

const SERVICES_DEFAULT = [
  { service_type: 'passport', name: 'Passport', name_sw: 'Pasipoti', icon: '🛂' },
  { service_type: 'national_id', name: 'National ID', name_sw: 'Kitambulisho', icon: '🪪' },
  { service_type: 'driving_license', name: 'Driving License', name_sw: 'Leseni', icon: '🚗' },
  { service_type: 'good_conduct', name: 'Good Conduct', name_sw: 'Mwenendo Mwema', icon: '📜' },
];

function HomePage() {
  const navigate = useNavigate();
  const { settings, updateSetting } = useAccessibility();
  const { isLoading: sessionLoading } = useSession();
  const { speak, setLanguage } = useElevenLabs();
  const [services, setServices] = useState(SERVICES_DEFAULT);
  const [isLoading, setIsLoading] = useState(true);
  const [showLangModal, setShowLangModal] = useState(true);

  const t = (en, sw) => settings.language === 'sw' ? sw : en;

  useEffect(() => {
    api.getServices()
      .then(data => setServices(data.services || SERVICES_DEFAULT))
      .catch(() => toast.error('Failed to load services'))
      .finally(() => setIsLoading(false));
  }, []);

  const selectLang = useCallback((lang) => {
    updateSetting('language', lang);
    setLanguage(lang);
    setShowLangModal(false);
    // Speak welcome message using ElevenLabs TTS
    speak(lang === 'en' 
      ? "Welcome! I'm Habari, your eCitizen assistant. How can I help you today?" 
      : "Karibu! Mimi ni Habari, msaidizi wako wa eCitizen. Naweza kukusaidia vipi leo?");
    toast.success(lang === 'en' ? 'English' : 'Kiswahili');
  }, [updateSetting, setLanguage, speak]);

  useEffect(() => {
    const handler = (e) => {
      if (!showLangModal) return;
      if (e.key === '1') selectLang('en');
      if (e.key === '2') selectLang('sw');
    };
    window.addEventListener('keypress', handler);
    return () => window.removeEventListener('keypress', handler);
  }, [showLangModal, selectLang]);

  if (isLoading || sessionLoading) {
    return (
      <div className="loading">
        <div className="spinner" />
        <p>Loading...</p>
      </div>
    );
  }

  return (
    <div className="home">
      {/* Language Modal */}
      {showLangModal && (
        <div className="modal-overlay">
          <div className="modal">
            <span className="modal-emoji">👋</span>
            <h2>Welcome / Karibu</h2>
            <p>I'm <strong>Habari</strong>, your assistant</p>
            <div className="lang-buttons">
              <button onClick={() => selectLang('en')} className="btn primary">
                🇬🇧 English (1)
              </button>
              <button onClick={() => selectLang('sw')} className="btn secondary">
                🇰🇪 Kiswahili (2)
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Hero */}
      <section className="hero">
        <h1>{t('eCitizen Voice Assistant', 'Msaidizi wa Sauti wa eCitizen')}</h1>
        <p>{t(
          'Access government services using your voice',
          'Pata huduma za serikali kwa kutumia sauti yako'
        )}</p>
      </section>

      {/* Voice Section */}
      <section className="voice-section">
        <VoiceInterface />
        <ChatInterface onResponse={(r) => {
          if (r.intent === 'book_appointment' && r.entities?.service_type) {
            navigate(`/booking/${r.entities.service_type}`);
          }
        }} />
      </section>

      {/* Services */}
      <section className="services-section">
        <h2>{t('Services', 'Huduma')}</h2>
        <div className="services-grid">
          {services.map((s) => (
            <ServiceCard
              key={s.service_type}
              service={s}
              onSelect={() => navigate(`/booking/${s.service_type}`)}
            />
          ))}
        </div>
      </section>

      {/* Quick Help */}
      <section className="help-section">
        <h3>{t('Voice Commands', 'Amri za Sauti')}</h3>
        <ul>
          <li>"I need a passport" / "Nataka pasipoti"</li>
          <li>"Book appointment" / "Weka miadi"</li>
          <li>"What services?" / "Huduma gani?"</li>
        </ul>
      </section>
    </div>
  );
}

export default HomePage;
