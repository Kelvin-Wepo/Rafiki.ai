/**
 * Hooks Index Export
 * All animation and interaction hooks for Rafiki Avatar
 */

// Core animation hooks
export { useAudioAnalyzer } from './useAudioAnalyzer';
export { useBlinking } from './useBlinking';
export { useMicroMovements } from './useMicroMovements';

// Enhanced animation hooks
export { useBreathing } from './useBreathing';
export { useEyeTracking } from './useEyeTracking';
export { useEmotions, type Emotion, type FacialExpression } from './useEmotions';
export { usePhonemeAnalyzer } from './usePhonemeAnalyzer';
export { useSpeechSynthesis } from './useSpeechSynthesis';

// SadTalker integration for realistic lip-sync
export { 
  useSadTalker, 
  type SadTalkerJob, 
  type SadTalkerOptions,
  type Avatar,
  type AnimationSettings 
} from './useSadTalker';
