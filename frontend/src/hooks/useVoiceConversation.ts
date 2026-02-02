/**
 * useVoiceConversation Hook
 * Handles real-time voice conversation with speech recognition and TTS
 */

import { useState, useCallback, useRef, useEffect } from 'react';
import { voiceApi, ttsApi, sessionApi } from '../lib/api';

export type ConversationState = 'idle' | 'listening' | 'processing' | 'speaking' | 'error';

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  audioUrl?: string;
}

export interface UseVoiceConversationOptions {
  language?: string;
  autoSpeak?: boolean;
  onStateChange?: (state: ConversationState) => void;
  onMessage?: (message: Message) => void;
  onError?: (error: string) => void;
}

export function useVoiceConversation(options: UseVoiceConversationOptions = {}) {
  const {
    language = 'en-KE',
    autoSpeak = true,
    onStateChange,
    onMessage,
    onError,
  } = options;

  const [state, setState] = useState<ConversationState>('idle');
  const [messages, setMessages] = useState<Message[]>([]);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [audioLevel, setAudioLevel] = useState(0);

  // Refs
  const recognitionRef = useRef<SpeechRecognition | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const animationFrameRef = useRef<number | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);

  // Update state with callback
  const updateState = useCallback((newState: ConversationState) => {
    setState(newState);
    onStateChange?.(newState);
  }, [onStateChange]);

  // Add message to history
  const addMessage = useCallback((role: 'user' | 'assistant', content: string, audioUrl?: string) => {
    const message: Message = {
      id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      role,
      content,
      timestamp: new Date(),
      audioUrl,
    };
    setMessages(prev => [...prev, message]);
    onMessage?.(message);
    return message;
  }, [onMessage]);

  // Initialize session
  const initSession = useCallback(async () => {
    if (sessionId) return sessionId;
    
    try {
      const session = await sessionApi.create();
      setSessionId(session.session_id);
      return session.session_id;
    } catch (err) {
      console.error('Failed to create session:', err);
      onError?.('Failed to initialize conversation');
      return null;
    }
  }, [sessionId, onError]);

  // Play TTS audio
  const speak = useCallback(async (text: string): Promise<void> => {
    updateState('speaking');
    
    try {
      // Try ElevenLabs TTS first
      const ttsResponse = await ttsApi.textToSpeech({ text });
      
      if (ttsResponse.success && ttsResponse.audio_data) {
        const audioBlob = new Blob(
          [Uint8Array.from(atob(ttsResponse.audio_data), c => c.charCodeAt(0))],
          { type: ttsResponse.content_type || 'audio/mpeg' }
        );
        const audioUrl = URL.createObjectURL(audioBlob);
        
        return new Promise((resolve, reject) => {
          if (audioRef.current) {
            audioRef.current.pause();
            audioRef.current.src = '';
          }
          
          audioRef.current = new Audio(audioUrl);
          audioRef.current.onended = () => {
            URL.revokeObjectURL(audioUrl);
            updateState('idle');
            resolve();
          };
          audioRef.current.onerror = () => {
            URL.revokeObjectURL(audioUrl);
            // Fallback to browser TTS
            speakWithBrowser(text).then(resolve).catch(reject);
          };
          audioRef.current.play().catch(() => {
            speakWithBrowser(text).then(resolve).catch(reject);
          });
        });
      } else {
        return speakWithBrowser(text);
      }
    } catch (err) {
      console.error('TTS error, falling back to browser:', err);
      return speakWithBrowser(text);
    }
  }, [updateState]);

  // Browser TTS fallback
  const speakWithBrowser = useCallback((text: string): Promise<void> => {
    return new Promise((resolve) => {
      updateState('speaking');
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = language === 'sw-KE' ? 'sw-KE' : 'en-KE';
      utterance.rate = 0.9;
      utterance.pitch = 1;
      utterance.onend = () => {
        updateState('idle');
        resolve();
      };
      utterance.onerror = () => {
        updateState('idle');
        resolve();
      };
      speechSynthesis.speak(utterance);
    });
  }, [language, updateState]);

  // Stop speaking
  const stopSpeaking = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.src = '';
    }
    speechSynthesis.cancel();
    updateState('idle');
  }, [updateState]);

  // Process user input (text or voice)
  const processInput = useCallback(async (input: string) => {
    if (!input.trim()) return;

    // Add user message
    addMessage('user', input);
    updateState('processing');

    try {
      const currentSessionId = await initSession();
      if (!currentSessionId) {
        throw new Error('No session');
      }

      // Send to backend
      const response = await voiceApi.sendMessage(input, currentSessionId, language);

      // Add assistant response
      addMessage('assistant', response.text);

      // Speak the response
      if (autoSpeak && response.text) {
        await speak(response.text);
      } else {
        updateState('idle');
      }

      return response;
    } catch (err) {
      console.error('Processing error:', err);
      const errorMsg = 'Sorry, I had trouble processing that. Please try again.';
      addMessage('assistant', errorMsg);
      onError?.(errorMsg);
      updateState('error');
      
      // Reset to idle after a moment
      setTimeout(() => updateState('idle'), 2000);
    }
  }, [addMessage, autoSpeak, initSession, language, onError, speak, updateState]);

  // Start listening with Web Speech API
  const startListening = useCallback(() => {
    // Check browser support
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      onError?.('Speech recognition is not supported in this browser');
      return;
    }

    // Stop any current speech
    stopSpeaking();

    // Create recognition instance
    recognitionRef.current = new SpeechRecognition();
    recognitionRef.current.continuous = false;
    recognitionRef.current.interimResults = true;
    recognitionRef.current.lang = language === 'sw-KE' ? 'sw-KE' : 'en-KE';

    recognitionRef.current.onstart = () => {
      setIsListening(true);
      setTranscript('');
      updateState('listening');
      
      // Start audio level monitoring
      startAudioLevelMonitoring();
    };

    recognitionRef.current.onresult = (event: SpeechRecognitionEvent) => {
      let interimTranscript = '';
      let finalTranscript = '';

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const result = event.results[i];
        if (result.isFinal) {
          finalTranscript += result[0].transcript;
        } else {
          interimTranscript += result[0].transcript;
        }
      }

      setTranscript(finalTranscript || interimTranscript);

      // If we have a final result, process it
      if (finalTranscript) {
        processInput(finalTranscript);
      }
    };

    recognitionRef.current.onerror = (event: SpeechRecognitionErrorEvent) => {
      console.error('Speech recognition error:', event.error);
      setIsListening(false);
      stopAudioLevelMonitoring();
      
      if (event.error === 'no-speech') {
        updateState('idle');
      } else if (event.error === 'not-allowed') {
        onError?.('Microphone access denied. Please allow microphone access.');
        updateState('error');
      } else {
        onError?.(`Speech recognition error: ${event.error}`);
        updateState('error');
      }
    };

    recognitionRef.current.onend = () => {
      setIsListening(false);
      stopAudioLevelMonitoring();
      if (state === 'listening') {
        updateState('idle');
      }
    };

    recognitionRef.current.start();
  }, [language, onError, processInput, state, stopSpeaking, updateState]);

  // Stop listening
  const stopListening = useCallback(() => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
    }
    setIsListening(false);
    stopAudioLevelMonitoring();
  }, []);

  // Audio level monitoring
  const startAudioLevelMonitoring = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaStreamRef.current = stream;
      
      audioContextRef.current = new AudioContext();
      analyserRef.current = audioContextRef.current.createAnalyser();
      const source = audioContextRef.current.createMediaStreamSource(stream);
      source.connect(analyserRef.current);
      analyserRef.current.fftSize = 256;

      const updateLevel = () => {
        if (analyserRef.current && isListening) {
          const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount);
          analyserRef.current.getByteFrequencyData(dataArray);
          const average = dataArray.reduce((a, b) => a + b) / dataArray.length;
          setAudioLevel(average);
          animationFrameRef.current = requestAnimationFrame(updateLevel);
        }
      };
      updateLevel();
    } catch (err) {
      console.error('Audio monitoring error:', err);
    }
  }, [isListening]);

  const stopAudioLevelMonitoring = useCallback(() => {
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
    }
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach(track => track.stop());
    }
    if (audioContextRef.current) {
      audioContextRef.current.close();
    }
    setAudioLevel(0);
  }, []);

  // Toggle listening
  const toggleListening = useCallback(() => {
    if (isListening) {
      stopListening();
    } else {
      startListening();
    }
  }, [isListening, startListening, stopListening]);

  // Send text message
  const sendMessage = useCallback(async (text: string) => {
    return processInput(text);
  }, [processInput]);

  // Clear conversation
  const clearConversation = useCallback(async () => {
    setMessages([]);
    setTranscript('');
    stopSpeaking();
    stopListening();
    
    // Create new session
    try {
      const session = await sessionApi.create();
      setSessionId(session.session_id);
    } catch (err) {
      console.error('Failed to create new session:', err);
    }
    
    updateState('idle');
  }, [stopSpeaking, stopListening, updateState]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopSpeaking();
      stopListening();
      stopAudioLevelMonitoring();
    };
  }, [stopSpeaking, stopListening, stopAudioLevelMonitoring]);

  return {
    // State
    state,
    messages,
    isListening,
    transcript,
    audioLevel,
    sessionId,
    
    // Actions
    startListening,
    stopListening,
    toggleListening,
    sendMessage,
    speak,
    stopSpeaking,
    clearConversation,
    
    // Helpers
    isSpeaking: state === 'speaking',
    isProcessing: state === 'processing',
    isIdle: state === 'idle',
  };
}

// Type declarations for Web Speech API
interface SpeechRecognition extends EventTarget {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  start(): void;
  stop(): void;
  abort(): void;
  onstart: (() => void) | null;
  onresult: ((event: SpeechRecognitionEvent) => void) | null;
  onerror: ((event: SpeechRecognitionErrorEvent) => void) | null;
  onend: (() => void) | null;
}

interface SpeechRecognitionEvent {
  results: SpeechRecognitionResultList;
  resultIndex: number;
}

interface SpeechRecognitionErrorEvent {
  error: string;
  message: string;
}

interface SpeechRecognitionResultList {
  length: number;
  item(index: number): SpeechRecognitionResult;
  [index: number]: SpeechRecognitionResult;
}

interface SpeechRecognitionResult {
  length: number;
  item(index: number): SpeechRecognitionAlternative;
  [index: number]: SpeechRecognitionAlternative;
  isFinal: boolean;
}

interface SpeechRecognitionAlternative {
  transcript: string;
  confidence: number;
}

declare global {
  interface Window {
    SpeechRecognition: {
      new (): SpeechRecognition;
    };
    webkitSpeechRecognition: {
      new (): SpeechRecognition;
    };
  }
}

export default useVoiceConversation;
