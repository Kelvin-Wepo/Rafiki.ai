/**
 * Login Form Component
 * Phone number input for initiating OTP authentication.
 * 
 * Features:
 * - Kenyan phone number validation (+254)
 * - Loading state during API call
 * - Error display
 * - National security branding
 */

import { useState, type FormEvent } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import './Auth.css';

interface LoginFormProps {
  onSuccess?: () => void;
}

export function LoginForm({ onSuccess }: LoginFormProps) {
  const { login, isLoading, error, clearError } = useAuth();
  const [phoneNumber, setPhoneNumber] = useState('');
  const [localError, setLocalError] = useState<string | null>(null);

  /**
   * Validate Kenyan phone number format.
   */
  const validatePhoneNumber = (phone: string): boolean => {
    // Remove spaces and dashes
    const cleaned = phone.replace(/[\s-]/g, '');
    
    // Valid formats:
    // +254XXXXXXXXX (12 chars)
    // 0XXXXXXXXX (10 chars)
    // 254XXXXXXXXX (12 chars)
    
    const patterns = [
      /^\+254\d{9}$/,    // +254...
      /^254\d{9}$/,       // 254...
      /^0\d{9}$/,         // 0...
    ];
    
    return patterns.some(pattern => pattern.test(cleaned));
  };

  /**
   * Format phone number to E.164 format for API.
   */
  const formatPhoneNumber = (phone: string): string => {
    const cleaned = phone.replace(/[\s-]/g, '');
    
    if (cleaned.startsWith('+254')) {
      return cleaned;
    }
    if (cleaned.startsWith('254')) {
      return `+${cleaned}`;
    }
    if (cleaned.startsWith('0')) {
      return `+254${cleaned.slice(1)}`;
    }
    return `+254${cleaned}`;
  };

  /**
   * Handle form submission.
   */
  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setLocalError(null);
    clearError();

    if (!phoneNumber.trim()) {
      setLocalError('Please enter your phone number');
      return;
    }

    if (!validatePhoneNumber(phoneNumber)) {
      setLocalError('Please enter a valid Kenyan phone number (e.g., 0712345678)');
      return;
    }

    try {
      const formattedPhone = formatPhoneNumber(phoneNumber);
      const response = await login(formattedPhone);
      
      if (response.success) {
        onSuccess?.();
      }
    } catch {
      // Error is handled by context
    }
  };

  const displayError = localError || error;

  return (
    <div className="auth-container">
      <div className="auth-card">
        <div className="auth-header">
          <div className="auth-logo">
            <svg viewBox="0 0 24 24" fill="currentColor" className="shield-icon">
              <path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4zm0 10.99h7c-.53 4.12-3.28 7.79-7 8.94V12H5V6.3l7-3.11v8.8z"/>
            </svg>
          </div>
          <h1 className="auth-title">Rafiki</h1>
          <p className="auth-subtitle">Secure Government Services Assistant</p>
        </div>

        <form onSubmit={handleSubmit} className="auth-form">
          <div className="form-group">
            <label htmlFor="phone" className="form-label">
              Phone Number
            </label>
            <div className="input-wrapper">
              <span className="input-prefix">🇰🇪</span>
              <input
                type="tel"
                id="phone"
                value={phoneNumber}
                onChange={(e) => setPhoneNumber(e.target.value)}
                placeholder="0712 345 678"
                className="form-input"
                disabled={isLoading}
                autoComplete="tel"
                autoFocus
              />
            </div>
            <p className="form-hint">
              Enter your Kenyan mobile number to receive a verification code
            </p>
          </div>

          {displayError && (
            <div className="alert alert-error">
              <svg viewBox="0 0 24 24" fill="currentColor" className="alert-icon">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/>
              </svg>
              <span>{displayError}</span>
            </div>
          )}

          <button
            type="submit"
            className="btn btn-primary btn-full"
            disabled={isLoading}
          >
            {isLoading ? (
              <>
                <span className="spinner" />
                Sending OTP...
              </>
            ) : (
              'Get Verification Code'
            )}
          </button>
        </form>

        <div className="auth-footer">
          <p className="security-notice">
            <svg viewBox="0 0 24 24" fill="currentColor" className="lock-icon">
              <path d="M18 8h-1V6c0-2.76-2.24-5-5-5S7 3.24 7 6v2H6c-1.1 0-2 .9-2 2v10c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V10c0-1.1-.9-2-2-2zm-6 9c-1.1 0-2-.9-2-2s.9-2 2-2 2 .9 2 2-.9 2-2 2zm3.1-9H8.9V6c0-1.71 1.39-3.1 3.1-3.1 1.71 0 3.1 1.39 3.1 3.1v2z"/>
            </svg>
            Your data is protected with government-grade encryption
          </p>
        </div>
      </div>
    </div>
  );
}

export default LoginForm;
