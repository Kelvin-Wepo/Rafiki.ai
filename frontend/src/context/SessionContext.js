/**
 * Session Context
 * Manages user session and conversation state
 */

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import api from '../services/api';

const SessionContext = createContext(null);

export function SessionProvider({ children }) {
  const [sessionId, setSessionId] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [conversationHistory, setConversationHistory] = useState([]);
  const [bookingState, setBookingState] = useState({});
  const [currentStep, setCurrentStep] = useState(0);

  // Initialize session on mount
  useEffect(() => {
    initializeSession();
  }, []);

  const initializeSession = async () => {
    setIsLoading(true);
    try {
      // Check for existing session
      const existingSessionId = localStorage.getItem('sessionId');
      
      if (existingSessionId) {
        // Validate existing session
        const response = await api.getSession(existingSessionId);
        if (response.is_active) {
          setSessionId(existingSessionId);
          // Load session state
          const state = await api.getSessionState(existingSessionId);
          setBookingState(state.booking_state || {});
          setCurrentStep(state.booking_progress?.percentage / 25 || 0);
          setIsLoading(false);
          return;
        }
      }

      // Create new session
      const response = await api.createSession({
        accessibility_preferences: JSON.parse(
          localStorage.getItem('accessibilitySettings') || '{}'
        ),
      });

      setSessionId(response.session_id);
      localStorage.setItem('sessionId', response.session_id);
    } catch (error) {
      console.error('Failed to initialize session:', error);
      // Create a local fallback session ID
      const fallbackId = `local-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
      setSessionId(fallbackId);
      localStorage.setItem('sessionId', fallbackId);
    } finally {
      setIsLoading(false);
    }
  };

  const addMessage = useCallback((message) => {
    setConversationHistory(prev => [...prev, {
      ...message,
      id: Date.now(),
      timestamp: new Date().toISOString(),
    }]);
  }, []);

  const clearConversation = useCallback(() => {
    setConversationHistory([]);
    setBookingState({});
    setCurrentStep(0);
  }, []);

  const updateBookingState = useCallback((updates) => {
    setBookingState(prev => ({ ...prev, ...updates }));
  }, []);

  const resetSession = useCallback(async () => {
    try {
      if (sessionId && !sessionId.startsWith('local-')) {
        await api.resetSession(sessionId);
      }
      clearConversation();
    } catch (error) {
      console.error('Failed to reset session:', error);
      clearConversation();
    }
  }, [sessionId, clearConversation]);

  const endSession = useCallback(async () => {
    try {
      if (sessionId && !sessionId.startsWith('local-')) {
        await api.deleteSession(sessionId);
      }
      localStorage.removeItem('sessionId');
      setSessionId(null);
      clearConversation();
      // Reinitialize new session
      await initializeSession();
    } catch (error) {
      console.error('Failed to end session:', error);
    }
  }, [sessionId, clearConversation]);

  const value = {
    sessionId,
    isLoading,
    conversationHistory,
    bookingState,
    currentStep,
    addMessage,
    clearConversation,
    updateBookingState,
    setCurrentStep,
    resetSession,
    endSession,
    initializeSession,
  };

  return (
    <SessionContext.Provider value={value}>
      {children}
    </SessionContext.Provider>
  );
}

export function useSession() {
  const context = useContext(SessionContext);
  if (!context) {
    throw new Error('useSession must be used within SessionProvider');
  }
  return context;
}

export default SessionContext;
