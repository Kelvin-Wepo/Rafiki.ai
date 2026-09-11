import { getStoredToken } from '../services/authService';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';
export const AGENCY_SESSION_KEY = 'rafiki_agency_session';

export type AgencyChatResponse = {
  session_id: string;
  response: string;
  step?: string;
  agency?: string | null;
  service?: string | null;
  language?: string;
  awaiting_payment?: boolean;
  payment_amount?: number | null;
  payment_description?: string | null;
  audio_base64?: string | null;
  audio_mime?: string;
  application_ref?: string | null;
  payment_ref?: string | null;
  receipt_available?: boolean;
  payment_demo?: boolean;
  detail?: string;
  message?: string;
};

async function agencyFetch(path: string, init: RequestInit = {}) {
  const token = getStoredToken();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(init.headers as Record<string, string> | undefined),
  };
  if (token) headers.Authorization = `Bearer ${token}`;
  const response = await fetch(`${API_BASE}${path}`, { ...init, headers });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const error = new Error(data.detail || data.message || `Request failed (${response.status})`);
    (error as Error & { payload?: unknown }).payload = data;
    throw error;
  }
  return data;
}

export function readAgencySessionId(): string | null {
  try {
    return sessionStorage.getItem(AGENCY_SESSION_KEY);
  } catch {
    return null;
  }
}

export function writeAgencySessionId(id: string | null): void {
  try {
    if (id) sessionStorage.setItem(AGENCY_SESSION_KEY, id);
    else sessionStorage.removeItem(AGENCY_SESSION_KEY);
  } catch {
    /* ignore */
  }
}

export async function startAgencyService(
  slug: string,
  language: string,
  chatSessionId?: string | null
): Promise<AgencyChatResponse> {
  return agencyFetch('/api/agencies/chat/start-service', {
    method: 'POST',
    body: JSON.stringify({
      service: slug,
      language,
      chat_session_id: chatSessionId || undefined,
    }),
  });
}

export async function continueAgencyChat(
  sessionId: string,
  message: string,
  chatSessionId?: string | null
): Promise<AgencyChatResponse> {
  return agencyFetch('/api/agencies/chat', {
    method: 'POST',
    body: JSON.stringify({
      session_id: sessionId,
      message,
      chat_session_id: chatSessionId || undefined,
    }),
  });
}

export async function checkAgencyPayment(sessionId: string): Promise<{
  paid?: boolean;
  application_ref?: string | null;
  payment_ref?: string | null;
  message?: string;
  demo?: boolean;
}> {
  return agencyFetch(`/api/agencies/payment/status/${sessionId}`);
}
