/**
 * API Service
 * Handles all communication with the backend
 */

import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Create axios instance with defaults
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for logging
apiClient.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('API Request Error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const message = error.response?.data?.message || error.message || 'An error occurred';
    console.error('API Error:', message);
    return Promise.reject(new Error(message));
  }
);

const api = {
  // Session endpoints
  createSession: async (preferences = {}) => {
    return apiClient.post('/session/create', preferences);
  },

  getSession: async (sessionId) => {
    return apiClient.get(`/session/${sessionId}`);
  },

  getSessionState: async (sessionId) => {
    return apiClient.get(`/session/${sessionId}/state`);
  },

  updatePreferences: async (sessionId, preferences) => {
    return apiClient.patch(`/session/${sessionId}/preferences`, preferences);
  },

  resetSession: async (sessionId) => {
    return apiClient.post(`/session/${sessionId}/reset`);
  },

  deleteSession: async (sessionId) => {
    return apiClient.delete(`/session/${sessionId}`);
  },

  // Voice endpoints
  processVoiceInput: async (data) => {
    return apiClient.post('/voice/process', data);
  },

  transcribeAudio: async (data) => {
    return apiClient.post('/voice/transcribe', data);
  },

  textToSpeech: async (text) => {
    return apiClient.post('/voice/speak', null, { params: { text } });
  },

  getVoices: async () => {
    return apiClient.get('/voice/voices');
  },

  updateVoiceSettings: async (settings) => {
    return apiClient.post('/voice/settings', null, { params: settings });
  },

  // Booking endpoints
  createBooking: async (bookingData) => {
    return apiClient.post('/booking/create', bookingData);
  },

  getBooking: async (bookingId) => {
    return apiClient.get(`/booking/${bookingId}`);
  },

  getUserBookings: async (phoneNumber, status = null) => {
    const params = status ? { status } : {};
    return apiClient.get(`/booking/user/${phoneNumber}`, { params });
  },

  cancelBooking: async (bookingId, sendSms = true) => {
    return apiClient.delete(`/booking/${bookingId}`, { params: { send_sms: sendSms } });
  },

  updateBooking: async (bookingId, updates) => {
    return apiClient.patch(`/booking/${bookingId}`, updates);
  },

  getAvailability: async (serviceType, daysAhead = 30) => {
    return apiClient.get(`/booking/availability/${serviceType}`, {
      params: { days_ahead: daysAhead },
    });
  },

  // Services endpoints
  getServices: async () => {
    return apiClient.get('/services/');
  },

  getService: async (serviceType) => {
    return apiClient.get(`/services/${serviceType}`);
  },

  getServiceRequirements: async (serviceType) => {
    return apiClient.get(`/services/${serviceType}/requirements`);
  },

  getECitizenInfo: async (serviceType) => {
    return apiClient.get(`/services/${serviceType}/ecitizen-info`);
  },

  // Health and utility endpoints
  healthCheck: async () => {
    return apiClient.get('/health');
  },

  getWelcomeMessage: async () => {
    return apiClient.get('/welcome');
  },

  // Chat/Message endpoints for Gemini integration
  sendMessage: async (message, language = 'en', sessionId = null) => {
    return apiClient.post('/voice/chat', {
      message,
      language,
      session_id: sessionId,
    });
  },

  // Analyze text for automation commands (used with ElevenLabs)
  analyzeForAutomation: async (text, language = 'en') => {
    return apiClient.post('/voice/analyze-automation', {
      text,
      language,
    });
  },
};

export default api;
