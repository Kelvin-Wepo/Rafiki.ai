/**
 * SignUpPage - Rafiki.ai Registration
 * Supports OTP verification via SMS, voice, or email.
 */

import React, { useState, useCallback, useRef, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  User,
  Mail,
  Phone,
  CreditCard,
  Lock,
  Check,
  AlertCircle,
  X,
  RefreshCw,
  ShieldCheck,
  Landmark,
  Sparkles,
} from 'lucide-react';
import { AuthInput, AuthButton, AuthCard } from '../components/Auth/components';
import { useAuth } from '../contexts/AuthContext';
import signupBg from '../assets/signup.png';
import rafikiAvatar from '../assets/rafiki_avatar.png';
import '../styles/auth.css';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

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

const validateEmail = (email: string): boolean => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
const validatePhone = (phone: string): boolean => /^(\+?254|0)7\d{8}$/.test(phone.replace(/\s/g, ''));
const validateIdNumber = (id: string): boolean => /^\d{7,8}$/.test(id);
const validateName = (name: string): boolean => {
  const words = name.trim().split(/\s+/);
  return words.length >= 2 && /^[a-zA-Z\s'-]+$/.test(name);
};

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
      <div className={`strength-label ${labelClass}`}>{label}</div>
    </div>
  );
}

