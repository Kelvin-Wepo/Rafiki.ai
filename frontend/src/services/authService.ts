/**
 * API Service for authentication and conversation management.
 * Handles all HTTP requests to the backend.
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Token storage keys
const TOKEN_KEY = 'rafiki_access_token';
const USER_KEY = 'rafiki_user';

/**
 * Get stored authentication token.
 */
export function getStoredToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

/**
 * Store authentication token.
 */
export function storeToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

/**
 * Clear stored authentication data.
 */
export function clearAuthData(): void {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

/**
 * Get stored user data.
 */
export function getStoredUser(): User | null {
  const data = localStorage.getItem(USER_KEY);
  return data ? JSON.parse(data) : null;
}

/**
 * Store user data.
 */
export function storeUser(user: User): void {
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

// Types
export interface User {
  id?: string;
  user_id?: string;
  full_name?: string;
  email_masked?: string;
  phone_masked?: string;
  status?: string;
  created_at?: string;
  last_login?: string | null;
}

export interface AuthResponse {
  success: boolean;
  message: string;
  user_id?: string;
  access_token?: string;
  token_type?: string;
  expires_in?: number;
  is_new_user?: boolean;
  user?: User;
  phone_masked?: string;
  error?: string;
  retry_after?: number;
}

export interface Conversation {
  id: string;
  title: string;
  preview?: string;
  message_count?: number;
  messages?: Message[];
  created_at: string;
  updated_at: string;
}

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  metadata?: Record<string, unknown>;
}

/**
 * Make authenticated API request.
 */
async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getStoredToken();
  
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...options.headers,
  };
  
  if (token) {
    (headers as Record<string, string>)['Authorization'] = `Bearer ${token}`;
  }
  
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });
  
  const data = await response.json();
  
  if (!response.ok) {
    throw {
      status: response.status,
      ...data,
    };
  }
  
  return data;
}

// ============== Authentication API ==============

// OTP Delivery Methods
export type OTPDeliveryMethod = 'sms' | 'voice' | 'both';

/**
 * Initiate login/registration with phone number.
 * Sends OTP via SMS, Voice Call, or Both.
 */
export async function initiateLogin(
  phoneNumber: string,
  deliveryMethod: OTPDeliveryMethod = 'both'
): Promise<AuthResponse> {
  return apiRequest<AuthResponse>('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ 
      phone_number: phoneNumber,
      delivery_method: deliveryMethod
    }),
  });
}

/**
 * Verify OTP and complete authentication.
 */
export async function verifyOTP(
  phoneNumber: string,
  otp: string
): Promise<AuthResponse> {
  const response = await apiRequest<AuthResponse>('/auth/verify-otp', {
    method: 'POST',
    body: JSON.stringify({ phone_number: phoneNumber, otp }),
  });
  
  // Store token and user on success
  if (response.success && response.access_token) {
    storeToken(response.access_token);
    if (response.user) {
      storeUser(response.user);
    }
  }
  
  return response;
}

/**
 * Logout and invalidate session.
 */
export async function logout(): Promise<{ success: boolean; message: string }> {
  try {
    const result = await apiRequest<{ success: boolean; message: string }>(
      '/auth/logout',
      { method: 'POST' }
    );
    clearAuthData();
    return result;
  } catch {
    // Clear local data even if server request fails
    clearAuthData();
    return { success: true, message: 'Logged out locally' };
  }
}

/**
 * Password-based login with email or phone.
 */
export interface PasswordLoginResponse {
  success: boolean;
  message: string;
  access_token?: string;
  session_id?: string;
  user?: User;
  error?: string;
}

export async function passwordLogin(
  identifier: string,
  password: string
): Promise<PasswordLoginResponse> {
  const response = await apiRequest<PasswordLoginResponse>('/auth/login/password', {
    method: 'POST',
    body: JSON.stringify({ identifier, password }),
  });
  
  // Store token and user on success
  if (response.success && response.access_token) {
    storeToken(response.access_token);
    if (response.user) {
      storeUser(response.user);
    }
    if (response.session_id) {
      localStorage.setItem('rafiki_session_id', response.session_id);
    }
  }
  
  return response;
}

/**
 * Validate current token.
 */
export async function validateToken(): Promise<{
  valid: boolean;
  user_id: string;
  phone_masked: string;
  expires: number;
} | null> {
  try {
    return await apiRequest('/auth/validate');
  } catch {
    clearAuthData();
    return null;
  }
}

/**
 * Get current user profile.
 */
export async function getCurrentUser(): Promise<User | null> {
  try {
    return await apiRequest<User>('/auth/me');
  } catch {
    return null;
  }
}

// ============== Conversation API ==============

/**
 * Create a new conversation.
 */
export async function createConversation(): Promise<Conversation> {
  return apiRequest<Conversation>('/auth/conversations', {
    method: 'POST',
  });
}

/**
 * Get all conversations for current user.
 */
export async function getConversations(
  includeArchived = false
): Promise<{ conversations: Conversation[] }> {
  const query = includeArchived ? '?include_archived=true' : '';
  return apiRequest<{ conversations: Conversation[] }>(
    `/auth/conversations${query}`
  );
}

/**
 * Get a specific conversation with messages.
 */
export async function getConversation(
  conversationId: string
): Promise<Conversation> {
  return apiRequest<Conversation>(`/auth/conversations/${conversationId}`);
}

/**
 * Add a message to a conversation.
 */
export async function addMessage(
  conversationId: string,
  role: 'user' | 'assistant',
  content: string,
  metadata?: Record<string, unknown>
): Promise<Message> {
  return apiRequest<Message>(`/auth/conversations/${conversationId}/messages`, {
    method: 'POST',
    body: JSON.stringify({ role, content, metadata }),
  });
}

/**
 * Delete (archive) a conversation.
 */
export async function deleteConversation(
  conversationId: string
): Promise<{ success: boolean; message: string }> {
  return apiRequest<{ success: boolean; message: string }>(
    `/auth/conversations/${conversationId}`,
    { method: 'DELETE' }
  );
}

/**
 * Export conversation transcript.
 */
export async function exportTranscript(
  conversationId: string,
  format: 'txt' | 'json' = 'txt'
): Promise<Blob> {
  const token = getStoredToken();
  
  const response = await fetch(
    `${API_BASE_URL}/auth/conversations/${conversationId}/export`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ conversation_id: conversationId, format }),
    }
  );
  
  if (!response.ok) {
    throw new Error('Failed to export transcript');
  }
  
  return response.blob();
}

/**
 * Download transcript file.
 */
export async function downloadTranscript(
  conversationId: string,
  format: 'txt' | 'json' = 'txt'
): Promise<void> {
  const blob = await exportTranscript(conversationId, format);
  
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `rafiki_transcript_${conversationId}.${format}`;
  document.body.appendChild(a);
  a.click();
  window.URL.revokeObjectURL(url);
  document.body.removeChild(a);
}

// ============== Audit Logs API ==============

/**
 * Get audit logs for current user.
 */
export async function getAuditLogs(
  limit = 50
): Promise<{
  logs: Array<{
    id: string;
    event_type: string;
    success: boolean;
    failure_reason: string | null;
    ip_address: string;
    timestamp: string;
  }>;
}> {
  return apiRequest(`/auth/audit-logs?limit=${limit}`);
}
