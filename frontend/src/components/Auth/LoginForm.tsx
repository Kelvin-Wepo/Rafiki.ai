/**
 * Login Form Component
 * Phone number input for initiating OTP authentication.
 * Perfectly centered modern glass-morphism design.
 */

import { useState, type FormEvent } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { Phone, AlertCircle, Lock, ArrowRight } from 'lucide-react';
import './Auth.css';

interface LoginFormProps {
  onSuccess?: () => void;
}

export function LoginForm({ onSuccess }: LoginFormProps) {
  const { login, isLoading, error, clearError } = useAuth();
  const [phoneNumber, setPhoneNumber] = useState('');
  const [localError, setLocalError] = useState<string | null>(null);

  const validatePhoneNumber = (phone: string): boolean => {
    const cleaned = phone.replace(/[\s-]/g, '');
    const patterns = [/^\+254\d{9}$/, /^254\d{9}$/, /^0\d{9}$/];
    return patterns.some(pattern => pattern.test(cleaned));
  };

  const formatPhoneNumber = (phone: string): string => {
    const cleaned = phone.replace(/[\s-]/g, '');
    if (cleaned.startsWith('+254')) return cleaned;
    if (cleaned.startsWith('254')) return `+${cleaned}`;
    if (cleaned.startsWith('0')) return `+254${cleaned.slice(1)}`;
    return `+254${cleaned}`;
  };

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
      if (response.success) onSuccess?.();
    } catch {
      // Error handled by context
    }
  };

  const displayError = localError || error;

  return (
    <div className="auth-container">
      <div className="auth-card">
        {/* Header */}
        <div className="auth-header">
          <div className="auth-logo">
            <div className="auth-logo-icon">🛡️</div>
            <span className="auth-logo-text">Rafiki.ai</span>
          </div>
          <h1 className="auth-title">Welcome Back</h1>
          <p className="auth-subtitle">
            Sign in to access government services with your verified phone number
          </p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="auth-form">
          <div className="form-group">
            <label htmlFor="phone" className="form-label">
              <Phone size={16} />
              Phone Number
            </label>
            <div className="phone-input-group">
              <div className="country-code">
                <span className="flag">🇰🇪</span>
                <span>+254</span>
              </div>
              <input
                type="tel"
                id="phone"
                value={phoneNumber}
                onChange={(e) => setPhoneNumber(e.target.value)}
                placeholder="712 345 678"
                className={`form-input ${displayError ? 'error' : ''}`}
                disabled={isLoading}
                autoComplete="tel"
                autoFocus
              />
            </div>
          </div>

          {/* Error Message */}
          {displayError && (
            <div className="auth-error">
              <AlertCircle size={18} />
              <span>{displayError}</span>
            </div>
          )}

          {/* Submit Button */}
          <button type="submit" className="auth-button" disabled={isLoading}>
            {isLoading ? (
              <>
                <span className="spinner" />
                <span>Sending OTP...</span>
              </>
            ) : (
              <>
                <span>Continue</span>
                <ArrowRight size={18} />
              </>
            )}
          </button>
        </form>

        {/* Footer */}
        <div className="auth-footer">
          <p className="auth-footer-text">
            <Lock size={14} style={{ display: 'inline', verticalAlign: 'middle', marginRight: '6px' }} />
            Your data is protected with end-to-end encryption
          </p>
        </div>
      </div>
    </div>
  );
}

export default LoginForm;
