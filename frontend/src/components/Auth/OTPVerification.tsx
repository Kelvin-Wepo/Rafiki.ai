/**
 * OTP Verification Component
 * 6-digit OTP input for completing authentication.
 * Perfectly centered modern glass-morphism design.
 */

import { useState, useRef, useEffect, type FormEvent, type KeyboardEvent, type ClipboardEvent } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { ArrowLeft, AlertCircle, Shield, CheckCircle } from 'lucide-react';
import './Auth.css';

interface OTPVerificationProps {
  onSuccess?: () => void;
  onBack?: () => void;
}

const OTP_LENGTH = 6;
const RESEND_COOLDOWN = 60;

export function OTPVerification({ onSuccess, onBack }: OTPVerificationProps) {
  const { verify, login, pendingPhone, isLoading, error, clearError, setIsVerifying, lastDeliveryMethod } = useAuth();
  
  const [otp, setOtp] = useState<string[]>(Array(OTP_LENGTH).fill(''));
  const [localError, setLocalError] = useState<string | null>(null);
  const [resendCooldown, setResendCooldown] = useState(RESEND_COOLDOWN);
  const [isResending, setIsResending] = useState(false);
  
  const inputRefs = useRef<(HTMLInputElement | null)[]>([]);

  useEffect(() => {
    if (resendCooldown > 0) {
      const timer = setTimeout(() => setResendCooldown(prev => prev - 1), 1000);
      return () => clearTimeout(timer);
    }
  }, [resendCooldown]);

  useEffect(() => {
    inputRefs.current[0]?.focus();
  }, []);

  const handleChange = (index: number, value: string) => {
    if (value && !/^\d$/.test(value)) return;

    const newOtp = [...otp];
    newOtp[index] = value;
    setOtp(newOtp);
    setLocalError(null);
    clearError();

    if (value && index < OTP_LENGTH - 1) {
      inputRefs.current[index + 1]?.focus();
    }

    if (value && index === OTP_LENGTH - 1) {
      const fullOtp = newOtp.join('');
      if (fullOtp.length === OTP_LENGTH) handleVerify(fullOtp);
    }
  };

  const handleKeyDown = (index: number, e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Backspace' && !otp[index] && index > 0) {
      inputRefs.current[index - 1]?.focus();
    }
  };

  const handlePaste = (e: ClipboardEvent<HTMLInputElement>) => {
    e.preventDefault();
    const pastedData = e.clipboardData.getData('text').replace(/\D/g, '');
    
    if (pastedData.length > 0) {
      const newOtp = [...otp];
      for (let i = 0; i < Math.min(pastedData.length, OTP_LENGTH); i++) {
        newOtp[i] = pastedData[i];
      }
      setOtp(newOtp);
      
      const lastIndex = Math.min(pastedData.length - 1, OTP_LENGTH - 1);
      inputRefs.current[lastIndex]?.focus();

      if (pastedData.length >= OTP_LENGTH) handleVerify(newOtp.join(''));
    }
  };

  const handleVerify = async (otpCode: string) => {
    if (!pendingPhone) {
      setLocalError('Session expired. Please start over.');
      return;
    }

    if (otpCode.length !== OTP_LENGTH) {
      setLocalError('Please enter all 6 digits');
      return;
    }

    try {
      const response = await verify(pendingPhone, otpCode);
      if (response.success) onSuccess?.();
    } catch {
      setOtp(Array(OTP_LENGTH).fill(''));
      inputRefs.current[0]?.focus();
    }
  };

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    handleVerify(otp.join(''));
  };

  const handleResend = async () => {
    if (!pendingPhone || resendCooldown > 0) return;
    
    setIsResending(true);
    setLocalError(null);
    clearError();
    
    try {
      await login(pendingPhone, lastDeliveryMethod || 'both');
      setResendCooldown(RESEND_COOLDOWN);
      setOtp(Array(OTP_LENGTH).fill(''));
      inputRefs.current[0]?.focus();
    } catch {
      setLocalError('Failed to resend OTP. Please try again.');
    } finally {
      setIsResending(false);
    }
  };

  const handleBack = () => {
    setIsVerifying(false);
    onBack?.();
  };

  const displayError = localError || error;
  const maskedPhone = pendingPhone
    ? pendingPhone.replace(/(\+\d{3})(\d{3})(\d{3})(\d{3})/, '$1 *** *** $4')
    : '***';

  return (
    <div className="auth-container">
      <div className="auth-card">
        {/* Back Button */}
        <button 
          type="button" 
          className="auth-button-secondary"
          onClick={handleBack}
          disabled={isLoading}
          style={{ marginBottom: '1.5rem' }}
        >
          <ArrowLeft size={18} />
          Back to Login
        </button>

        {/* Header */}
        <div className="auth-header">
          <div className="auth-logo">
            <div className="auth-logo-icon">
              {lastDeliveryMethod === 'voice' ? '📞' : lastDeliveryMethod === 'sms' ? '📱' : '📱📞'}
            </div>
          </div>
          <h1 className="auth-title">Verify Your Phone</h1>
          <p className="auth-subtitle">
            {lastDeliveryMethod === 'voice' 
              ? 'Listen to the voice call for your code' 
              : lastDeliveryMethod === 'sms' 
              ? 'Enter the 6-digit code from SMS'
              : 'Enter the 6-digit code from SMS or voice call'}
          </p>
        </div>

        {/* Phone Info Box */}
        <div className="otp-info">
          <div className="otp-info-title">Code sent to</div>
          <div className="otp-info-phone">{maskedPhone}</div>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="auth-form">
          {/* OTP Inputs */}
          <div className="otp-input-group">
            {otp.map((digit, index) => (
              <input
                key={index}
                ref={el => { inputRefs.current[index] = el }}
                type="text"
                inputMode="numeric"
                maxLength={1}
                value={digit}
                onChange={(e) => handleChange(index, e.target.value)}
                onKeyDown={(e) => handleKeyDown(index, e)}
                onPaste={index === 0 ? handlePaste : undefined}
                className={`otp-input ${digit ? 'filled' : ''} ${displayError ? 'error' : ''}`}
                disabled={isLoading}
                autoComplete="one-time-code"
              />
            ))}
          </div>

          {/* Error Message */}
          {displayError && (
            <div className="auth-error">
              <AlertCircle size={18} />
              <span>{displayError}</span>
            </div>
          )}

          {/* Submit Button */}
          <button
            type="submit"
            className="auth-button"
            disabled={isLoading || otp.join('').length !== OTP_LENGTH}
          >
            {isLoading ? (
              <>
                <span className="spinner" />
                <span>Verifying...</span>
              </>
            ) : (
              <>
                <CheckCircle size={18} />
                <span>Verify & Login</span>
              </>
            )}
          </button>

          {/* Resend Section */}
          <div className="resend-section">
            {resendCooldown > 0 ? (
              <p className="resend-timer">
                Resend code in <strong>{resendCooldown}s</strong>
              </p>
            ) : (
              <button
                type="button"
                className="auth-link"
                onClick={handleResend}
                disabled={isResending}
              >
                {isResending ? 'Sending...' : "Didn't receive code? Resend"}
              </button>
            )}
          </div>
        </form>

        {/* Footer */}
        <div className="auth-footer">
          <p className="auth-footer-text">
            <Shield size={14} style={{ display: 'inline', verticalAlign: 'middle', marginRight: '6px' }} />
            OTP expires in 5 minutes
          </p>
        </div>
      </div>
    </div>
  );
}

export default OTPVerification;
