import React, { useState, useEffect, useCallback } from 'react';
import { useAccessibility } from '../context/AccessibilityContext';
import { useElevenLabs } from '../context/ElevenLabsContext';
import TalkingAvatar from './TalkingAvatar';
import voiceBookingService from '../services/voiceBookingService';
import toast from 'react-hot-toast';
import './VoiceInterface.css';

function VoiceInterface({ disabled = false }) {
  const [bookingStatus, setBookingStatus] = useState(null);
  const { settings, announce } = useAccessibility();
  const {
    isConnected,
    status,
    transcript,
    response,
    startConversation,
    endConversation,
    setLanguage
  } = useElevenLabs();

  const t = (en, sw) => settings.language === 'sw' ? sw : en;

  // Process voice input for booking automation
  const processForBooking = useCallback((userText) => {
    if (!userText) return;
    voiceBookingService.setLanguage(settings.language);
    const result = voiceBookingService.processInput(userText);
    
    if (result.complete) {
      toast.success(t('Opening eCitizen...', 'Inafungua eCitizen...'));
      setBookingStatus(null);
    } else if (result.service) {
      setBookingStatus(voiceBookingService.getStatus());
    }
    
    return result;
  }, [settings.language]);

  // Sync language with ElevenLabs
  useEffect(() => {
    setLanguage(settings.language);
    voiceBookingService.setLanguage(settings.language);
  }, [settings.language, setLanguage]);

  // Process transcript for booking
  useEffect(() => {
    if (transcript) {
      processForBooking(transcript);
    }
  }, [transcript, processForBooking]);

  const toggle = useCallback(async () => {
    if (isConnected) {
      await endConversation();
      setBookingStatus(null);
      voiceBookingService.cancel();
      announce(t('Ended', 'Imemalizika'));
    } else {
      announce(t('Connecting...', 'Inaunganisha...'));
      const ok = await startConversation();
      if (!ok) {
        toast.error(t('Failed to connect', 'Imeshindwa kuunganisha'));
      } else {
        toast.success(t('Connected!', 'Imeunganishwa!'));
      }
    }
  }, [isConnected, startConversation, endConversation, announce]);

  const statusText = {
    connecting: t('Connecting...', 'Inaunganisha...'),
    listening: t('Listening...', 'Inasikiliza...'),
    speaking: t('Speaking...', 'Inazungumza...'),
    idle: t('Tap to talk', 'Bonyeza kuongea'),
    connected: t('Listening...', 'Inasikiliza...'),
    error: t('Error - Tap to retry', 'Hitilafu - Bonyeza tena'),
  };

  return (
    <div className="voice-interface">
      <TalkingAvatar
        isListening={status === 'listening' || status === 'connected'}
        isSpeaking={status === 'speaking'}
        size="large"
      />

      {/* Booking Progress */}
      {bookingStatus && bookingStatus.service && (
        <div className="booking-progress">
          <span className="booking-badge">
            📋 {t('Booking:', 'Maombi:')} {bookingStatus.service}
          </span>
          {Object.keys(bookingStatus.data).length > 0 && (
            <div className="collected-data">
              {Object.entries(bookingStatus.data).map(([k, v]) => (
                <span key={k} className="data-chip">{k}: {v}</span>
              ))}
            </div>
          )}
        </div>
      )}

      {isConnected && (transcript || response) && (
        <div className="transcript">
          {transcript && <p className="user">You: {transcript}</p>}
          {response && <p className="assistant">Habari: {response}</p>}
        </div>
      )}

      <button
        className={`voice-btn ${status}`}
        onClick={toggle}
        disabled={disabled || status === 'connecting'}
      >
        {isConnected ? <StopIcon /> : <MicIcon />}
        <span>{isConnected ? t('End', 'Maliza') : t('Start', 'Anza')}</span>
      </button>

      <p className="status">{statusText[status] || statusText.idle}</p>

      {/* Quick booking hints */}
      {!isConnected && (
        <div className="hints">
          <p className="hint-title">{t('Try saying:', 'Jaribu kusema:')}</p>
          <ul>
            <li>"Book a passport appointment"</li>
            <li>"I need a driving license"</li>
            <li>"Apply for good conduct"</li>
          </ul>
        </div>
      )}

      {isConnected && (
        <div className="active-dot">
          <span className="dot" />
          {t('Active', 'Hai')}
        </div>
      )}
    </div>
  );
}

const MicIcon = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
    <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3zm5-3c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z" />
  </svg>
);

const StopIcon = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
    <rect x="6" y="6" width="12" height="12" rx="2" />
  </svg>
);

export default VoiceInterface;
