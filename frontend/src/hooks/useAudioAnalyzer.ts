/**
 * Web Audio API Hook for Real-time Audio Analysis
 * Provides audio data for lip-sync and voice activity detection
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import type { AudioAnalysis, Viseme } from '../types/avatar.types';

interface UseAudioAnalyzerOptions {
  fftSize?: number;
  smoothingTimeConstant?: number;
  minDecibels?: number;
  maxDecibels?: number;
}

interface UseAudioAnalyzerReturn {
  audioData: AudioAnalysis;
  isActive: boolean;
  startAnalyzing: (stream?: MediaStream) => Promise<void>;
  stopAnalyzing: () => void;
  analyzeAudioElement: (audioElement: HTMLAudioElement) => void;
}

// Map frequency/amplitude to viseme
const getVisemeFromAudio = (amplitude: number, frequency: number): Viseme => {
  if (amplitude < 0.1) return 'neutral';
  
  // Simplified viseme mapping based on frequency bands
  if (frequency < 300) return 'oo';
  if (frequency < 500) return 'oh';
  if (frequency < 800) return 'aa';
  if (frequency < 1200) return 'ee';
  if (frequency < 2000) return 'consonant';
  if (frequency < 3000) return 'ff';
  return 'th';
};

export const useAudioAnalyzer = (
  options: UseAudioAnalyzerOptions = {}
): UseAudioAnalyzerReturn => {
  const {
    fftSize = 256,
    smoothingTimeConstant = 0.8,
    minDecibels = -90,
    maxDecibels = -10
  } = options;

  const [audioData, setAudioData] = useState<AudioAnalysis>({
    amplitude: 0,
    frequency: 0,
    isSpeaking: false,
    viseme: 'neutral'
  });
  const [isActive, setIsActive] = useState(false);

  const audioContextRef = useRef<AudioContext | null>(null);
  const analyzerRef = useRef<AnalyserNode | null>(null);
  const sourceRef = useRef<MediaStreamAudioSourceNode | MediaElementAudioSourceNode | null>(null);
  const animationFrameRef = useRef<number>(0);
  const dataArrayRef = useRef<Uint8Array<ArrayBuffer> | null>(null);

  const analyze = useCallback(() => {
    if (!analyzerRef.current || !dataArrayRef.current) return;

    const analyzer = analyzerRef.current;
    const dataArray = dataArrayRef.current;
    
    // Get frequency data
    analyzer.getByteFrequencyData(dataArray);

    // Calculate amplitude (RMS of frequency data)
    let sum = 0;
    let maxIndex = 0;
    let maxValue = 0;
    
    for (let i = 0; i < dataArray.length; i++) {
      const value = dataArray[i];
      sum += value * value;
      if (value > maxValue) {
        maxValue = value;
        maxIndex = i;
      }
    }
    
    const rms = Math.sqrt(sum / dataArray.length);
    const amplitude = Math.min(1, rms / 128);
    
    // Calculate dominant frequency
    const nyquist = audioContextRef.current!.sampleRate / 2;
    const frequency = (maxIndex / dataArray.length) * nyquist;
    
    // Voice activity detection
    const isSpeaking = amplitude > 0.15;
    
    // Get viseme
    const viseme = getVisemeFromAudio(amplitude, frequency);

    setAudioData({
      amplitude,
      frequency,
      isSpeaking,
      viseme
    });

    animationFrameRef.current = requestAnimationFrame(analyze);
  }, []);

  const initializeAnalyzer = useCallback(() => {
    if (!audioContextRef.current) {
      audioContextRef.current = new (window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext)();
    }

    const audioContext = audioContextRef.current;
    analyzerRef.current = audioContext.createAnalyser();
    analyzerRef.current.fftSize = fftSize;
    analyzerRef.current.smoothingTimeConstant = smoothingTimeConstant;
    analyzerRef.current.minDecibels = minDecibels;
    analyzerRef.current.maxDecibels = maxDecibels;

    dataArrayRef.current = new Uint8Array(analyzerRef.current.frequencyBinCount);
  }, [fftSize, smoothingTimeConstant, minDecibels, maxDecibels]);

  const startAnalyzing = useCallback(async (stream?: MediaStream) => {
    try {
      initializeAnalyzer();
      
      const audioContext = audioContextRef.current!;
      const analyzer = analyzerRef.current!;

      // Resume audio context if suspended
      if (audioContext.state === 'suspended') {
        await audioContext.resume();
      }

      // Get or use provided media stream
      const mediaStream = stream || await navigator.mediaDevices.getUserMedia({ audio: true });
      sourceRef.current = audioContext.createMediaStreamSource(mediaStream);
      sourceRef.current.connect(analyzer);

      setIsActive(true);
      analyze();
    } catch (error) {
      console.error('Failed to start audio analysis:', error);
    }
  }, [initializeAnalyzer, analyze]);

  const analyzeAudioElement = useCallback((audioElement: HTMLAudioElement) => {
    try {
      initializeAnalyzer();
      
      const audioContext = audioContextRef.current!;
      const analyzer = analyzerRef.current!;

      // Create source from audio element
      sourceRef.current = audioContext.createMediaElementSource(audioElement);
      sourceRef.current.connect(analyzer);
      analyzer.connect(audioContext.destination);

      setIsActive(true);
      analyze();
    } catch (error) {
      console.error('Failed to analyze audio element:', error);
    }
  }, [initializeAnalyzer, analyze]);

  const stopAnalyzing = useCallback(() => {
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
    }

    if (sourceRef.current) {
      sourceRef.current.disconnect();
      sourceRef.current = null;
    }

    setIsActive(false);
    setAudioData({
      amplitude: 0,
      frequency: 0,
      isSpeaking: false,
      viseme: 'neutral'
    });
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopAnalyzing();
      if (audioContextRef.current) {
        audioContextRef.current.close();
      }
    };
  }, [stopAnalyzing]);

  return {
    audioData,
    isActive,
    startAnalyzing,
    stopAnalyzing,
    analyzeAudioElement
  };
};

export default useAudioAnalyzer;
