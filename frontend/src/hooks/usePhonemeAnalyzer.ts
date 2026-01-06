/**
 * Advanced Phoneme Analysis Hook
 * More accurate lip-sync using frequency band analysis and phoneme detection
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import type { Viseme } from '../types/avatar.types';

interface PhonemeAnalysis {
  viseme: Viseme;
  intensity: number;
  confidence: number;
  formants: {
    f1: number; // First formant (mouth openness)
    f2: number; // Second formant (tongue position)
  };
}

interface UsePhonemeAnalyzerOptions {
  fftSize?: number;
  smoothingFactor?: number;
}

// Phoneme to viseme mapping based on linguistic research
// Reserved for future phoneme detection integration
// eslint-disable-next-line @typescript-eslint/no-unused-vars
export const PHONEME_VISEME_MAP: Record<string, Viseme> = {
  // Vowels
  'a': 'aa',   // father
  'æ': 'aa',   // cat
  'ɑ': 'aa',   // hot
  'e': 'ee',   // bed
  'i': 'ee',   // see
  'ɪ': 'ee',   // sit
  'o': 'oh',   // go
  'ɔ': 'oh',   // caught
  'u': 'oo',   // too
  'ʊ': 'oo',   // put
  'ə': 'neutral', // about
  
  // Consonants
  'p': 'consonant',
  'b': 'consonant',
  'm': 'consonant',
  't': 'consonant',
  'd': 'consonant',
  'n': 'consonant',
  'k': 'consonant',
  'g': 'consonant',
  'θ': 'th',
  'ð': 'th',
  'f': 'ff',
  'v': 'ff',
  's': 'consonant',
  'z': 'consonant',
  'ʃ': 'consonant',
  'ʒ': 'consonant',
};

// Frequency ranges for formant analysis (in Hz)
const FORMANT_RANGES = {
  f1: { min: 200, max: 900 },   // First formant
  f2: { min: 800, max: 2500 },  // Second formant
  f3: { min: 1800, max: 3500 }, // Third formant (for consonants)
};

export const usePhonemeAnalyzer = (options: UsePhonemeAnalyzerOptions = {}) => {
  const { fftSize = 2048, smoothingFactor = 0.7 } = options;

  const [phonemeData, setPhonemeData] = useState<PhonemeAnalysis>({
    viseme: 'neutral',
    intensity: 0,
    confidence: 0,
    formants: { f1: 0, f2: 0 }
  });

  const audioContextRef = useRef<AudioContext | null>(null);
  const analyzerRef = useRef<AnalyserNode | null>(null);
  const smoothedDataRef = useRef<PhonemeAnalysis>({
    viseme: 'neutral',
    intensity: 0,
    confidence: 0,
    formants: { f1: 0, f2: 0 }
  });

  // Extract formants from frequency data
  const extractFormants = useCallback((frequencyData: Uint8Array, sampleRate: number) => {
    const binCount = frequencyData.length;
    const nyquist = sampleRate / 2;
    const binWidth = nyquist / binCount;

    // Find peaks in formant ranges
    const findPeak = (minFreq: number, maxFreq: number): number => {
      const minBin = Math.floor(minFreq / binWidth);
      const maxBin = Math.min(Math.ceil(maxFreq / binWidth), binCount - 1);
      
      let maxValue = 0;
      let maxIndex = minBin;
      
      for (let i = minBin; i <= maxBin; i++) {
        if (frequencyData[i] > maxValue) {
          maxValue = frequencyData[i];
          maxIndex = i;
        }
      }
      
      return maxIndex * binWidth;
    };

    return {
      f1: findPeak(FORMANT_RANGES.f1.min, FORMANT_RANGES.f1.max),
      f2: findPeak(FORMANT_RANGES.f2.min, FORMANT_RANGES.f2.max)
    };
  }, []);

  // Map formants to viseme
  const formantToViseme = useCallback((f1: number, f2: number, intensity: number): Viseme => {
    if (intensity < 0.1) return 'neutral';

    // Vowel classification based on formant values
    // High F1 = open mouth, Low F1 = closed mouth
    // High F2 = front vowel, Low F2 = back vowel
    
    const normalizedF1 = (f1 - FORMANT_RANGES.f1.min) / (FORMANT_RANGES.f1.max - FORMANT_RANGES.f1.min);
    const normalizedF2 = (f2 - FORMANT_RANGES.f2.min) / (FORMANT_RANGES.f2.max - FORMANT_RANGES.f2.min);

    // Open vowels (high F1)
    if (normalizedF1 > 0.6) {
      return 'aa';
    }
    
    // Front vowels (high F2)
    if (normalizedF2 > 0.6) {
      return 'ee';
    }
    
    // Back rounded vowels (low F2)
    if (normalizedF2 < 0.3) {
      if (normalizedF1 > 0.4) {
        return 'oh';
      }
      return 'oo';
    }
    
    // Mid vowels
    if (normalizedF1 > 0.3 && normalizedF1 < 0.6) {
      if (normalizedF2 > 0.4) {
        return 'ee';
      }
      return 'oh';
    }

    // Consonants (low intensity with specific patterns)
    if (intensity < 0.3) {
      if (f2 > 2000) return 'consonant';
      if (f2 < 1000) return 'ff';
      return 'th';
    }

    return 'neutral';
  }, []);

  // Smooth transition between visemes
  const smoothViseme = useCallback((current: PhonemeAnalysis, target: PhonemeAnalysis): PhonemeAnalysis => {
    const lerp = (a: number, b: number, t: number) => a + (b - a) * t;
    
    return {
      viseme: target.intensity > 0.15 ? target.viseme : current.viseme,
      intensity: lerp(current.intensity, target.intensity, 1 - smoothingFactor),
      confidence: lerp(current.confidence, target.confidence, 1 - smoothingFactor),
      formants: {
        f1: lerp(current.formants.f1, target.formants.f1, 1 - smoothingFactor),
        f2: lerp(current.formants.f2, target.formants.f2, 1 - smoothingFactor)
      }
    };
  }, [smoothingFactor]);

  // Analyze audio buffer
  const analyzeBuffer = useCallback((analyzerNode: AnalyserNode) => {
    const frequencyData = new Uint8Array(analyzerNode.frequencyBinCount);
    analyzerNode.getByteFrequencyData(frequencyData);

    const sampleRate = audioContextRef.current?.sampleRate ?? 44100;
    
    // Calculate RMS for intensity
    let sum = 0;
    for (let i = 0; i < frequencyData.length; i++) {
      sum += frequencyData[i] * frequencyData[i];
    }
    const rms = Math.sqrt(sum / frequencyData.length);
    const intensity = Math.min(1, rms / 128);

    // Extract formants
    const formants = extractFormants(frequencyData, sampleRate);
    
    // Map to viseme
    const viseme = formantToViseme(formants.f1, formants.f2, intensity);
    
    // Calculate confidence based on formant clarity
    const confidence = intensity > 0.1 ? Math.min(1, intensity * 2) : 0;

    const targetData: PhonemeAnalysis = {
      viseme,
      intensity,
      confidence,
      formants
    };

    // Smooth the transition
    smoothedDataRef.current = smoothViseme(smoothedDataRef.current, targetData);
    setPhonemeData(smoothedDataRef.current);

    return smoothedDataRef.current;
  }, [extractFormants, formantToViseme, smoothViseme]);

  // Initialize audio context and analyzer
  const initAnalyzer = useCallback(() => {
    if (!audioContextRef.current) {
      audioContextRef.current = new (window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext)();
    }

    analyzerRef.current = audioContextRef.current.createAnalyser();
    analyzerRef.current.fftSize = fftSize;
    analyzerRef.current.smoothingTimeConstant = 0.5;

    return analyzerRef.current;
  }, [fftSize]);

  // Connect to audio source
  const connectSource = useCallback((source: MediaStreamAudioSourceNode | MediaElementAudioSourceNode) => {
    if (analyzerRef.current) {
      source.connect(analyzerRef.current);
    }
  }, []);

  // Reset to neutral
  const reset = useCallback(() => {
    smoothedDataRef.current = {
      viseme: 'neutral',
      intensity: 0,
      confidence: 0,
      formants: { f1: 0, f2: 0 }
    };
    setPhonemeData(smoothedDataRef.current);
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (audioContextRef.current?.state !== 'closed') {
        audioContextRef.current?.close();
      }
    };
  }, []);

  return {
    phonemeData,
    initAnalyzer,
    connectSource,
    analyzeBuffer,
    reset,
    audioContext: audioContextRef.current,
    analyzer: analyzerRef.current
  };
};

export default usePhonemeAnalyzer;
