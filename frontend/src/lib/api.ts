/**
 * API Integration Layer
 * Centralized API calls for Rafiki AI Assistant
 * Mapped to actual backend endpoints
 */

import axios, { type AxiosInstance, type AxiosError } from 'axios';

// Get the base URL from environment variable
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Create axios instance with default config
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('rafiki_access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      // Clear token and redirect to login
      localStorage.removeItem('rafiki_access_token');
      localStorage.removeItem('rafiki_user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// ============================================
// AUTH API - Maps to /auth/* endpoints
// ============================================

export interface AuthResponse {
  success: boolean;
  message: string;
  user_id?: string;
  access_token?: string;
  token_type?: string;
  expires_in?: number;
  is_new_user?: boolean;
  user?: {
    user_id: string;
    phone_masked: string;
    status: string;
    created_at: string;
    last_login: string | null;
  };
  phone_masked?: string;
  error?: string;
  retry_after?: number;
}

export interface UserProfile {
  user_id: string;
  phone_masked: string;
  status: string;
  created_at: string;
  last_login: string | null;
}

export const authApi = {
  /**
   * Initiate login with phone number - sends OTP
   * POST /auth/login
   */
  login: async (phoneNumber: string): Promise<AuthResponse> => {
    const response = await apiClient.post('/auth/login', {
      phone_number: phoneNumber,
    });
    return response.data;
  },

  /**
   * Verify OTP and get auth token
   * POST /auth/verify-otp
   */
  verifyOTP: async (phoneNumber: string, otp: string): Promise<AuthResponse> => {
    const response = await apiClient.post('/auth/verify-otp', {
      phone_number: phoneNumber,
      otp: otp,
    });
    return response.data;
  },

  /**
   * Logout and invalidate session
   * POST /auth/logout
   */
  logout: async (): Promise<{ success: boolean; message: string }> => {
    const response = await apiClient.post('/auth/logout');
    localStorage.removeItem('rafiki_access_token');
    localStorage.removeItem('rafiki_user');
    return response.data;
  },

  /**
   * Get current user profile
   * GET /auth/me
   */
  getProfile: async (): Promise<UserProfile> => {
    const response = await apiClient.get('/auth/me');
    return response.data;
  },

  /**
   * Validate current token
   * GET /auth/validate
   */
  validateToken: async (): Promise<{ valid: boolean; user_id?: string }> => {
    try {
      const response = await apiClient.get('/auth/validate');
      return { valid: true, ...response.data };
    } catch {
      return { valid: false };
    }
  },
};

// ============================================
// SESSION API - Maps to /session/* endpoints
// ============================================

export interface Session {
  session_id: string;
  created_at: string;
  expires_at: string;
  is_active: boolean;
}

export interface SessionState {
  session_id: string;
  conversation_context: Record<string, unknown>;
  booking_state: Record<string, unknown>;
  booking_progress: {
    percentage: number;
    completed_fields: string[];
    remaining_fields: string[];
  };
  user_preferences: Record<string, unknown>;
  last_activity: string;
}

export const sessionApi = {
  /**
   * Create a new conversation session
   * POST /session/create
   */
  create: async (preferences?: Record<string, unknown>): Promise<Session> => {
    const response = await apiClient.post('/session/create', {
      accessibility_preferences: preferences,
    });
    return response.data;
  },

  /**
   * Get session details
   * GET /session/{session_id}
   */
  get: async (sessionId: string): Promise<Session> => {
    const response = await apiClient.get(`/session/${sessionId}`);
    return response.data;
  },

  /**
   * Get session conversation state
   * GET /session/{session_id}/state
   */
  getState: async (sessionId: string): Promise<SessionState> => {
    const response = await apiClient.get(`/session/${sessionId}/state`);
    return response.data;
  },

  /**
   * Update session preferences
   * PATCH /session/{session_id}/preferences
   */
  updatePreferences: async (
    sessionId: string,
    preferences: Record<string, unknown>
  ): Promise<Session> => {
    const response = await apiClient.patch(`/session/${sessionId}/preferences`, preferences);
    return response.data;
  },
};

// ============================================
// VOICE API - Maps to /voice/* endpoints
// ============================================

export interface VoiceProcessRequest {
  audio_data?: string; // Base64 encoded audio
  text_input?: string;
  session_id: string;
  input_mode: 'voice' | 'text';
  language?: string;
}

export interface AssistantResponse {
  text: string;
  session_id: string;
  intent?: string;
  entities?: Record<string, unknown>;
  requires_input: boolean;
  suggested_actions: string[];
  context?: {
    conversation_state?: string;
    transcribed_text?: string;
  };
}

export const voiceApi = {
  /**
   * Process voice or text input
   * POST /voice/process
   */
  process: async (request: VoiceProcessRequest): Promise<AssistantResponse> => {
    const response = await apiClient.post('/voice/process', request);
    return response.data;
  },

  /**
   * Send text message
   */
  sendMessage: async (
    text: string,
    sessionId: string,
    language: string = 'en-KE'
  ): Promise<AssistantResponse> => {
    return voiceApi.process({
      text_input: text,
      session_id: sessionId,
      input_mode: 'text',
      language,
    });
  },

  /**
   * Send audio message
   */
  sendAudio: async (
    audioBase64: string,
    sessionId: string,
    language: string = 'en-KE'
  ): Promise<AssistantResponse> => {
    return voiceApi.process({
      audio_data: audioBase64,
      session_id: sessionId,
      input_mode: 'voice',
      language,
    });
  },
};

// ============================================
// ELEVENLABS TTS API - Maps to /elevenlabs/* endpoints
// ============================================

export interface TTSRequest {
  text: string;
  voice_id?: string;
  model_id?: string;
}

export interface TTSResponse {
  success: boolean;
  audio_data?: string; // Base64 encoded audio
  content_type?: string;
  error?: string;
}

export interface SignedUrlResponse {
  success: boolean;
  signed_url?: string;
  agent_id?: string;
  error?: string;
}

export interface Voice {
  voice_id: string;
  name: string;
  preview_url?: string;
  labels?: Record<string, string>;
}

export const ttsApi = {
  /**
   * Get signed URL for ElevenLabs agent WebSocket
   * GET /elevenlabs/signed-url
   */
  getSignedUrl: async (agentId?: string): Promise<SignedUrlResponse> => {
    const response = await apiClient.get('/elevenlabs/signed-url', {
      params: agentId ? { agent_id: agentId } : undefined,
    });
    return response.data;
  },

  /**
   * Text-to-speech conversion
   * POST /elevenlabs/tts
   */
  textToSpeech: async (request: TTSRequest): Promise<TTSResponse> => {
    const response = await apiClient.post('/elevenlabs/tts', request);
    return response.data;
  },

  /**
   * Get available voices
   * GET /elevenlabs/voices
   */
  getVoices: async (): Promise<{ success: boolean; voices: Voice[] }> => {
    const response = await apiClient.get('/elevenlabs/voices');
    return response.data;
  },
};

// ============================================
// AVATAR ANIMATION API - Maps to /api/avatar/* endpoints
// ============================================

export interface AnimateRequest {
  audio_file: File;
  avatar_id?: string;
  preprocess?: 'crop' | 'resize' | 'full';
  still_mode?: boolean;
  expression_scale?: number;
}

export interface TextToVideoRequest {
  text: string;
  avatar_id?: string;
  voice_id?: string;
  preprocess?: 'crop' | 'resize' | 'full';
  still_mode?: boolean;
  expression_scale?: number;
}

export const avatarApi = {
  /**
   * Generate talking avatar video from audio
   * POST /api/avatar/animate
   */
  animateFromAudio: async (request: AnimateRequest): Promise<Blob> => {
    const formData = new FormData();
    formData.append('audio_file', request.audio_file);
    if (request.avatar_id) formData.append('avatar_id', request.avatar_id);
    if (request.preprocess) formData.append('preprocess', request.preprocess);
    if (request.still_mode !== undefined) formData.append('still_mode', String(request.still_mode));
    if (request.expression_scale !== undefined) formData.append('expression_scale', String(request.expression_scale));

    const response = await apiClient.post('/api/avatar/animate', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      responseType: 'blob',
    });
    return response.data;
  },

  /**
   * Generate talking avatar video from text
   * POST /api/avatar/text-to-video
   */
  textToVideo: async (request: TextToVideoRequest): Promise<Blob> => {
    const formData = new FormData();
    formData.append('text', request.text);
    if (request.avatar_id) formData.append('avatar_id', request.avatar_id);
    if (request.voice_id) formData.append('voice_id', request.voice_id);
    if (request.preprocess) formData.append('preprocess', request.preprocess);
    if (request.still_mode !== undefined) formData.append('still_mode', String(request.still_mode));
    if (request.expression_scale !== undefined) formData.append('expression_scale', String(request.expression_scale));

    const response = await apiClient.post('/api/avatar/text-to-video', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      responseType: 'blob',
    });
    return response.data;
  },

  /**
   * Get available avatars
   * GET /api/avatar/avatars
   */
  getAvatars: async (): Promise<{ avatars: Array<{ id: string; name: string; thumbnail: string }> }> => {
    const response = await apiClient.get('/api/avatar/avatars');
    return response.data;
  },

  /**
   * Get animation settings
   * GET /api/avatar/settings
   */
  getSettings: async (): Promise<Record<string, unknown>> => {
    const response = await apiClient.get('/api/avatar/settings');
    return response.data;
  },
};

