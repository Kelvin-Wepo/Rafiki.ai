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
import type { User, AuthResponse } from '../services/authService';
import {
  initiateLogin,
  verifyOTP,
  logout as logoutApi,
  validateToken,
  getCurrentUser,
  getStoredToken,
  getStoredUser,
  clearAuthData,
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
  login: (phoneNumber: string) => Promise<AuthResponse>;
  verify: (phoneNumber: string, otp: string) => Promise<AuthResponse>;
  logout: () => Promise<void>;
  clearError: () => void;
  
  // Auth state helpers
  pendingPhone: string | null;
  setPendingPhone: (phone: string | null) => void;
  isVerifying: boolean;
  setIsVerifying: (value: boolean) => void;
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

  /**
   * Validate existing token on mount.
   */
  useEffect(() => {
    const validateAuth = async () => {
      const token = getStoredToken();
      
      if (!token) {
        setIsLoading(false);
        return;
      }
      
      try {
        const validation = await validateToken();
        
        if (validation?.valid) {
          // Token is valid, fetch user details
          const userData = await getCurrentUser();
          if (userData) {
            setUser(userData);
            setIsAuthenticated(true);
          } else {
            // Could not get user, clear auth
            clearAuthData();
            setUser(null);
            setIsAuthenticated(false);
          }
        } else {
          // Token invalid
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
   * Sends OTP via SMS.
   */
  const login = useCallback(async (phoneNumber: string): Promise<AuthResponse> => {
    setError(null);
    setIsLoading(true);
    
    try {
      const response = await initiateLogin(phoneNumber);
      
      if (response.success) {
        setPendingPhone(phoneNumber);
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
   * Clear error message.
   */
  const clearError = useCallback(() => {
    setError(null);
  }, []);

  // Context value
  const value: AuthContextType = {
    user,
    isAuthenticated,
    isLoading,
    error,
    login,
    verify,
    logout,
    clearError,
    pendingPhone,
    setPendingPhone,
    isVerifying,
    setIsVerifying,
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
