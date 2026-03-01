/**
 * Login Form Component
 * Phone number input for initiating OTP authentication.
 * Supports SMS, Voice Call, or Both delivery methods.
 * Perfectly centered modern glass-morphism design.
 */

import { useState, type FormEvent } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import type { OTPDeliveryMethod } from '../../services/authService';
import { Phone, AlertCircle, Lock, ArrowRight, MessageSquare, PhoneCall, Zap } from 'lucide-react';
import './Auth.css';

interface LoginFormProps {
  onSuccess?: () => void;
}

export function LoginForm({ onSuccess }: LoginFormProps) {
  const { login, isLoading, error, clearError } = useAuth();
  const [phoneNumber, setPhoneNumber] = useState('');
  const [deliveryMethod, setDeliveryMethod] = useState<OTPDeliveryMethod>('both');
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
      const response = await login(formattedPhone, deliveryMethod);
      if (response.success) onSuccess?.();
    } catch {
      // Error handled by context
    }
  };

  const displayError = localError || error;

  return (
    <div className="auth-container" role="main" aria-label="Login page">
      <div className="auth-card">
        {/* Header */}
        <div className="auth-header">
          <div className="auth-logo">
            <div className="auth-logo-icon" aria-hidden="true">🛡️</div>
            <span className="auth-logo-text">Rafiki.ai</span>
          </div>
          <h1 className="auth-title">Karibu Nyumbani 🇰🇪</h1>
          <p className="auth-subtitle">
            Huduma za Serikali kwa <strong>kila</strong> Mkenya.
            <span className="accessibility-note">Sema. Sikiliza. Pata Msaada.</span>
          </p>
          <p className="auth-tagline">
            Government services at your fingertips — just speak!
          </p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="auth-form" aria-label="Phone number login form">
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

          {/* OTP Delivery Method Selection */}
          <div className="form-group">
            <label className="form-label">
              <Zap size={16} />
              Receive OTP via
            </label>
            <div className="delivery-method-group">
              <button
                type="button"
                className={`delivery-option ${deliveryMethod === 'sms' ? 'active' : ''}`}
                onClick={() => setDeliveryMethod('sms')}
                disabled={isLoading}
              >
                <MessageSquare size={20} />
                <span>SMS</span>
              </button>
              <button
                type="button"
                className={`delivery-option ${deliveryMethod === 'voice' ? 'active' : ''}`}
                onClick={() => setDeliveryMethod('voice')}
                disabled={isLoading}
              >
                <PhoneCall size={20} />
                <span>Voice Call</span>
              </button>
              <button
                type="button"
                className={`delivery-option ${deliveryMethod === 'both' ? 'active' : ''}`}
                onClick={() => setDeliveryMethod('both')}
                disabled={isLoading}
              >
                <Zap size={20} />
                <span>Both</span>
              </button>
            </div>
            <p className="delivery-hint">
              {deliveryMethod === 'sms' && '📱 You will receive a text message with your code'}
              {deliveryMethod === 'voice' && '📞 You will receive a phone call with your code'}
              {deliveryMethod === 'both' && '📱📞 You will receive both SMS and a phone call'}
            </p>
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
