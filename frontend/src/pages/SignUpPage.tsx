/**
 * SignUpPage - Rafiki.ai Registration
 * "Savanna at Dawn" themed sign up page
 * Supports OTP verification via SMS, voice, or email
 */

import React, { useState, useCallback, useRef, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { User, Mail, Phone, CreditCard, Lock, Check, AlertCircle, X, RefreshCw } from 'lucide-react';
import { AuthInput, AuthButton, AuthCard } from '../components/Auth/components';
import signupBg from '../assets/signup.png';
import rafikiAvatar from '../assets/rafiki_avatar.png';
import '../styles/auth.css';

const API_BASE = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

interface FormData {
  fullName: string;
  email: string;
  phone: string;
  idNumber: string;
  password: string;
  confirmPassword: string;
  hasDisability: boolean;
  agreeToTerms: boolean;
  otpDelivery: 'sms' | 'voice' | 'email';
}

interface FormErrors {
  fullName?: string;
  email?: string;
  phone?: string;
  idNumber?: string;
  password?: string;
  confirmPassword?: string;
  agreeToTerms?: string;
}

interface OtpState {
  showModal: boolean;
  code: string[];
  expiresIn: number;
  emailMasked: string;
  phoneMasked: string;
  resending: boolean;
  verifying: boolean;
  error: string | null;
}

// Validation helpers
const validateEmail = (email: string): boolean => {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
};

const validatePhone = (phone: string): boolean => {
  return /^(\+?254|0)7\d{8}$/.test(phone.replace(/\s/g, ''));
};

const validateIdNumber = (id: string): boolean => {
  return /^\d{7,8}$/.test(id);
};

const validateName = (name: string): boolean => {
  const words = name.trim().split(/\s+/);
  return words.length >= 2 && /^[a-zA-Z\s'-]+$/.test(name);
};

// Password strength calculator
const getPasswordStrength = (password: string): { level: number; label: string } => {
  if (password.length === 0) return { level: 0, label: '' };
  if (password.length < 8) return { level: 1, label: 'Weak' };
  
  const hasUppercase = /[A-Z]/.test(password);
  const hasNumber = /\d/.test(password);
  const hasSymbol = /[!@#$%^&*(),.?":{}|<>]/.test(password);
  
  if (hasUppercase && hasNumber && hasSymbol) return { level: 4, label: 'Strong' };
  if ((hasUppercase && hasNumber) || (hasUppercase && hasSymbol) || (hasNumber && hasSymbol)) {
    return { level: 3, label: 'Good' };
  }
  return { level: 2, label: 'Fair' };
};

// Password Strength Bar Component
function PasswordStrengthBar({ password }: { password: string }) {
  const { level, label } = getPasswordStrength(password);
  
  if (password.length === 0) return null;
  
  const labelClass = level === 1 ? 'weak' : level === 2 ? 'fair' : level === 3 ? 'good' : 'strong';
  
  return (
    <div>
      <div className="strength-bar">
        {[1, 2, 3, 4].map((segment) => (
          <div
            key={segment}
            className={`strength-segment ${level >= segment ? `active-${level}` : ''}`}
          />
        ))}
      </div>
      <div className={`strength-label ${labelClass}`}>
        {label}
      </div>
    </div>
  );
}

// Custom Checkbox Component
function AuthCheckbox({
  checked,
  onChange,
  label,
  subtext,
  highlighted = false,
  error,
}: {
  checked: boolean;
  onChange: (checked: boolean) => void;
  label: React.ReactNode;
  subtext?: string;
  highlighted?: boolean;
  error?: string;
}) {
  return (
    <div>
      <label className={`auth-checkbox-wrapper ${highlighted && checked ? 'highlighted' : ''}`}>
        <div className="auth-checkbox">
          <input
            type="checkbox"
            checked={checked}
            onChange={(e) => onChange(e.target.checked)}
            aria-invalid={Boolean(error)}
          />
          <div className="auth-checkbox-visual">
            <Check size={14} strokeWidth={3} aria-hidden="true" />
          </div>
        </div>
        <div>
          <div className="auth-checkbox-label">{label}</div>
          {subtext && <div className="auth-checkbox-subtext">{subtext}</div>}
        </div>
      </label>
      {error && (
        <div className="auth-error mt-2" role="alert">
          <AlertCircle size={14} aria-hidden="true" />
          <span>{error}</span>
        </div>
      )}
    </div>
  );
}

export function SignUpPage() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [formData, setFormData] = useState<FormData>({
    fullName: '',
    email: '',
    phone: '',
    idNumber: '',
    password: '',
    confirmPassword: '',
    hasDisability: false,
    agreeToTerms: false,
    otpDelivery: 'sms',
  });
  const [formErrors, setFormErrors] = useState<FormErrors>({});
  const [touched, setTouched] = useState<Set<string>>(new Set());
  
  // OTP verification state
  const [otpState, setOtpState] = useState<OtpState>({
    showModal: false,
    code: ['', '', '', '', '', ''],
    expiresIn: 300,
    emailMasked: '',
    phoneMasked: '',
    resending: false,
    verifying: false,
    error: null,
  });
  const otpInputRefs = useRef<(HTMLInputElement | null)[]>([]);
  
  // OTP timer countdown
  useEffect(() => {
    if (!otpState.showModal || otpState.expiresIn <= 0) return;
    const timer = setInterval(() => {
      setOtpState(prev => ({ ...prev, expiresIn: Math.max(0, prev.expiresIn - 1) }));
    }, 1000);
    return () => clearInterval(timer);
  }, [otpState.showModal, otpState.expiresIn]);

  const updateField = useCallback((field: keyof FormData, value: string | boolean) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    setTouched(prev => new Set(prev).add(field));
    setError(null);
  }, []);

  const validateForm = useCallback((): boolean => {
    const errors: FormErrors = {};

    if (!validateName(formData.fullName)) {
      errors.fullName = 'Please enter your full name as on your National ID';
    }

    if (!validateEmail(formData.email)) {
      errors.email = 'Please enter a valid email address';
    }

    if (!validatePhone(formData.phone)) {
      errors.phone = 'Please enter a valid Kenyan phone number';
    }

    if (!validateIdNumber(formData.idNumber)) {
      errors.idNumber = 'Please enter a valid 7 or 8 digit ID number';
    }

    if (formData.password.length < 8) {
      errors.password = 'Password must be at least 8 characters';
    } else if (!/[A-Z]/.test(formData.password) || !/\d/.test(formData.password)) {
      errors.password = 'Password must contain at least one uppercase letter and one number';
    }

    if (formData.password !== formData.confirmPassword) {
      errors.confirmPassword = 'Passwords do not match';
    }

    if (!formData.agreeToTerms) {
      errors.agreeToTerms = 'You must agree to the terms to continue';
    }

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  }, [formData]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Mark all fields as touched
    setTouched(new Set(['fullName', 'email', 'phone', 'idNumber', 'password', 'confirmPassword', 'agreeToTerms']));

    if (!validateForm()) {
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const res = await fetch(`${API_BASE}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          full_name: formData.fullName,
          email: formData.email,
          phone: formData.phone.replace(/\s/g, ''),
          id_number: formData.idNumber,
          password: formData.password,
          has_disability: formData.hasDisability,
          otp_delivery: formData.otpDelivery,
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        // Handle specific error cases
        if (data.error === 'email_exists') {
          throw new Error('An account with this email already exists');
        } else if (data.error === 'phone_exists') {
          throw new Error('An account with this phone number already exists');
        } else if (data.error === 'id_exists') {
          throw new Error('An account with this ID number already exists');
        }
        throw new Error(data.message || data.detail || 'Registration failed');
      }

      // Show OTP verification modal if required
      if (data.requires_verification) {
        setOtpState({
          showModal: true,
          code: ['', '', '', '', '', ''],
          expiresIn: data.expires_in || 300,
          emailMasked: data.email_masked || '',
          phoneMasked: data.phone_masked || '',
          resending: false,
          verifying: false,
          error: null,
        });
        // Focus first OTP input
        setTimeout(() => otpInputRefs.current[0]?.focus(), 100);
      } else {
        // Direct login (shouldn't happen but handle it)
        localStorage.setItem('rafiki_session_id', data.session_id);
        localStorage.setItem('rafiki_last_user', formData.fullName.split(' ')[0]);
        navigate('/chat');
      }
    } catch (err: any) {
      setError(err.message || 'An error occurred. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // Handle OTP input
  const handleOtpChange = (index: number, value: string) => {
    if (!/^\d*$/.test(value)) return; // Only allow digits
    
    const newCode = [...otpState.code];
    newCode[index] = value.slice(-1); // Only take last character
    setOtpState(prev => ({ ...prev, code: newCode, error: null }));
    
    // Auto-focus next input
    if (value && index < 5) {
      otpInputRefs.current[index + 1]?.focus();
    }
  };

  const handleOtpKeyDown = (index: number, e: React.KeyboardEvent) => {
    if (e.key === 'Backspace' && !otpState.code[index] && index > 0) {
      otpInputRefs.current[index - 1]?.focus();
    }
  };

  const handleOtpPaste = (e: React.ClipboardEvent) => {
    e.preventDefault();
    const pastedData = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6);
    if (pastedData.length === 6) {
      const newCode = pastedData.split('');
      setOtpState(prev => ({ ...prev, code: newCode, error: null }));
      otpInputRefs.current[5]?.focus();
    }
  };

  // Verify OTP
  const handleVerifyOtp = async () => {
    const otp = otpState.code.join('');
    if (otp.length !== 6) {
      setOtpState(prev => ({ ...prev, error: 'Please enter all 6 digits' }));
      return;
    }

    setOtpState(prev => ({ ...prev, verifying: true, error: null }));

    try {
      const res = await fetch(`${API_BASE}/auth/verify-registration`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: formData.email,
          phone: formData.phone.replace(/\s/g, ''),
          otp: otp,
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.message || data.detail || 'Verification failed');
      }

      // Success - store session and redirect
      localStorage.setItem('rafiki_session_id', data.session_id);
      localStorage.setItem('rafiki_token', data.access_token);
      localStorage.setItem('rafiki_last_user', formData.fullName.split(' ')[0]);
      navigate('/chat');
    } catch (err: any) {
      setOtpState(prev => ({ 
        ...prev, 
        verifying: false, 
        error: err.message || 'Invalid OTP. Please try again.' 
      }));
    }
  };

  // Resend OTP
  const handleResendOtp = async (method: 'sms' | 'voice' | 'email') => {
    setOtpState(prev => ({ ...prev, resending: true, error: null }));

    try {
      const res = await fetch(`${API_BASE}/auth/resend-otp`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: formData.email,
          phone: formData.phone.replace(/\s/g, ''),
          delivery_method: method,
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.message || data.detail || 'Failed to resend OTP');
      }

      // Reset code and timer
      setOtpState(prev => ({ 
        ...prev, 
        code: ['', '', '', '', '', ''],
        expiresIn: data.expires_in || 300,
        resending: false,
      }));
      otpInputRefs.current[0]?.focus();
    } catch (err: any) {
      setOtpState(prev => ({ 
        ...prev, 
        resending: false, 
        error: err.message || 'Failed to resend OTP' 
      }));
    }
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const handleGoogleSignUp = () => {
    // TODO: Implement Google OAuth
    window.location.href = `${API_BASE}/auth/google`;
  };

  return (
    <div className="auth-page">
      {/* Background Panel - Desktop */}
      <div className="auth-bg-panel">
        <img
          src={signupBg}
          alt=""
          className="auth-bg-image absolute inset-0 w-full h-full object-cover"
        />
        <div className="auth-bg-overlay" />
        <div className="auth-bg-content">
          <img
            src={rafikiAvatar}
            alt=""
            className="rafiki-glow w-20 h-20 mb-6"
            aria-hidden="true"
          />
          <h1 className="font-playfair text-4xl lg:text-5xl text-white leading-tight mb-2">
            Your Government.
          </h1>
          <h2 className="font-playfair text-4xl lg:text-5xl leading-tight mb-4" style={{ color: '#C8860A' }}>
            Made Simple.
          </h2>
          <p className="font-dm-sans text-base text-white/70 max-w-md">
            Access all Kenyan government services from one place.
          </p>
        </div>
      </div>

      {/* Mobile Background */}
      <div className="auth-mobile-bg lg:hidden">
        <img src={signupBg} alt="" className="w-full h-full object-cover" />
        <div className="auth-mobile-overlay" />
      </div>

      {/* Form Panel */}
      <div className="auth-form-panel">
        <AuthCard>
          <form onSubmit={handleSubmit} noValidate>
            {/* Header */}
            <div className="text-center mb-8 fade-up">
              <img
                src={rafikiAvatar}
                alt="Rafiki AI"
                className="rafiki-glow-subtle w-12 h-12 mx-auto mb-4"
              />
              <h1 className="font-playfair text-2xl md:text-3xl text-gray-900 mb-2">
                Create your account
              </h1>
              <p className="font-dm-sans text-sm text-gray-500">
                Join thousands of Kenyans accessing government services online
              </p>
            </div>

            {/* Error Banner */}
            {error && (
              <div className="auth-error-banner mb-6 fade-up" role="alert">
                <AlertCircle size={20} aria-hidden="true" />
                <span>{error}</span>
              </div>
            )}

            {/* Form Fields */}
            <div className="space-y-5">
              {/* Full Name */}
              <div className="fade-up fade-up-delay-1">
                <AuthInput
                  label="Full Name"
                  placeholder="As it appears on your National ID"
                  icon={<User size={20} aria-hidden="true" />}
                  value={formData.fullName}
                  onChange={(v) => updateField('fullName', v)}
                  error={touched.has('fullName') ? formErrors.fullName : undefined}
                  autoComplete="name"
                  required
                />
              </div>

              {/* Email */}
              <div className="fade-up fade-up-delay-2">
                <AuthInput
                  label="Email Address"
                  placeholder="yourname@email.com"
                  type="email"
                  icon={<Mail size={20} aria-hidden="true" />}
                  value={formData.email}
                  onChange={(v) => updateField('email', v)}
                  error={touched.has('email') ? formErrors.email : undefined}
                  autoComplete="email"
                  required
                />
              </div>

              {/* Phone */}
              <div className="fade-up fade-up-delay-3">
                <AuthInput
                  label="Phone Number"
                  placeholder="07XX XXX XXX"
                  type="tel"
                  icon={<Phone size={20} aria-hidden="true" />}
                  value={formData.phone}
                  onChange={(v) => updateField('phone', v)}
                  error={touched.has('phone') ? formErrors.phone : undefined}
                  autoComplete="tel"
                  required
                />
              </div>

              {/* National ID */}
              <div className="fade-up fade-up-delay-4">
                <AuthInput
                  label="National ID Number"
                  placeholder="7 or 8 digit ID number"
                  icon={<CreditCard size={20} aria-hidden="true" />}
                  value={formData.idNumber}
                  onChange={(v) => updateField('idNumber', v)}
                  error={touched.has('idNumber') ? formErrors.idNumber : undefined}
                  autoComplete="off"
                  required
                />
              </div>

              {/* Password */}
              <div className="fade-up fade-up-delay-5">
                <AuthInput
                  label="Password"
                  placeholder="Create a strong password"
                  icon={<Lock size={20} aria-hidden="true" />}
                  value={formData.password}
                  onChange={(v) => updateField('password', v)}
                  error={touched.has('password') ? formErrors.password : undefined}
                  showPasswordToggle
                  autoComplete="new-password"
                  required
                />
                <PasswordStrengthBar password={formData.password} />
              </div>

              {/* Confirm Password */}
              <div className="fade-up fade-up-delay-6">
                <AuthInput
                  label="Confirm Password"
                  placeholder="Re-enter your password"
                  icon={<Lock size={20} aria-hidden="true" />}
                  value={formData.confirmPassword}
                  onChange={(v) => updateField('confirmPassword', v)}
                  error={touched.has('confirmPassword') ? formErrors.confirmPassword : undefined}
                  showPasswordToggle
                  autoComplete="new-password"
                  required
                />
              </div>

              {/* Disability Checkbox */}
              <div className="fade-up fade-up-delay-7 pt-2">
                <AuthCheckbox
                  checked={formData.hasDisability}
                  onChange={(v) => updateField('hasDisability', v)}
                  label="I am a person living with disabilities (PWD)"
                  subtext="This helps us provide tailored assistance for your needs"
                  highlighted
                />
              </div>

              {/* Terms Checkbox */}
              <div className="fade-up fade-up-delay-8">
                <AuthCheckbox
                  checked={formData.agreeToTerms}
                  onChange={(v) => updateField('agreeToTerms', v)}
                  label={
                    <>
                      I agree to the{' '}
                      <a href="#" onClick={(e) => e.preventDefault()}>Terms of Service</a>
                      {' '}and{' '}
                      <a href="#" onClick={(e) => e.preventDefault()}>Privacy Policy</a>
                    </>
                  }
                  error={touched.has('agreeToTerms') ? formErrors.agreeToTerms : undefined}
                />
              </div>

              {/* Submit Button */}
              <div className="fade-up fade-up-delay-9 pt-2">
                <AuthButton
                  type="submit"
                  variant="primary"
                  fullWidth
                  loading={loading}
                >
                  Create Account
                </AuthButton>
              </div>

              {/* Divider */}
              <div className="auth-divider fade-up fade-up-delay-10">
                <div className="auth-divider-line" />
                <span className="auth-divider-text">or sign up with</span>
                <div className="auth-divider-line" />
              </div>

              {/* Google Button */}
              <div className="fade-up fade-up-delay-10">
                <AuthButton
                  variant="google"
                  fullWidth
                  onClick={handleGoogleSignUp}
                >
                  Continue with Google
                </AuthButton>
              </div>

              {/* Footer Link */}
              <div className="text-center pt-4 fade-up fade-up-delay-10">
                <p className="font-dm-sans text-sm text-gray-600">
                  Already have an account?{' '}
                  <Link to="/login" className="auth-link">
                    Sign in
                  </Link>
                </p>
              </div>
            </div>
          </form>
        </AuthCard>
      </div>

      {/* OTP Verification Modal */}
      {otpState.showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
          <div className="relative w-full max-w-md bg-white rounded-2xl shadow-2xl p-8">
            {/* Close Button */}
            <button
              type="button"
              onClick={() => setOtpState(prev => ({ ...prev, showModal: false }))}
              className="absolute top-4 right-4 p-2 rounded-full hover:bg-gray-100 transition-colors"
              aria-label="Close"
            >
              <X size={20} className="text-gray-500" />
            </button>

            {/* Header */}
            <div className="text-center mb-6">
              <div className="w-16 h-16 bg-gradient-to-r from-amber-400 to-amber-600 rounded-full flex items-center justify-center mx-auto mb-4">
                <Lock size={28} className="text-white" />
              </div>
              <h3 className="font-playfair text-2xl text-gray-900 mb-2">Verify Your Account</h3>
              <p className="font-dm-sans text-gray-600 text-sm">
                We sent a 6-digit code to{' '}
                <span className="font-medium">{otpState.phoneMasked}</span>
                {otpState.emailMasked && (
                  <> and <span className="font-medium">{otpState.emailMasked}</span></>
                )}
              </p>
            </div>

            {/* OTP Input */}
            <div className="flex justify-center gap-2 mb-6" onPaste={handleOtpPaste}>
              {otpState.code.map((digit, index) => (
                <input
                  key={index}
                  ref={(el) => { otpInputRefs.current[index] = el; }}
                  type="text"
                  inputMode="numeric"
                  maxLength={1}
                  value={digit}
                  onChange={(e) => handleOtpChange(index, e.target.value)}
                  onKeyDown={(e) => handleOtpKeyDown(index, e)}
                  className="w-12 h-14 text-center text-2xl font-bold border-2 rounded-xl 
                    focus:border-amber-500 focus:ring-2 focus:ring-amber-200 outline-none
                    transition-all text-gray-900"
                  aria-label={`Digit ${index + 1}`}
                />
              ))}
            </div>

            {/* Timer */}
            <div className="text-center mb-4">
              {otpState.expiresIn > 0 ? (
                <p className="font-dm-sans text-sm text-gray-500">
                  Code expires in <span className="font-medium text-amber-600">{formatTime(otpState.expiresIn)}</span>
                </p>
              ) : (
                <p className="font-dm-sans text-sm text-red-500">
                  Code expired. Please request a new one.
                </p>
              )}
            </div>

            {/* Error */}
            {otpState.error && (
              <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2">
                <AlertCircle size={18} className="text-red-500 flex-shrink-0" />
                <span className="font-dm-sans text-sm text-red-700">{otpState.error}</span>
              </div>
            )}

            {/* Verify Button */}
            <AuthButton
              variant="primary"
              fullWidth
              onClick={handleVerifyOtp}
              loading={otpState.verifying}
              disabled={otpState.code.join('').length !== 6 || otpState.expiresIn <= 0}
            >
              Verify & Continue
            </AuthButton>

            {/* Resend Options */}
            <div className="mt-6 pt-4 border-t border-gray-100">
              <p className="font-dm-sans text-sm text-gray-500 text-center mb-3">
                Didn't receive the code?
              </p>
              <div className="flex justify-center gap-2 flex-wrap">
                <button
                  type="button"
                  onClick={() => handleResendOtp('sms')}
                  disabled={otpState.resending}
                  className="inline-flex items-center gap-1 px-3 py-1.5 text-sm font-medium 
                    text-amber-600 hover:text-amber-700 hover:bg-amber-50 rounded-lg 
                    transition-colors disabled:opacity-50"
                >
                  {otpState.resending ? <RefreshCw size={14} className="animate-spin" /> : <Phone size={14} />}
                  SMS
                </button>
                <button
                  type="button"
                  onClick={() => handleResendOtp('voice')}
                  disabled={otpState.resending}
                  className="inline-flex items-center gap-1 px-3 py-1.5 text-sm font-medium 
                    text-amber-600 hover:text-amber-700 hover:bg-amber-50 rounded-lg 
                    transition-colors disabled:opacity-50"
                >
                  {otpState.resending ? <RefreshCw size={14} className="animate-spin" /> : null}
                  📞 Voice Call
                </button>
                <button
                  type="button"
                  onClick={() => handleResendOtp('email')}
                  disabled={otpState.resending}
                  className="inline-flex items-center gap-1 px-3 py-1.5 text-sm font-medium 
                    text-amber-600 hover:text-amber-700 hover:bg-amber-50 rounded-lg 
                    transition-colors disabled:opacity-50"
                >
                  {otpState.resending ? <RefreshCw size={14} className="animate-spin" /> : <Mail size={14} />}
                  Email
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default SignUpPage;
