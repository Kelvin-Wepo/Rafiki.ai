import { useEffect, useState, useCallback } from 'react';
import * as chatService from '../services/chatService';

const STORAGE_KEY = 'rafiki_active_session';

export function useChatSessions() {
  const [sessions, setSessions] = useState<any[]>([]);
  const [transcripts, setTranscripts] = useState<any[]>([]);
  const [unread, setUnread] = useState<number>(0);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(() => {
    return localStorage.getItem(STORAGE_KEY);
  });
  const [isLoading, setIsLoading] = useState(false);

  const loadSessions = useCallback(async () => {
    setIsLoading(true);
    try {
      const data = await chatService.listSessions();
      setSessions(data || []);
    } catch (err) {
      console.error('Failed to load sessions', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const loadTranscripts = useCallback(async () => {
    try {
      const data = await chatService.listTranscripts();
      setTranscripts(data || []);
    } catch (err) {
      console.error('Failed to load transcripts', err);
    }
  }, []);

  const loadUnread = useCallback(async () => {
    try {
      const data = await chatService.unreadCount();
      setUnread(data?.count || 0);
    } catch (err) {
      console.error('Failed to load unread count', err);
    }
  }, []);

  useEffect(() => {
    loadSessions();
    loadTranscripts();
    loadUnread();
  }, [loadSessions, loadTranscripts, loadUnread]);

  const createNewSession = useCallback(async () => {
    const res = await chatService.createSession();
    const id = res?.id || res?.conversation_id || res?.session_id;
    if (id) {
      localStorage.setItem(STORAGE_KEY, id);
      setActiveSessionId(id);
      await loadSessions();
    }
    return id;
  }, [loadSessions]);

  const loadSession = useCallback(async (id: string) => {
    const session = await chatService.getSession(id);
    if (session) {
      localStorage.setItem(STORAGE_KEY, id);
      setActiveSessionId(id);
      // refresh sessions list
      await loadSessions();
    }
    return session;
  }, [loadSessions]);

  const sendMessage = useCallback(async (sessionId: string, sender: string, content: string, audioUrl?: string) => {
    const res = await chatService.postMessage(sessionId, sender, content, audioUrl);
    // refresh session
    const updated = await chatService.getSession(sessionId);
    await loadSessions();
    return { res, updated };
  }, [loadSessions]);

  const downloadTranscript = useCallback(async (transcriptId: string) => {
    const blob = await chatService.downloadTranscript(transcriptId);
    return blob;
  }, []);

  return {
    sessions,
    transcripts,
    unread,
    activeSessionId,
    isLoading,
    createNewSession,
    loadSession,
    sendMessage,
    downloadTranscript,
    refresh: async () => { await Promise.all([loadSessions(), loadTranscripts(), loadUnread()]); },
  };
}

export default useChatSessions;
