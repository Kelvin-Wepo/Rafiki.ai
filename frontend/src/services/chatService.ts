const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
import { getStoredToken } from './authService';

async function apiFetch(path: string, init: RequestInit = {}) {
  const token = getStoredToken();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(init.headers as Record<string, string> || {}),
  };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE_URL}${path}`, {
    credentials: 'include',
    ...init,
    headers,
  });

  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(text || res.statusText);
  }

  // Try to parse JSON, otherwise return raw
  const contentType = res.headers.get('content-type') || '';
  if (contentType.includes('application/json')) return res.json();
  return res;
}

export async function createSession() {
  return apiFetch('/api/chat/sessions', { method: 'POST' });
}

export async function listSessions(skip = 0, limit = 20) {
  return apiFetch(`/api/chat/sessions?skip=${skip}&limit=${limit}`);
}

export async function getSession(id: string) {
  return apiFetch(`/api/chat/sessions/${id}`);
}

export async function postMessage(sessionId: string, sender: string, content: string, audioUrl?: string) {
  return apiFetch(`/api/chat/sessions/${sessionId}/messages`, {
    method: 'POST',
    body: JSON.stringify({ session_id: sessionId, sender, content, audio_url: audioUrl }),
  });
}

export async function listTranscripts(skip = 0, limit = 20) {
  return apiFetch(`/api/chat/transcripts?skip=${skip}&limit=${limit}`);
}

export async function downloadTranscript(transcriptId: string) {
  const token = getStoredToken();
  const res = await fetch(`${API_BASE_URL}/api/chat/transcripts/${transcriptId}/download`, {
    headers: token ? { Authorization: `Bearer ${token}` } : undefined,
  });
  if (!res.ok) throw new Error('Failed to download transcript');
  return res.blob();
}

export async function unreadCount() {
  return apiFetch('/api/chat/transcripts/unread-count');
}

export async function generateTranscript(sessionId: string, format = 'pdf') {
  return apiFetch(`/api/chat/sessions/${sessionId}/generate-transcript?format=${encodeURIComponent(format)}`, { method: 'POST' });
}

export default {
  createSession,
  listSessions,
  getSession,
  postMessage,
  listTranscripts,
  downloadTranscript,
  unreadCount,
  generateTranscript,
};
