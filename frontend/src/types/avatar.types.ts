/**
 * Rafiki Avatar Type Definitions
 * Government AI Voice Assistant Avatar System
 */

// Animation states for the avatar
export type AvatarState = 'idle' | 'listening' | 'thinking' | 'speaking' | 'error';

// Mouth viseme shapes for lip-sync (mapped to phonemes)
export type Viseme = 
  | 'neutral'    // Closed/rest
  | 'aa'         // Open vowels (a, ah)
  | 'ee'         // Front vowels (e, i)
  | 'oo'         // Rounded vowels (o, u)
  | 'oh'         // Mid-open (oh)
  | 'consonant'  // Consonant shapes (m, b, p)
  | 'th'         // Dental (th)
  | 'ff'         // Labio-dental (f, v)
  | 'smile';     // Happy expression

// Eye states
export type EyeState = 'open' | 'half' | 'closed' | 'squint';

// Audio analysis data from Web Audio API
export interface AudioAnalysis {
  amplitude: number;      // 0-1 volume level
  frequency: number;      // Dominant frequency
  isSpeaking: boolean;    // Voice activity detection
  viseme: Viseme;         // Estimated mouth shape
}

// Avatar component props
export interface RafikiAvatarProps {
  state: AvatarState;
  audioData?: AudioAnalysis;
  size?: number | string;
  className?: string;
  onStateChange?: (state: AvatarState) => void;
  accessible?: boolean;
}

// Eye component props
export interface EyeProps {
  state: EyeState;
  position: 'left' | 'right';
  lookDirection?: { x: number; y: number };
  glowColor?: string;
  pupilDilation?: number;
  expressionSquint?: number;
}

// Mouth component props
export interface MouthProps {
  viseme: Viseme;
  intensity?: number; // 0-1 how open the mouth is
  state: AvatarState;
  smileIntensity?: number; // -1 (frown) to 1 (smile)
  lipCornerPull?: number; // -1 to 1
}

// Animation configuration
export interface AnimationConfig {
  blinkInterval: { min: number; max: number }; // milliseconds
  blinkDuration: number;
  microMovementIntensity: number;
  transitionDuration: number;
}

// Glow overlay configuration
export interface GlowConfig {
  color: string;
  intensity: number;
  pulseSpeed: number;
  blur: number;
}

// State-specific configurations
export const STATE_CONFIGS: Record<AvatarState, { 
  glow: GlowConfig; 
  animation: Partial<AnimationConfig>;
  ariaLabel: string;
}> = {
  idle: {
    glow: { color: 'rgba(34, 139, 34, 0.3)', intensity: 0.3, pulseSpeed: 4000, blur: 20 },
    animation: { microMovementIntensity: 0.2 },
    ariaLabel: 'Rafiki is idle and ready to assist'
  },
  listening: {
    glow: { color: 'rgba(65, 105, 225, 0.5)', intensity: 0.6, pulseSpeed: 1500, blur: 25 },
    animation: { microMovementIntensity: 0.4 },
    ariaLabel: 'Rafiki is listening to you'
  },
  thinking: {
    glow: { color: 'rgba(255, 215, 0, 0.4)', intensity: 0.5, pulseSpeed: 800, blur: 30 },
    animation: { microMovementIntensity: 0.3 },
    ariaLabel: 'Rafiki is processing your request'
  },
  speaking: {
    glow: { color: 'rgba(220, 20, 60, 0.4)', intensity: 0.5, pulseSpeed: 2000, blur: 25 },
    animation: { microMovementIntensity: 0.5 },
    ariaLabel: 'Rafiki is speaking'
  },
  error: {
    glow: { color: 'rgba(178, 34, 34, 0.6)', intensity: 0.7, pulseSpeed: 500, blur: 35 },
    animation: { microMovementIntensity: 0.1 },
    ariaLabel: 'An error occurred. Please try again.'
  }
};

// Color palette for Rafiki (Kenyan flag colors + skin tones)
export const RAFIKI_COLORS = {
  // Primary palette (Kenyan flag)
  primary: {
    red: '#C8102E',
    white: '#FFFFFF',
    black: '#000000',
    green: '#007A33'
  },
  // Skin tones
  skin: {
    base: '#8D5524',
    highlight: '#A67B5B',
    shadow: '#5C3D2E',
    undertone: '#C68642'
  },
  // UI accents
  accent: {
    gold: '#FFD700',
    warmGlow: '#FFA500',
    coolGlow: '#4169E1'
  }
};

// Default animation configuration
export const DEFAULT_ANIMATION_CONFIG: AnimationConfig = {
  blinkInterval: { min: 2000, max: 6000 },
  blinkDuration: 150,
  microMovementIntensity: 0.3,
  transitionDuration: 300
};
