/**
 * Voice State Machine Types
 * Defines all states and transitions for the voice assistant
 */

export type VoiceState = 'idle' | 'listening' | 'processing' | 'talking';

export interface VoiceStateConfig {
  label: string;
  color: string;
  bgColor: string;
  description: string;
}

export const VOICE_STATE_CONFIG: Record<VoiceState, VoiceStateConfig> = {
  idle: {
    label: 'Ready',
    color: 'text-green-400',
    bgColor: 'bg-green-500/20',
    description: 'Tap the microphone to speak',
  },
  listening: {
    label: 'Listening...',
    color: 'text-blue-400',
    bgColor: 'bg-blue-500/20',
    description: 'Speak now, I\'m listening',
  },
  processing: {
    label: 'Processing...',
    color: 'text-purple-400',
    bgColor: 'bg-purple-500/20',
    description: 'Analyzing your request',
  },
  talking: {
    label: 'Speaking',
    color: 'text-orange-400',
    bgColor: 'bg-orange-500/20',
    description: 'Rafiki is responding',
  },
};

/**
 * User Types - matches authService User type
 */
export interface User {
  user_id: string;
  phone_masked: string;
  status: string;
  created_at: string;
  last_login: string | null;
}

/**
 * Chat Types
 */
export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  audioUrl?: string;
}

export interface Conversation {
  id: string;
  title: string;
  messages: Message[];
  createdAt: Date;
  updatedAt: Date;
}

/**
 * Quick Action Types
 */
export interface QuickAction {
  id: string;
  label: string;
  query: string;
  icon?: string;
}

export const DEFAULT_QUICK_ACTIONS: QuickAction[] = [
  {
    id: 'id-status',
    label: 'Check ID application status',
    query: 'What is the status of my ID application?',
  },
  {
    id: 'find-office',
    label: 'Find a government office',
    query: 'Help me find the nearest government office',
  },
  {
    id: 'birth-cert',
    label: 'Apply for a birth certificate',
    query: 'How do I apply for a birth certificate?',
  },
];

/**
 * Sidebar Navigation Types
 */
export interface NavItem {
  id: string;
  label: string;
  icon: string;
  path?: string;
  action?: () => void;
}

/**
 * Audio Waveform Types
 */
export interface WaveformBar {
  height: number;
  delay: number;
}
