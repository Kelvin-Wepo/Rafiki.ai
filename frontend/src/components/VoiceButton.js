/**
 * Voice Button Component
 * Large, accessible button for voice input with visual feedback
 */

import React, { useState, useEffect, useCallback } from 'react';
import { useAccessibility } from '../context/AccessibilityContext';
import { useSession } from '../context/SessionContext';
import voiceService from '../services/voiceService';
import api from '../services/api';
import toast from 'react-hot-toast';

function VoiceButton({ onResponse, disabled = false }) {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [interimTranscript, setInterimTranscript] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const { settings, announce, speak, stopSpeaking } = useAccessibility();
  const { sessionId, addMessage } = useSession();

  // Setup voice service callbacks
  useEffect(() => {
    voiceService.onStart = () => {
      setIsListening(true);
      announce('Listening... Speak now');
    };

    voiceService.onEnd = () => {
      setIsListening(false);
    };

    voiceService.onResult = ({ final, interim, isFinal }) => {
      if (isFinal && final) {
        setTranscript(final);
        setInterimTranscript('');
        handleVoiceInput(final);
      } else {
        setInterimTranscript(interim);
      }
    };

    voiceService.onError = (message) => {
      setIsListening(false);
      toast.error(message);
      announce(message);
    };

    return () => {
      voiceService.stopListening();
    };
  }, [announce, sessionId]);

  const handleVoiceInput = useCallback(async (text) => {
    if (!text.trim() || !sessionId) return;

    setIsProcessing(true);
    stopSpeaking();

    // Add user message to conversation
    addMessage({
      role: 'user',
      content: text,
      type: 'voice',
    });

    try {
      // Determine language code for API: sw-KE for Kiswahili, en-KE for English
      const languageCode = settings.language === 'sw' ? 'sw-KE' : 'en-KE';
      
      const response = await api.processVoiceInput({
        text_input: text,
        session_id: sessionId,
        input_mode: 'voice',
        language: languageCode,
      });

      // Add assistant response to conversation
      addMessage({
        role: 'assistant',
        content: response.text,
        intent: response.intent,
        entities: response.entities,
      });

      // Speak the response if voice is enabled
      if (settings.voiceEnabled && settings.autoSpeak) {
        speak(response.text);
      }

      // Notify parent component
      if (onResponse) {
        onResponse(response);
      }

      announce('Response received');
    } catch (error) {
      console.error('Error processing voice input:', error);
      toast.error('Failed to process your request. Please try again.');
      announce('Error processing request');
    } finally {
      setIsProcessing(false);
      setTranscript('');
    }
  }, [sessionId, addMessage, settings, speak, stopSpeaking, announce, onResponse]);

  const toggleListening = async () => {
    if (isListening) {
      voiceService.stopListening();
      setIsListening(false);
    } else {
      // Request permission first
      const hasPermission = await voiceService.requestMicrophonePermission();
      if (!hasPermission) {
        toast.error('Microphone access is required for voice input');
        announce('Microphone access denied');
        return;
      }

      // Stop any ongoing speech
      stopSpeaking();
      
      // Clear previous transcript
      setTranscript('');
      setInterimTranscript('');
      
      // Start listening with the correct language
      const languageCode = settings.language === 'sw' ? 'sw-KE' : 'en-KE';
      voiceService.startListening(languageCode);
    }
  };

  const handleKeyDown = (e) => {
    // Space or Enter to toggle
    if (e.key === ' ' || e.key === 'Enter') {
      e.preventDefault();
      toggleListening();
    }
    // Escape to stop
    if (e.key === 'Escape' && isListening) {
      voiceService.stopListening();
    }
  };

  const isVoiceSupported = voiceService.isSupported();

  if (!isVoiceSupported) {
    return (
      <div className="voice-not-supported" role="alert">
        <p>Voice input is not supported in your browser.</p>
        <p>Please use text input or try a different browser.</p>
      </div>
    );
  }

  return (
    <div className="voice-button-container">
      {/* Transcription Display */}
      {(transcript || interimTranscript) && (
        <div 
          className="transcription-display"
          role="status"
          aria-live="polite"
        >
          <span className="transcription-label">You said:</span>
          <p className={`transcription-text ${isListening ? 'listening' : ''}`}>
            {transcript || interimTranscript}
          </p>
        </div>
      )}

      {/* Voice Indicator */}
      {isListening && (
        <div 
          className={`voice-indicator listening`}
          role="status"
          aria-label="Listening"
        >
          <span className="voice-indicator-dot" />
          <span className="voice-indicator-dot" />
          <span className="voice-indicator-dot" />
          <span className="sr-only">Listening for voice input</span>
        </div>
      )}

      {/* Main Voice Button */}
      <button
        className={`btn btn-voice btn-primary ${isListening ? 'listening' : ''}`}
        onClick={toggleListening}
        onKeyDown={handleKeyDown}
        disabled={disabled || isProcessing}
        aria-label={isListening ? 'Stop listening' : 'Start voice input'}
        aria-pressed={isListening}
        title={isListening ? 'Click to stop listening' : 'Click to start speaking'}
      >
        {isProcessing ? (
          <span className="loading-spinner" aria-hidden="true" />
        ) : (
          <svg 
            width="32" 
            height="32" 
            viewBox="0 0 24 24" 
            fill="currentColor"
            aria-hidden="true"
          >
            {isListening ? (
              // Stop icon
              <path d="M6 6h12v12H6z"/>
            ) : (
              // Microphone icon
              <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3zm-1-9c0-.55.45-1 1-1s1 .45 1 1v6c0 .55-.45 1-1 1s-1-.45-1-1V5zm6 6c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/>
            )}
          </svg>
        )}
      </button>

      {/* Instructions */}
      <p 
        className="voice-instructions"
        id="voice-instructions"
        style={{ 
          textAlign: 'center', 
          marginTop: 'var(--spacing-md)',
          color: 'var(--color-text-secondary)'
        }}
      >
        {isListening 
          ? 'Listening... Speak clearly'
          : isProcessing 
          ? 'Processing your request...'
          : 'Press the button and speak your request'}
      </p>
    </div>
  );
}

export default VoiceButton;
