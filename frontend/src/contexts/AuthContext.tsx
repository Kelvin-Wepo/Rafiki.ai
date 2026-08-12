/**
 * Authentication Context
 * Provides auth state and functions throughout the application.
 * 
 * Features:
 * - Phone-based OTP authentication
 * - Session management
 * - Token persistence
 * - Auto-validation on mount
 */

import {
  createContext,
  useContext,
  useEffect,
  useState,
  useCallback,
  type ReactNode,
} from 'react';
import type { User, AuthResponse, OTPDeliveryMethod, PasswordLoginResponse } from '../services/authService';
import {
  initiateLogin,
  verifyOTP,
  logout as logoutApi,
  validateToken,
  getCurrentUser,
  getStoredToken,
  getStoredUser,
  clearAuthData,
  passwordLogin as passwordLoginApi,
  storeToken,
  storeUser,
} from '../services/authService';

// Auth state interface
interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

// Auth context interface
interface AuthContextType extends AuthState {
  // Auth actions
  login: (phoneNumber: string, deliveryMethod?: OTPDeliveryMethod) => Promise<AuthResponse>;
  passwordLogin: (identifier: string, password: string) => Promise<PasswordLoginResponse>;
  verify: (phoneNumber: string, otp: string) => Promise<AuthResponse>;
  logout: () => Promise<void>;
  clearError: () => void;
  completeSession: (user: User, token: string, sessionId?: string) => void;
  
  // Auth state helpers
  pendingPhone: string | null;
  setPendingPhone: (phone: string | null) => void;
  isVerifying: boolean;
  setIsVerifying: (value: boolean) => void;
  lastDeliveryMethod: OTPDeliveryMethod | null;
}

// Create context with undefined initial value
const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Provider props
interface AuthProviderProps {
  children: ReactNode;
}

/**
 * Auth Provider Component
 * Wraps the application to provide authentication state and functions.
 */
export function AuthProvider({ children }: AuthProviderProps) {
  // Core auth state
  const [user, setUser] = useState<User | null>(() => getStoredUser());
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // OTP flow state
  const [pendingPhone, setPendingPhone] = useState<string | null>(null);
  const [isVerifying, setIsVerifying] = useState(false);
  const [lastDeliveryMethod, setLastDeliveryMethod] = useState<OTPDeliveryMethod | null>(null);

  /**
   * Validate existing token on mount.
   * Uses parallel API calls to reduce load time.
   */
  useEffect(() => {
    const validateAuth = async () => {
      const token = getStoredToken();
      
      if (!token) {
        setIsLoading(false);
        return;
      }
      
      try {
        // Parallelize API calls instead of sequential
        const [validation, userData] = await Promise.all([
          validateToken().catch(() => null),
          getCurrentUser().catch(() => null)
        ]);
        
        if (validation?.valid && userData) {
          setUser(userData);
          setIsAuthenticated(true);
        } else {
          // Token invalid or user fetch failed
          clearAuthData();
          setUser(null);
          setIsAuthenticated(false);
        }
      } catch {
        // Validation failed
        clearAuthData();
        setUser(null);
        setIsAuthenticated(false);
      } finally {
        setIsLoading(false);
      }
    };
    
    validateAuth();
  }, []);

  /**
   * Initiate login with phone number.
   * Sends OTP via SMS, Voice, or Both.
   */
  const login = useCallback(async (
    phoneNumber: string,
    deliveryMethod: OTPDeliveryMethod = 'both'
  ): Promise<AuthResponse> => {
    setError(null);
    setIsLoading(true);
    
    try {
      const response = await initiateLogin(phoneNumber, deliveryMethod);
      
      if (response.success) {
        setPendingPhone(phoneNumber);
        setLastDeliveryMethod(deliveryMethod);
        setIsVerifying(true);
      } else {
        setError(response.message || 'Failed to send OTP');
      }
      
      return response;
    } catch (err: unknown) {
      const errorMessage = err instanceof Error 
        ? err.message 
        : (err as { message?: string })?.message || 'Failed to initiate login';
      setError(errorMessage);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * Verify OTP and complete authentication.
   */
  const verify = useCallback(async (
    phoneNumber: string,
    otp: string
  ): Promise<AuthResponse> => {
    setError(null);
    setIsLoading(true);
    
    try {
      const response = await verifyOTP(phoneNumber, otp);
      
      if (response.success && response.user) {
        setUser(response.user);
        setIsAuthenticated(true);
        setPendingPhone(null);
        setIsVerifying(false);
      } else {
        setError(response.message || 'Invalid OTP');
      }
      
      return response;
    } catch (err: unknown) {
      const errorObj = err as { message?: string; error?: string };
      const errorMessage = errorObj?.message || errorObj?.error || 'Verification failed';
      setError(errorMessage);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * Logout and clear session.
   */
  const logout = useCallback(async (): Promise<void> => {
    setIsLoading(true);
    
    try {
      await logoutApi();
    } finally {
      setUser(null);
      setIsAuthenticated(false);
      setPendingPhone(null);
      setIsVerifying(false);
      setError(null);
      setIsLoading(false);
    }
  }, []);

  /**
   * Login with email/phone and password.
   */
  const passwordLogin = useCallback(async (
    identifier: string,
    password: string
  ): Promise<PasswordLoginResponse> => {
    setError(null);
    setIsLoading(true);
    
    try {
      const response = await passwordLoginApi(identifier, password);
      
      if (response.success && response.user) {
        setUser(response.user);
        setIsAuthenticated(true);
      } else if (response.success) {
        // Login successful but no user object returned - still mark as authenticated
        setIsAuthenticated(true);
      } else {
        setError(response.message || 'Login failed');
      }
      
      return response;
    } catch (err: unknown) {
      const errorObj = err as { message?: string; error?: string; detail?: string };
      const errorMessage = errorObj?.message || errorObj?.detail || errorObj?.error || 'Login failed';
      setError(errorMessage);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * Clear error message.
   */
  const clearError = useCallback(() => {
    setError(null);
  }, []);

  /**
   * Complete an authenticated session started outside the normal login flows
   * (e.g. after signup + OTP verification). Persists the token/user and
   * updates context state so ProtectedRoute recognizes the session.
   */
  const completeSession = useCallback((newUser: User, token: string, sessionId?: string) => {
    storeToken(token);
    storeUser(newUser);
    if (sessionId) {
      localStorage.setItem('rafiki_session_id', sessionId);
    }
    setUser(newUser);
    setIsAuthenticated(true);
  }, []);

  // Context value
  const value: AuthContextType = {
    user,
    isAuthenticated,
    isLoading,
    error,
    login,
    passwordLogin,
    verify,
    logout,
    clearError,
    completeSession,
    pendingPhone,
    setPendingPhone,
    isVerifying,
    setIsVerifying,
    lastDeliveryMethod,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

/**
 * Custom hook to use auth context.
 * Must be used within an AuthProvider.
 */
export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  
  return context;
}

export default AuthContext;
