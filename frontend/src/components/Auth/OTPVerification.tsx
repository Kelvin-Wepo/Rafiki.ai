/**
 * OTP Verification Component
 * 6-digit OTP input for completing authentication.
 * 
 * Features:
 * - 6 individual digit inputs with auto-focus
 * - Paste support for OTP
 * - Resend functionality with cooldown
 * - Countdown timer
 * - Error display
 */

import { useState, useRef, useEffect, type FormEvent, type KeyboardEvent, type ClipboardEvent } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import './Auth.css';

interface OTPVerificationProps {
  onSuccess?: () => void;
  onBack?: () => void;
}

const OTP_LENGTH = 6;
const RESEND_COOLDOWN = 60; // seconds

export function OTPVerification({ onSuccess, onBack }: OTPVerificationProps) {
  const { verify, login, pendingPhone, isLoading, error, clearError, setIsVerifying } = useAuth();
  
  const [otp, setOtp] = useState<string[]>(Array(OTP_LENGTH).fill(''));
  const [localError, setLocalError] = useState<string | null>(null);
  const [resendCooldown, setResendCooldown] = useState(RESEND_COOLDOWN);
  const [isResending, setIsResending] = useState(false);
  
  const inputRefs = useRef<(HTMLInputElement | null)[]>([]);

  // Cooldown timer for resend
  useEffect(() => {
    if (resendCooldown > 0) {
      const timer = setTimeout(() => {
        setResendCooldown(prev => prev - 1);
      }, 1000);
      return () => clearTimeout(timer);
    }
  }, [resendCooldown]);

  // Focus first input on mount
  useEffect(() => {
    inputRefs.current[0]?.focus();
  }, []);

  /**
   * Handle single digit input.
   */
  const handleChange = (index: number, value: string) => {
    // Only allow digits
    if (value && !/^\d$/.test(value)) return;

    const newOtp = [...otp];
    newOtp[index] = value;
    setOtp(newOtp);
    setLocalError(null);
    clearError();

    // Auto-focus next input
    if (value && index < OTP_LENGTH - 1) {
      inputRefs.current[index + 1]?.focus();
    }

    // Auto-submit when complete
    if (value && index === OTP_LENGTH - 1) {
      const fullOtp = newOtp.join('');
      if (fullOtp.length === OTP_LENGTH) {
        handleVerify(fullOtp);
      }
    }
  };

  /**
   * Handle backspace navigation.
   */
  const handleKeyDown = (index: number, e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Backspace' && !otp[index] && index > 0) {
      inputRefs.current[index - 1]?.focus();
    }
  };

  /**
   * Handle paste event.
   */
  const handlePaste = (e: ClipboardEvent<HTMLInputElement>) => {
    e.preventDefault();
    const pastedData = e.clipboardData.getData('text').replace(/\D/g, '');
    
    if (pastedData.length > 0) {
      const newOtp = [...otp];
      for (let i = 0; i < Math.min(pastedData.length, OTP_LENGTH); i++) {
        newOtp[i] = pastedData[i];
      }
      setOtp(newOtp);
      
      // Focus last filled input or last input
      const lastIndex = Math.min(pastedData.length - 1, OTP_LENGTH - 1);
      inputRefs.current[lastIndex]?.focus();

      // Auto-submit if complete
      if (pastedData.length >= OTP_LENGTH) {
        handleVerify(newOtp.join(''));
      }
    }
  };

  /**
   * Verify OTP with backend.
   */
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
      
      if (response.success) {
        onSuccess?.();
      }
    } catch {
      // Clear OTP on error
      setOtp(Array(OTP_LENGTH).fill(''));
      inputRefs.current[0]?.focus();
    }
  };

  /**
   * Handle form submission.
   */
  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    handleVerify(otp.join(''));
  };

  /**
   * Resend OTP.
   */
  const handleResend = async () => {
    if (!pendingPhone || resendCooldown > 0) return;
    
    setIsResending(true);
    setLocalError(null);
    clearError();
    
    try {
      await login(pendingPhone);
      setResendCooldown(RESEND_COOLDOWN);
      setOtp(Array(OTP_LENGTH).fill(''));
      inputRefs.current[0]?.focus();
    } catch {
      setLocalError('Failed to resend OTP. Please try again.');
    } finally {
      setIsResending(false);
    }
  };

  /**
   * Go back to phone input.
   */
  const handleBack = () => {
    setIsVerifying(false);
    onBack?.();
  };

  const displayError = localError || error;

  // Mask phone number for display
  const maskedPhone = pendingPhone
    ? pendingPhone.replace(/(\+\d{3})(\d{3})(\d{3})(\d{3})/, '$1 *** *** $4')
    : '***';

  return (
    <div className="auth-container">
      <div className="auth-card">
        <button 
          type="button" 
          className="back-button"
          onClick={handleBack}
          disabled={isLoading}
        >
          <svg viewBox="0 0 24 24" fill="currentColor">
            <path d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z"/>
          </svg>
          Back
        </button>

        <div className="auth-header">
          <div className="auth-logo otp-logo">
            <svg viewBox="0 0 24 24" fill="currentColor" className="message-icon">
              <path d="M20 2H4c-1.1 0-1.99.9-1.99 2L2 22l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm-7 12h-2v-2h2v2zm0-4h-2V6h2v4z"/>
            </svg>
          </div>
          <h1 className="auth-title">Enter Verification Code</h1>
          <p className="auth-subtitle">
            We sent a 6-digit code to<br />
            <strong>{maskedPhone}</strong>
          </p>
        </div>

        <form onSubmit={handleSubmit} className="auth-form">
          <div className="otp-inputs">
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
                className={`otp-input ${digit ? 'filled' : ''}`}
                disabled={isLoading}
                autoComplete="one-time-code"
              />
            ))}
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
            disabled={isLoading || otp.join('').length !== OTP_LENGTH}
          >
            {isLoading ? (
              <>
                <span className="spinner" />
                Verifying...
              </>
            ) : (
              'Verify & Login'
            )}
          </button>

          <div className="resend-section">
            {resendCooldown > 0 ? (
              <p className="resend-timer">
                Resend code in <strong>{resendCooldown}s</strong>
              </p>
            ) : (
              <button
                type="button"
                className="btn btn-link"
                onClick={handleResend}
                disabled={isResending}
              >
                {isResending ? 'Sending...' : "Didn't receive code? Resend"}
              </button>
            )}
          </div>
        </form>

        <div className="auth-footer">
          <p className="security-notice">
            <svg viewBox="0 0 24 24" fill="currentColor" className="lock-icon">
              <path d="M18 8h-1V6c0-2.76-2.24-5-5-5S7 3.24 7 6v2H6c-1.1 0-2 .9-2 2v10c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V10c0-1.1-.9-2-2-2zm-6 9c-1.1 0-2-.9-2-2s.9-2 2-2 2 .9 2 2-.9 2-2 2zm3.1-9H8.9V6c0-1.71 1.39-3.1 3.1-3.1 1.71 0 3.1 1.39 3.1 3.1v2z"/>
            </svg>
            OTP expires in 5 minutes
          </p>
        </div>
      </div>
    </div>
  );
}

export default OTPVerification;
