/**
 * ElevenLabs Context
 * Provides app-wide access to ElevenLabs voice functionality
 */

import React, { createContext, useContext, useState, useCallback, useEffect } from 'react';
import elevenLabsService from '../services/elevenLabsService';

const ElevenLabsContext = createContext(null);

export function ElevenLabsProvider({ children }) {
  // State
  const [isConnected, setIsConnected] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [status, setStatus] = useState('idle'); // idle, connecting, listening, speaking, error
  const [transcript, setTranscript] = useState('');
  const [response, setResponse] = useState('');
  const [error, setError] = useState(null);
  const [volume, setVolumeState] = useState(1.0);
  const [language, setLanguageState] = useState('en');

  // Setup callbacks
  useEffect(() => {
    elevenLabsService.onConnect = () => {
      setIsConnected(true);
      setStatus('listening');
      setError(null);
    };

    elevenLabsService.onDisconnect = () => {
      setIsConnected(false);
      setIsListening(false);
      setIsSpeaking(false);
      setStatus('idle');
    };

    elevenLabsService.onModeChange = (mode) => {
      setStatus(mode);
      setIsListening(mode === 'listening');
      setIsSpeaking(mode === 'speaking');
    };

    elevenLabsService.onUserTranscript = (text) => {
      setTranscript(text);
    };

    elevenLabsService.onAgentResponse = (text) => {
      setResponse(text);
    };

    elevenLabsService.onError = (err) => {
      setError(typeof err === 'string' ? err : err.message || 'Unknown error');
      setStatus('error');
    };

    return () => {
      elevenLabsService.onConnect = null;
      elevenLabsService.onDisconnect = null;
      elevenLabsService.onModeChange = null;
      elevenLabsService.onUserTranscript = null;
      elevenLabsService.onAgentResponse = null;
      elevenLabsService.onError = null;
    };
  }, []);

  // Start voice conversation
  const startConversation = useCallback(async () => {
    setStatus('connecting');
    setError(null);
    const success = await elevenLabsService.startConversation();
    if (!success) {
      setStatus('error');
      setError('Failed to connect to voice assistant');
    }
    return success;
  }, []);

  // End voice conversation
  const endConversation = useCallback(async () => {
    await elevenLabsService.endConversation();
    setIsConnected(false);
    setIsListening(false);
    setIsSpeaking(false);
    setStatus('idle');
    setTranscript('');
    setResponse('');
  }, []);

  // Toggle conversation
  const toggleConversation = useCallback(async () => {
    if (isConnected) {
      await endConversation();
    } else {
      await startConversation();
    }
  }, [isConnected, startConversation, endConversation]);

  // Speak text using TTS
  const speak = useCallback(async (text) => {
    if (!text) return false;
    setIsSpeaking(true);
    const success = await elevenLabsService.speak(text);
    setIsSpeaking(false);
    return success;
  }, []);

  // Set volume
  const setVolume = useCallback((vol) => {
    const clampedVol = Math.max(0, Math.min(1, vol));
    setVolumeState(clampedVol);
    elevenLabsService.setVolume(clampedVol);
  }, []);

  // Set language
  const setLanguage = useCallback((lang) => {
    setLanguageState(lang);
    elevenLabsService.setLanguage(lang);
  }, []);

  // Clear error
  const clearError = useCallback(() => {
    setError(null);
    if (status === 'error') {
      setStatus('idle');
    }
  }, [status]);

  const value = {
    // State
    isConnected,
    isListening,
    isSpeaking,
    status,
    transcript,
    response,
    error,
    volume,
    language,
    
    // Actions
    startConversation,
    endConversation,
    toggleConversation,
    speak,
    setVolume,
    setLanguage,
    clearError,
    
    // Service access (for advanced usage)
    service: elevenLabsService
  };

  return (
    <ElevenLabsContext.Provider value={value}>
      {children}
    </ElevenLabsContext.Provider>
  );
}

export function useElevenLabs() {
  const context = useContext(ElevenLabsContext);
  if (!context) {
    throw new Error('useElevenLabs must be used within an ElevenLabsProvider');
  }
  return context;
}

export default ElevenLabsContext;
