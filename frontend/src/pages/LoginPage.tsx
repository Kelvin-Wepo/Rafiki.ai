/**
 * LoginPage - Rafiki.ai Sign In
 */

import React, { useState, useCallback, useEffect, useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { User, Lock, AlertCircle, ShieldCheck, ExternalLink } from 'lucide-react';
import { AuthInput, AuthButton, AuthCard } from '../components/Auth/components';
import { RafikiLogo } from '../components/RafikiLogo';
import { useAuth } from '../contexts/AuthContext';
import '../styles/auth.css';

interface FormData {
  emailOrPhone: string;
  password: string;
}

interface FormErrors {
  emailOrPhone?: string;
  password?: string;
}

// Validation helpers
const validateEmail = (email: string): boolean => {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
};

const validatePhone = (phone: string): boolean => {
  return /^(\+?254|0)7\d{8}$/.test(phone.replace(/\s/g, ''));
};

const validateEmailOrPhone = (value: string): boolean => {
  const cleaned = value.trim();
  return validateEmail(cleaned) || validatePhone(cleaned);
};

export function LoginPage() {
  const navigate = useNavigate();
  const { passwordLogin, isAuthenticated } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [shake, setShake] = useState(false);
  const [lastUserName, setLastUserName] = useState<string | null>(null);
  const [formData, setFormData] = useState<FormData>({
    emailOrPhone: '',
    password: '',
  });
  const [formErrors, setFormErrors] = useState<FormErrors>({});
  const [touched, setTouched] = useState<Set<string>>(new Set());

  // Focus targets for screen reader users: first invalid field / error banner
  const emailOrPhoneRef = useRef<HTMLInputElement>(null);
  const passwordRef = useRef<HTMLInputElement>(null);
  const errorBannerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (error) {
      errorBannerRef.current?.focus();
    }
  }, [error]);

  // Check for returning user
  useEffect(() => {
    const savedName = localStorage.getItem('rafiki_last_user');
    if (savedName) {
      setLastUserName(savedName);
    }
  }, []);

  const updateField = useCallback((field: keyof FormData, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    setTouched(prev => new Set(prev).add(field));
    setError(null);
  }, []);

  const validateForm = useCallback((): boolean => {
    const errors: FormErrors = {};

    if (!validateEmailOrPhone(formData.emailOrPhone)) {
      errors.emailOrPhone = 'Please enter a valid email or Kenyan phone number';
    }

    if (formData.password.length === 0) {
      errors.password = 'Please enter your password';
    }

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  }, [formData]);

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated) {
      navigate('/chat');
    }
  }, [isAuthenticated, navigate]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    setTouched(new Set(['emailOrPhone', 'password']));

    if (!validateForm()) {
      if (!validateEmailOrPhone(formData.emailOrPhone)) {
        emailOrPhoneRef.current?.focus();
      } else {
        passwordRef.current?.focus();
      }
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await passwordLogin(
        formData.emailOrPhone.trim().replace(/\s/g, ''),
        formData.password
      );

      if (response.success) {
        // Store user name for personalization
        if (response.user?.full_name) {
          localStorage.setItem('rafiki_last_user', response.user.full_name.split(' ')[0]);
        }
        // Navigation will happen automatically via AuthRoute when isAuthenticated changes
      } else {
        throw new Error(response.message || 'Invalid credentials');
      }
    } catch (err) {
      setError(err instanceof Error && err.message ? err.message : 'Invalid email/phone or password');
      // Trigger shake animation
      setShake(true);
      setTimeout(() => setShake(false), 600);
    } finally {
      setLoading(false);
    }
  };

  const handleEcitizenSignIn = () => {
    // TODO: implement eCitizen OAuth once the integration exists
    setNotice('eCitizen sign-in is coming soon — please use your email or phone number for now.');
  };

  return (
    <div className="auth-page">
      {/* Kenya badge */}
      <div className="auth-topbar">
        <span className="kenya-badge">🇰🇪 Kenya</span>
      </div>

      {/* Form Panel */}
      <main className="auth-form-panel">
        <AuthCard shake={shake}>
          <form onSubmit={handleSubmit} noValidate aria-labelledby="login-heading">
            {/* Header */}
            <div className="text-center mb-5 fade-up">
              <RafikiLogo size={30} showTagline className="mb-3" />
              <h1 id="login-heading" className="font-playfair text-2xl md:text-3xl text-gray-900 mb-2">
                {lastUserName ? `Welcome back, ${lastUserName}!` : 'Welcome back!'}
              </h1>
              <p className="font-dm-sans text-sm text-gray-500">
                Let's securely connect to your eCitizen account so I can help you.
              </p>
            </div>

            {/* Error Banner */}
            {error && (
              <div
                ref={errorBannerRef}
                className="auth-error-banner mb-6"
                role="alert"
                tabIndex={-1}
              >
                <AlertCircle size={20} aria-hidden="true" />
                <span>{error}</span>
              </div>
            )}

            {/* Form Fields */}
            <div className="space-y-4">
              {/* Email or Phone */}
              <div className="fade-up fade-up-delay-1">
                <AuthInput
                  label="Email or Phone Number"
                  placeholder="Enter your email or phone number"
                  icon={<User size={20} aria-hidden="true" />}
                  value={formData.emailOrPhone}
                  onChange={(v) => updateField('emailOrPhone', v)}
                  error={touched.has('emailOrPhone') ? formErrors.emailOrPhone : undefined}
                  autoComplete="username"
                  required
                  staticLabel
                  inputRef={emailOrPhoneRef}
                />
              </div>

              {/* Password */}
              <div className="fade-up fade-up-delay-2">
                <AuthInput
                  label="Password"
                  placeholder="Enter your password"
                  icon={<Lock size={20} aria-hidden="true" />}
                  value={formData.password}
                  onChange={(v) => updateField('password', v)}
                  error={touched.has('password') ? formErrors.password : undefined}
                  showPasswordToggle
                  autoComplete="current-password"
                  required
                  staticLabel
                  inputRef={passwordRef}
                />
              </div>

              {/* Forgot Password */}
              <div className="text-right fade-up fade-up-delay-3">
                <Link to="/forgot-password" className="auth-link text-sm">
                  Forgot password?
                </Link>
              </div>

              {/* Submit Button */}
              <div className="fade-up fade-up-delay-4">
                <AuthButton
                  type="submit"
                  variant="primary"
                  fullWidth
                  loading={loading}
                >
                  <Lock size={18} aria-hidden="true" />
                  Sign in securely
                </AuthButton>
              </div>

              {/* Divider */}
              <div className="auth-divider fade-up fade-up-delay-5">
                <div className="auth-divider-line" />
                <span className="auth-divider-text">OR</span>
                <div className="auth-divider-line" />
              </div>

              {/* eCitizen Button */}
              <div className="fade-up fade-up-delay-5">
                <AuthButton variant="google" fullWidth onClick={handleEcitizenSignIn}>
                  <ExternalLink size={18} aria-hidden="true" />
                  <span>
                    Continue with{' '}
                    <strong style={{ color: 'var(--rafiki-green-deep)' }}>eCitizen</strong>
                  </span>
                </AuthButton>
                {notice && (
                  <p role="status" className="font-dm-sans text-xs text-gray-500 mt-2 text-center">
                    {notice}
                  </p>
                )}
              </div>

              {/* Trust box */}
              <div className="auth-trust-box fade-up fade-up-delay-6">
                <ShieldCheck size={20} aria-hidden="true" />
                <span>
                  Your credentials are only used to access your eCitizen account
                  with your permission.{' '}
                  <Link to="/" className="auth-link">
                    Learn more
                  </Link>
                </span>
              </div>

              {/* Footer Link */}
              <div className="text-center pt-2 fade-up fade-up-delay-6">
                <p className="font-dm-sans text-sm text-gray-600">
                  New to Rafiki?{' '}
                  <Link to="/signup" className="auth-link">
                    Create an account
                  </Link>
                </p>
              </div>
            </div>
          </form>
        </AuthCard>
      </main>

      {/* Footer strip */}
      <div className="kenya-stripe" aria-hidden="true" />
      <div className="proudly-kenyan">Proudly Kenyan 🇰🇪</div>
    </div>
  );
}

export default LoginPage;
