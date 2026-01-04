/**
 * Accessibility Context
 * Manages accessibility preferences across the application
 */

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';

const AccessibilityContext = createContext(null);

// Default accessibility settings
const defaultSettings = {
  highContrast: false,
  largeText: false,
  reducedMotion: false,
  screenReaderMode: false,
  speechRate: 80, // 0.8x speed (80/100) - 20% slower than normal
  speechPitch: 1.0,
  voiceEnabled: true,
  autoSpeak: true,
  language: 'en', // 'en' for English, 'sw' for Kiswahili
};

export function AccessibilityProvider({ children }) {
  const [settings, setSettings] = useState(() => {
    // Load settings from localStorage
    const saved = localStorage.getItem('accessibilitySettings');
    if (saved) {
      try {
        return { ...defaultSettings, ...JSON.parse(saved) };
      } catch (e) {
        console.error('Failed to parse accessibility settings:', e);
      }
    }
    return defaultSettings;
  });

  // Check system preferences on mount
  useEffect(() => {
    // Check for reduced motion preference
    const motionQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    if (motionQuery.matches) {
      setSettings(prev => ({ ...prev, reducedMotion: true }));
    }

    // Check for high contrast preference
    const contrastQuery = window.matchMedia('(prefers-contrast: more)');
    if (contrastQuery.matches) {
      setSettings(prev => ({ ...prev, highContrast: true }));
    }
  }, []);

  // Apply settings to document
  useEffect(() => {
    document.documentElement.setAttribute('data-high-contrast', settings.highContrast);
    document.documentElement.setAttribute('data-large-text', settings.largeText);
    document.documentElement.setAttribute('data-reduced-motion', settings.reducedMotion);

    // Save to localStorage
    localStorage.setItem('accessibilitySettings', JSON.stringify(settings));
  }, [settings]);

  const updateSetting = useCallback((key, value) => {
    setSettings(prev => ({ ...prev, [key]: value }));
  }, []);

  const toggleSetting = useCallback((key) => {
    setSettings(prev => ({ ...prev, [key]: !prev[key] }));
  }, []);

  const resetSettings = useCallback(() => {
    setSettings(defaultSettings);
    localStorage.removeItem('accessibilitySettings');
  }, []);

  // Announce message to screen readers
  const announce = useCallback((message, priority = 'polite') => {
    const announcer = document.getElementById('announcements');
    if (announcer) {
      announcer.setAttribute('aria-live', priority);
      announcer.textContent = message;
      
      // Clear after announcement
      setTimeout(() => {
        announcer.textContent = '';
      }, 1000);
    }
  }, []);

  // Speak text using Web Speech API with natural pacing
  const speak = useCallback((text, options = {}) => {
    if (!settings.voiceEnabled || !window.speechSynthesis) return;

    // Cancel any ongoing speech
    window.speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    
    // Speech rate: 0.8 = 20% slower than normal (1.0)
    // Using settings.speechRate / 100 so 80 becomes 0.8
    utterance.rate = (options.rate || settings.speechRate) / 100;
    
    // Natural pitch
    utterance.pitch = options.pitch || settings.speechPitch || 1.0;
    utterance.volume = options.volume || 1;
    
    // Set language based on user preference
    const langCode = options.lang || (settings.language === 'sw' ? 'sw-KE' : 'en-KE');
    utterance.lang = langCode;
    
    // Try to select a natural-sounding voice
    const voices = window.speechSynthesis.getVoices();
    const preferredVoice = voices.find(voice => 
      voice.lang.startsWith(settings.language === 'sw' ? 'sw' : 'en') && 
      (voice.name.includes('Neural') || voice.name.includes('Natural') || voice.name.includes('Google'))
    ) || voices.find(voice => voice.lang.startsWith(settings.language === 'sw' ? 'sw' : 'en'));
    
    if (preferredVoice) {
      utterance.voice = preferredVoice;
    }

    window.speechSynthesis.speak(utterance);
  }, [settings.voiceEnabled, settings.speechRate, settings.speechPitch, settings.language]);

  // Stop speaking
  const stopSpeaking = useCallback(() => {
    if (window.speechSynthesis) {
      window.speechSynthesis.cancel();
    }
  }, []);

  const value = {
    settings,
    updateSetting,
    toggleSetting,
    resetSettings,
    announce,
    speak,
    stopSpeaking,
  };

  return (
    <AccessibilityContext.Provider value={value}>
      {children}
    </AccessibilityContext.Provider>
  );
}

export function useAccessibility() {
  const context = useContext(AccessibilityContext);
  if (!context) {
    throw new Error('useAccessibility must be used within AccessibilityProvider');
  }
  return context;
}

export default AccessibilityContext;