// ============================================
// SERVICES API - Maps to /services/* endpoints
// ============================================

export interface GovernmentService {
  id: string;
  name: string;
  description: string;
  category: string;
  requirements?: string[];
  estimated_time?: string;
}

export const servicesApi = {
  /**
   * Get available services
   * GET /services
   */
  getAll: async (): Promise<GovernmentService[]> => {
    const response = await apiClient.get('/services');
    return response.data;
  },

  /**
   * Get service by ID
   * GET /services/{service_id}
   */
  getById: async (serviceId: string): Promise<GovernmentService> => {
    const response = await apiClient.get(`/services/${serviceId}`);
    return response.data;
  },
};

// ============================================
// BOOKING API - Maps to /booking/* endpoints
// ============================================

export interface BookingRequest {
  service_id: string;
  date: string;
  time_slot: string;
  user_name: string;
  phone_number: string;
}

export interface Booking {
  booking_id: string;
  service_id: string;
  date: string;
  time_slot: string;
  status: string;
  confirmation_code?: string;
}

export const bookingApi = {
  /**
   * Create a new booking
   * POST /booking/create
   */
  create: async (request: BookingRequest): Promise<Booking> => {
    const response = await apiClient.post('/booking/create', request);
    return response.data;
  },

  /**
   * Get booking by ID
   * GET /booking/{booking_id}
   */
  getById: async (bookingId: string): Promise<Booking> => {
    const response = await apiClient.get(`/booking/${bookingId}`);
    return response.data;
  },

  /**
   * Get available time slots
   * GET /booking/slots
   */
  getTimeSlots: async (serviceId: string, date: string): Promise<string[]> => {
    const response = await apiClient.get('/booking/slots', {
      params: { service_id: serviceId, date },
    });
    return response.data;
  },
};

