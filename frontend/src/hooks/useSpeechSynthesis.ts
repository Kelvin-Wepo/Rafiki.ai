/**
 * Speech Synthesis Hook
 * Text-to-Speech with lip-sync timing markers
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import type { Viseme, AudioAnalysis } from '../types/avatar.types';

interface SpeechOptions {
  voice?: SpeechSynthesisVoice;
  rate?: number;
  pitch?: number;
  volume?: number;
}

interface WordTiming {
  word: string;
  startTime: number;
  endTime: number;
  visemes: Viseme[];
}

interface UseSpeechSynthesisReturn {
  speak: (text: string, options?: SpeechOptions) => Promise<void>;
  stop: () => void;
  pause: () => void;
  resume: () => void;
  isSpeaking: boolean;
  isPaused: boolean;
  currentWord: string;
  audioData: AudioAnalysis;
  voices: SpeechSynthesisVoice[];
  selectedVoice: SpeechSynthesisVoice | null;
  setVoice: (voice: SpeechSynthesisVoice) => void;
}

// Phoneme to viseme mapping for English
// Reserved for enhanced phoneme detection
// eslint-disable-next-line @typescript-eslint/no-unused-vars
export const PHONEME_TO_VISEME: Record<string, Viseme> = {
  // Vowels
  'a': 'aa', 'e': 'ee', 'i': 'ee', 'o': 'oh', 'u': 'oo',
  'aa': 'aa', 'ae': 'aa', 'ah': 'aa', 'ao': 'oh', 'aw': 'aa',
  'ay': 'aa', 'eh': 'ee', 'er': 'ee', 'ey': 'ee', 'ih': 'ee',
  'iy': 'ee', 'ow': 'oh', 'oy': 'oh', 'uh': 'oo', 'uw': 'oo',
  
  // Consonants
  'b': 'consonant', 'ch': 'consonant', 'd': 'consonant',
  'dh': 'th', 'f': 'ff', 'g': 'consonant', 'hh': 'consonant',
  'jh': 'consonant', 'k': 'consonant', 'l': 'consonant',
  'm': 'consonant', 'n': 'consonant', 'ng': 'consonant',
  'p': 'consonant', 'r': 'consonant', 's': 'consonant',
  'sh': 'consonant', 't': 'consonant', 'th': 'th',
  'v': 'ff', 'w': 'oo', 'y': 'ee', 'z': 'consonant',
  'zh': 'consonant'
};

// Simple letter-to-viseme for basic lip-sync
const letterToViseme = (letter: string): Viseme => {
  const lower = letter.toLowerCase();
  
  // Vowels
  if ('aàáâãäå'.includes(lower)) return 'aa';
  if ('eèéêë'.includes(lower)) return 'ee';
  if ('iìíîï'.includes(lower)) return 'ee';
  if ('oòóôõö'.includes(lower)) return 'oh';
  if ('uùúûü'.includes(lower)) return 'oo';
  
  // Consonants
  if ('mbp'.includes(lower)) return 'consonant';
  if ('fv'.includes(lower)) return 'ff';
  if ('sz'.includes(lower)) return 'consonant';
  if ('td'.includes(lower)) return 'consonant';
  if ('kg'.includes(lower)) return 'consonant';
  if ('lr'.includes(lower)) return 'consonant';
  if ('w'.includes(lower)) return 'oo';
  if ('y'.includes(lower)) return 'ee';
  
  return 'neutral';
};

// Generate viseme sequence for a word
const wordToVisemes = (word: string): Viseme[] => {
  const visemes: Viseme[] = [];
  const letters = word.split('');
  
  for (let i = 0; i < letters.length; i++) {
    const letter = letters[i];
    
    // Skip non-alphabetic characters
    if (!/[a-zA-Z]/.test(letter)) continue;
    
    // Check for digraphs
    if (i < letters.length - 1) {
      const digraph = (letter + letters[i + 1]).toLowerCase();
      if (['th', 'sh', 'ch', 'wh', 'ph'].includes(digraph)) {
        if (digraph === 'th') visemes.push('th');
        else if (digraph === 'sh' || digraph === 'ch') visemes.push('consonant');
        else if (digraph === 'wh') visemes.push('oo');
        else if (digraph === 'ph') visemes.push('ff');
        i++; // Skip next letter
        continue;
      }
    }
    
    visemes.push(letterToViseme(letter));
  }
  
  return visemes.length > 0 ? visemes : ['neutral'];
};

export const useSpeechSynthesis = (): UseSpeechSynthesisReturn => {
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [currentWord, setCurrentWord] = useState('');
  const [voices, setVoices] = useState<SpeechSynthesisVoice[]>([]);
  const [selectedVoice, setSelectedVoice] = useState<SpeechSynthesisVoice | null>(null);
  const [audioData, setAudioData] = useState<AudioAnalysis>({
    amplitude: 0,
    frequency: 0,
    isSpeaking: false,
    viseme: 'neutral'
  });

  const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null);
  const wordTimingsRef = useRef<WordTiming[]>([]);
  const currentWordIndexRef = useRef(0);
  const visemeIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const currentVisemeIndexRef = useRef(0);

  // Load available voices
  useEffect(() => {
    const loadVoices = () => {
      const availableVoices = speechSynthesis.getVoices();
      setVoices(availableVoices);
      
      // Try to find a suitable voice (prefer female English voice)
      const preferredVoice = availableVoices.find(v => 
        v.lang.startsWith('en') && 
        (v.name.toLowerCase().includes('female') || 
         v.name.toLowerCase().includes('woman') ||
         v.name.toLowerCase().includes('samantha') ||
         v.name.toLowerCase().includes('victoria'))
      ) || availableVoices.find(v => v.lang.startsWith('en')) || availableVoices[0];
      
      if (preferredVoice && !selectedVoice) {
        setSelectedVoice(preferredVoice);
      }
    };

    loadVoices();
    speechSynthesis.onvoiceschanged = loadVoices;

    return () => {
      speechSynthesis.onvoiceschanged = null;
    };
  }, [selectedVoice]);

  // Animate visemes for current word
  const animateWordVisemes = useCallback((visemes: Viseme[], duration: number) => {
    if (visemeIntervalRef.current) {
      clearInterval(visemeIntervalRef.current);
    }

    currentVisemeIndexRef.current = 0;
    const visemeTime = duration / visemes.length;

    const updateViseme = () => {
      if (currentVisemeIndexRef.current < visemes.length) {
        const viseme = visemes[currentVisemeIndexRef.current];
        setAudioData({
          amplitude: 0.5 + Math.random() * 0.3,
          frequency: 200 + Math.random() * 600,
          isSpeaking: true,
          viseme
        });
        currentVisemeIndexRef.current++;
      }
    };

    // Initial viseme
    updateViseme();

    // Set up interval for remaining visemes
    if (visemes.length > 1) {
      visemeIntervalRef.current = setInterval(updateViseme, visemeTime);
      
      // Clean up after word is done
      setTimeout(() => {
        if (visemeIntervalRef.current) {
          clearInterval(visemeIntervalRef.current);
        }
      }, duration);
    }
  }, []);

  // Speak text
  const speak = useCallback(async (text: string, options: SpeechOptions = {}) => {
    return new Promise<void>((resolve, reject) => {
      if (!('speechSynthesis' in window)) {
        reject(new Error('Speech synthesis not supported'));
        return;
      }

      // Cancel any ongoing speech
      speechSynthesis.cancel();

      const utterance = new SpeechSynthesisUtterance(text);
      utteranceRef.current = utterance;

      // Set voice and options
      utterance.voice = options.voice || selectedVoice;
      utterance.rate = options.rate ?? 1;
      utterance.pitch = options.pitch ?? 1;
      utterance.volume = options.volume ?? 1;

      // Pre-calculate word timings and visemes
      const words = text.split(/\s+/).filter(w => w.length > 0);
      const avgWordDuration = 200 / utterance.rate; // ms per word
      
      wordTimingsRef.current = words.map((word, index) => ({
        word,
        startTime: index * avgWordDuration,
        endTime: (index + 1) * avgWordDuration,
        visemes: wordToVisemes(word)
      }));
      currentWordIndexRef.current = 0;

      // Event handlers
      utterance.onstart = () => {
        setIsSpeaking(true);
        setIsPaused(false);
        setAudioData(prev => ({ ...prev, isSpeaking: true }));
      };

      utterance.onboundary = (event) => {
        if (event.name === 'word') {
          const wordTiming = wordTimingsRef.current[currentWordIndexRef.current];
          if (wordTiming) {
            setCurrentWord(wordTiming.word);
            animateWordVisemes(wordTiming.visemes, avgWordDuration);
            currentWordIndexRef.current++;
          }
        }
      };

      utterance.onpause = () => {
        setIsPaused(true);
      };

      utterance.onresume = () => {
        setIsPaused(false);
      };

      utterance.onend = () => {
        setIsSpeaking(false);
        setIsPaused(false);
        setCurrentWord('');
        setAudioData({
          amplitude: 0,
          frequency: 0,
          isSpeaking: false,
          viseme: 'neutral'
        });
        if (visemeIntervalRef.current) {
          clearInterval(visemeIntervalRef.current);
        }
        resolve();
      };

      utterance.onerror = (event) => {
        setIsSpeaking(false);
        setIsPaused(false);
        setCurrentWord('');
        setAudioData({
          amplitude: 0,
          frequency: 0,
          isSpeaking: false,
          viseme: 'neutral'
        });
        reject(new Error(event.error));
      };

      // Start speaking
      speechSynthesis.speak(utterance);
    });
  }, [selectedVoice, animateWordVisemes]);

  // Stop speaking
  const stop = useCallback(() => {
    speechSynthesis.cancel();
    setIsSpeaking(false);
    setIsPaused(false);
    setCurrentWord('');
    setAudioData({
      amplitude: 0,
      frequency: 0,
      isSpeaking: false,
      viseme: 'neutral'
    });
    if (visemeIntervalRef.current) {
      clearInterval(visemeIntervalRef.current);
    }
  }, []);

  // Pause speaking
  const pause = useCallback(() => {
    speechSynthesis.pause();
  }, []);

  // Resume speaking
  const resume = useCallback(() => {
    speechSynthesis.resume();
  }, []);

  // Set voice
  const setVoice = useCallback((voice: SpeechSynthesisVoice) => {
    setSelectedVoice(voice);
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      speechSynthesis.cancel();
      if (visemeIntervalRef.current) {
        clearInterval(visemeIntervalRef.current);
      }
    };
  }, []);

  return {
    speak,
    stop,
    pause,
    resume,
    isSpeaking,
    isPaused,
    currentWord,
    audioData,
    voices,
    selectedVoice,
    setVoice
  };
};

export default useSpeechSynthesis;