function AuthCheckbox({
  checked,
  onChange,
  label,
  subtext,
  highlighted = false,
  error,
  inputRef,
}: {
  checked: boolean;
  onChange: (checked: boolean) => void;
  label: React.ReactNode;
  subtext?: string;
  highlighted?: boolean;
  error?: string;
  inputRef?: React.Ref<HTMLInputElement>;
}) {
  return (
    <div>
      <label className={`auth-checkbox-wrapper ${highlighted && checked ? 'highlighted' : ''}`}>
        <div className="auth-checkbox">
          <input
            ref={inputRef}
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
  const { completeSession, completeAuth } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [ecitizenNotice, setEcitizenNotice] = useState(false);
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

  const fieldRefs = {
    fullName: useRef<HTMLInputElement>(null),
    email: useRef<HTMLInputElement>(null),
    phone: useRef<HTMLInputElement>(null),
    idNumber: useRef<HTMLInputElement>(null),
    password: useRef<HTMLInputElement>(null),
    confirmPassword: useRef<HTMLInputElement>(null),
    agreeToTerms: useRef<HTMLInputElement>(null),
  };
  const errorBannerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (error) errorBannerRef.current?.focus();
  }, [error]);

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

  const validateForm = useCallback((): FormErrors => {
    const errors: FormErrors = {};

    if (!validateName(formData.fullName)) errors.fullName = 'Please enter your full name as on your National ID';
    if (!validateEmail(formData.email)) errors.email = 'Please enter a valid email address';
    if (!validatePhone(formData.phone)) errors.phone = 'Please enter a valid Kenyan phone number';
    if (!validateIdNumber(formData.idNumber)) errors.idNumber = 'Please enter a valid 7 or 8 digit ID number';
    if (formData.password.length < 8) errors.password = 'Password must be at least 8 characters';
    else if (!/[A-Z]/.test(formData.password) || !/\d/.test(formData.password)) {
      errors.password = 'Password must contain at least one uppercase letter and one number';
    }
    if (formData.password !== formData.confirmPassword) errors.confirmPassword = 'Passwords do not match';
    if (!formData.agreeToTerms) errors.agreeToTerms = 'You must agree to the terms to continue';

    setFormErrors(errors);
    return errors;
  }, [formData]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setTouched(new Set(['fullName', 'email', 'phone', 'idNumber', 'password', 'confirmPassword', 'agreeToTerms']));

    const errors = validateForm();
    if (Object.keys(errors).length > 0) {
      const fieldOrder = ['fullName', 'email', 'phone', 'idNumber', 'password', 'confirmPassword', 'agreeToTerms'] as const;
      const firstInvalid = fieldOrder.find((f) => errors[f]);
      if (firstInvalid) fieldRefs[firstInvalid].current?.focus();
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
        if (data.error === 'email_exists') throw new Error('An account with this email already exists');
        if (data.error === 'phone_exists') throw new Error('An account with this phone number already exists');
        if (data.error === 'id_exists') throw new Error('An account with this ID number already exists');
        throw new Error(data.message || data.detail || 'Registration failed');
      }

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
        setTimeout(() => otpInputRefs.current[0]?.focus(), 100);
      } else {
        localStorage.setItem('rafiki_session_id', data.session_id);
        localStorage.setItem('rafiki_last_user', formData.fullName.split(' ')[0]);
        completeAuth(data.user ?? null);
        navigate('/chat');
      }
    } catch (err) {
      setError(err instanceof Error && err.message ? err.message : 'An error occurred. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleOtpChange = (index: number, value: string) => {
    if (!/^\d*$/.test(value)) return;
    const newCode = [...otpState.code];
    newCode[index] = value.slice(-1);
    setOtpState(prev => ({ ...prev, code: newCode, error: null }));
    if (value && index < 5) otpInputRefs.current[index + 1]?.focus();
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
          otp,
        }),
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.message || data.detail || 'Verification failed');

      completeSession(data.user || { full_name: formData.fullName }, data.access_token, data.session_id);
      localStorage.setItem('rafiki_last_user', formData.fullName.split(' ')[0]);
      completeAuth(data.user ?? null);
      navigate('/chat');
    } catch (err) {
      setOtpState(prev => ({
        ...prev,
        verifying: false,
        error: err instanceof Error && err.message ? err.message : 'Invalid OTP. Please try again.',
      }));
    }
  };

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
      if (!res.ok) throw new Error(data.message || data.detail || 'Failed to resend OTP');

      setOtpState(prev => ({
        ...prev,
        code: ['', '', '', '', '', ''],
        expiresIn: data.expires_in || 300,
        resending: false,
      }));
      otpInputRefs.current[0]?.focus();
    } catch (err) {
      setOtpState(prev => ({
        ...prev,
        resending: false,
        error: err instanceof Error && err.message ? err.message : 'Failed to resend OTP',
      }));
    }
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const handleEcitizenSignUp = () => {
    setEcitizenNotice(true);
    setTimeout(() => setEcitizenNotice(false), 3000);
  };

  return (
    <div className="signup-page">
      <img src={signupBg} alt="" className="signup-page-bg" aria-hidden="true" />
      <div className="signup-page-overlay" />

      <div className="signup-kenya-chip">
        <span aria-hidden="true">🇰🇪</span> Kenya
      </div>

      <div className="signup-content">
        <AuthCard className="signup-card">
          <div className="auth-flag-stripe" aria-hidden="true">
            <span />
            <span />
            <span />
          </div>
          <form onSubmit={handleSubmit} noValidate>
            <div className="signup-brand fade-up">
              <img src={rafikiAvatar} alt="" className="signup-brand-logo" aria-hidden="true" />
              <div>
                <h1 className="signup-brand-name">Rafiki</h1>
                <p className="signup-brand-tagline">AI Government Assistant</p>
              </div>
            </div>

            <div className="signup-progress fade-up">
              <div className="signup-progress-step active">
                <span className="signup-progress-dot">1</span>
                Account details
              </div>
              <div className="signup-progress-line" />
              <div className="signup-progress-step">
                <span className="signup-progress-dot">2</span>
                Verify
              </div>
            </div>

            <div className="text-center mb-6 fade-up">
              <h1 className="signup-title">Create your account</h1>
              <p className="signup-subtitle">
                Join thousands of Kenyans accessing government services in one place.
              </p>
              <p className="font-dm-sans text-sm text-gray-600 mt-2">
                Already have an account?{' '}
                <Link to="/login" className="auth-link">
                  Sign in
                </Link>
              </p>
            </div>

            {error && (
              <div ref={errorBannerRef} className="auth-error-banner mb-6" role="alert" tabIndex={-1}>
                <AlertCircle size={20} aria-hidden="true" />
                <span>{error}</span>
              </div>
            )}

            <div className="space-y-5">
              <div className="grid md:grid-cols-2 gap-5 fade-up fade-up-delay-1">
                <AuthInput
                  label="Full Name"
                  placeholder="As it appears on your National ID"
                  icon={<User size={20} aria-hidden="true" />}
                  value={formData.fullName}
                  onChange={(v) => updateField('fullName', v)}
                  error={touched.has('fullName') ? formErrors.fullName : undefined}
                  autoComplete="name"
                  required
                  inputRef={fieldRefs.fullName}
                />
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
                  inputRef={fieldRefs.email}
                />
              </div>

              <div className="grid md:grid-cols-2 gap-5 fade-up fade-up-delay-2">
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
                  inputRef={fieldRefs.phone}
                />
                <AuthInput
                  label="National ID Number"
                  placeholder="7 or 8 digit ID number"
                  icon={<CreditCard size={20} aria-hidden="true" />}
                  value={formData.idNumber}
                  onChange={(v) => updateField('idNumber', v)}
                  error={touched.has('idNumber') ? formErrors.idNumber : undefined}
                  autoComplete="off"
                  required
                  inputRef={fieldRefs.idNumber}
                />
              </div>

              <div className="grid md:grid-cols-2 gap-5 fade-up fade-up-delay-3">
                <div>
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
                    inputRef={fieldRefs.password}
                  />
                  <PasswordStrengthBar password={formData.password} />
                </div>
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
                  inputRef={fieldRefs.confirmPassword}
                />
              </div>

              <div className="fade-up fade-up-delay-7 pt-2">
                <AuthCheckbox
                  checked={formData.hasDisability}
                  onChange={(v) => updateField('hasDisability', v)}
                  label="I am a person living with disabilities (PWD)"
                  subtext="This helps us provide tailored assistance for your needs"
                  highlighted
                />
              </div>

              <div className="fade-up fade-up-delay-8">
                <AuthCheckbox
                  checked={formData.agreeToTerms}
                  onChange={(v) => updateField('agreeToTerms', v)}
                  label={
                    <>
                      I agree to the <strong>Terms of Service</strong> and <strong>Privacy Policy</strong>
                    </>
                  }
                  error={touched.has('agreeToTerms') ? formErrors.agreeToTerms : undefined}
                  inputRef={fieldRefs.agreeToTerms}
                />
              </div>

              <div className="fade-up fade-up-delay-9 pt-2">
                <AuthButton type="submit" variant="primary" fullWidth loading={loading}>
                  <Sparkles size={18} aria-hidden="true" />
                  <span>Create Account</span>
                </AuthButton>
              </div>

              <div className="auth-divider fade-up fade-up-delay-10">
                <div className="auth-divider-line" />
                <span className="auth-divider-text">OR</span>
                <div className="auth-divider-line" />
              </div>

              <div className="fade-up fade-up-delay-10">
                <button type="button" className="ecitizen-button" onClick={handleEcitizenSignUp}>
                  <Landmark size={18} aria-hidden="true" />
                  <span>Continue with eCitizen</span>
                </button>
                {ecitizenNotice && (
                  <p className="ecitizen-notice" role="status">
                    eCitizen sign-up is coming soon.
                  </p>
                )}
              </div>

              <div className="login-security-note fade-up fade-up-delay-10">
                <ShieldCheck size={18} aria-hidden="true" />
                <p>
                  Your details are encrypted and only used to verify your identity with Kenyan government services.
                </p>
              </div>

              <div className="text-center pt-2 fade-up fade-up-delay-10">
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

      <div className="login-footer-bar">Proudly Kenyan 🇰🇪</div>

      {otpState.showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
          <div
            className="relative w-full max-w-md bg-white rounded-2xl shadow-2xl p-8"
            role="dialog"
            aria-modal="true"
            aria-labelledby="otp-heading"
          >
            <button
              type="button"
              onClick={() => setOtpState(prev => ({ ...prev, showModal: false }))}
              className="absolute top-4 right-4 p-2 rounded-full hover:bg-gray-100 transition-colors"
              aria-label="Close"
            >
              <X size={20} className="text-gray-500" />
            </button>

            <div className="text-center mb-6">
              <div className="w-16 h-16 bg-gradient-to-r from-green-700 to-green-900 rounded-full flex items-center justify-center mx-auto mb-4">
                <Lock size={28} className="text-white" />
              </div>
              <h3 id="otp-heading" className="font-playfair text-2xl text-gray-900 mb-2">Verify Your Account</h3>
              <p className="font-dm-sans text-gray-600 text-sm">
                We sent a 6-digit code to{' '}
                <span className="font-medium">{otpState.phoneMasked}</span>
                {otpState.emailMasked && (
                  <> and <span className="font-medium">{otpState.emailMasked}</span></>
                )}
              </p>
            </div>

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
                  className="w-12 h-14 text-center text-2xl font-bold border-2 rounded-xl focus:border-green-700 focus:ring-2 focus:ring-green-200 outline-none transition-all text-gray-900"
                  aria-label={`Digit ${index + 1}`}
                />
              ))}
            </div>

            {otpState.error && (
              <div className="auth-error-banner mb-4" role="alert">
                <AlertCircle size={18} aria-hidden="true" />
                <span>{otpState.error}</span>
              </div>
            )}

            <div className="flex justify-between items-center mb-6 text-sm text-gray-600">
              <span>Code expires in {formatTime(otpState.expiresIn)}</span>
              <button
                type="button"
                className="inline-flex items-center gap-2 text-green-700 hover:text-green-800 font-medium"
                onClick={() => handleResendOtp(formData.otpDelivery)}
                disabled={otpState.resending}
              >
                <RefreshCw size={16} className={otpState.resending ? 'animate-spin' : ''} />
                {otpState.resending ? 'Sending...' : 'Resend'}
              </button>
            </div>

            <AuthButton type="button" variant="primary" fullWidth loading={otpState.verifying} onClick={handleVerifyOtp}>
              <ShieldCheck size={18} aria-hidden="true" />
              <span>Verify & continue</span>
            </AuthButton>
          </div>
        </div>
      )}
    </div>
  );
}

export default SignUpPage;