// Export the axios instance for custom requests
export { apiClient };

// ============================================
// AGENCIES API - Maps to /api/agencies/* endpoints
// ============================================

export interface AgenciesChatRequest {
  session_id?: string;
  message: string;
}

export interface AgenciesChatResponse {
  session_id: string;
  response: string;
  step: string;
  agency: string | null;
  service: string | null;
  awaiting_payment: boolean;
  payment_amount: number | null;
}

export interface PaymentInitRequest {
  session_id: string;
  phone: string;
  amount_ksh: number;
  service: string;
  email?: string;
}

export interface PaymentVerifyResponse {
  success: boolean;
  paid: boolean;
  status?: string;
  amount_ksh?: number;
  message: string;
}

export const agenciesApi = {
  /**
   * Start a new chat session with Rafiki
   * POST /api/agencies/chat/start
   */
  startChat: async (): Promise<AgenciesChatResponse> => {
    const response = await apiClient.post('/api/agencies/chat/start');
    return response.data;
  },

  /**
   * Send a message in the chat flow
   * POST /api/agencies/chat
   */
  chat: async (request: AgenciesChatRequest): Promise<AgenciesChatResponse> => {
    const response = await apiClient.post('/api/agencies/chat', request);
    return response.data;
  },

  /**
   * Send a message with an existing session
   */
  sendMessage: async (sessionId: string, message: string): Promise<AgenciesChatResponse> => {
    return agenciesApi.chat({ session_id: sessionId, message });
  },

  /**
   * Initiate M-PESA payment
   * POST /api/agencies/payment/initiate
   */
  initiatePayment: async (request: PaymentInitRequest): Promise<{
    reference: string;
    message: string;
    display_text: string;
  }> => {
    const response = await apiClient.post('/api/agencies/payment/initiate', request);
    return response.data;
  },

  /**
   * Verify payment status
   * POST /api/agencies/payment/verify
   */
  verifyPayment: async (reference: string): Promise<PaymentVerifyResponse> => {
    const response = await apiClient.post('/api/agencies/payment/verify', { reference });
    return response.data;
  },

  /**
   * Get payment status for session
   * GET /api/agencies/payment/status/{session_id}
   */
  getPaymentStatus: async (sessionId: string): Promise<PaymentVerifyResponse> => {
    const response = await apiClient.get(`/api/agencies/payment/status/${sessionId}`);
    return response.data;
  },

  /**
   * End/clear a session
   * DELETE /api/agencies/chat/{session_id}
   */
  endSession: async (sessionId: string): Promise<{ message: string }> => {
    const response = await apiClient.delete(`/api/agencies/chat/${sessionId}`);
    return response.data;
  },
};

// Default export with all APIs
const api = {
  auth: authApi,
  session: sessionApi,
  voice: voiceApi,
  tts: ttsApi,
  avatar: avatarApi,
  services: servicesApi,
  booking: bookingApi,
  agencies: agenciesApi,
};

export default api;
