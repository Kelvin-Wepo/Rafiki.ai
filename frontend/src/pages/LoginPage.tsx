/**
 * LoginPage - Rafiki.ai Sign In
 * "Savanna at Dawn" themed login page
 */

import React, { useState, useCallback, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { User, Lock, AlertCircle, ShieldCheck, Landmark } from 'lucide-react';
import { AuthInput, AuthButton, AuthCard } from '../components/Auth/components';
import { useAuth } from '../contexts/AuthContext';
import loginBg from '../assets/login.png';
import rafikiAvatar from '../assets/rafiki_avatar.png';
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
  const [shake, setShake] = useState(false);
  const [lastUserName, setLastUserName] = useState<string | null>(null);
  const [formData, setFormData] = useState<FormData>({
    emailOrPhone: '',
    password: '',
  });
  const [formErrors, setFormErrors] = useState<FormErrors>({});
  const [touched, setTouched] = useState<Set<string>>(new Set());

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
    } catch (err: any) {
      setError(err.message || 'Invalid email/phone or password');
      // Trigger shake animation
      setShake(true);
      setTimeout(() => setShake(false), 600);
    } finally {
      setLoading(false);
    }
  };

  const [showEcitizenNotice, setShowEcitizenNotice] = useState(false);

  const handleEcitizenSignIn = () => {
    // eCitizen SSO is not wired up yet - UI placeholder only.
    setShowEcitizenNotice(true);
    setTimeout(() => setShowEcitizenNotice(false), 3000);
  };

  return (
    <div className="login-page">
      <img src={loginBg} alt="" className="login-page-bg" aria-hidden="true" />
      <div className="login-page-overlay" />

      <div className="login-kenya-chip">
        <span aria-hidden="true">🇰🇪</span> Kenya
      </div>

      <div className="login-content">
        <AuthCard shake={shake} className="login-card">
          <div className="auth-flag-stripe" aria-hidden="true">
            <span />
            <span />
            <span />
          </div>
          <form onSubmit={handleSubmit} noValidate>
            {/* Brand Header */}
            <div className="login-brand fade-up">
              <img
                src={rafikiAvatar}
                alt=""
                className="login-brand-logo"
                aria-hidden="true"
              />
              <div>
                <h1 className="login-brand-name">Rafiki</h1>
                <p className="login-brand-tagline">AI Government Assistant</p>
              </div>
            </div>

            {/* Returning User Greeting */}
            {lastUserName && (
              <div className="text-center mb-2 fade-up">
                <p className="font-dm-sans text-sm" style={{ color: 'var(--rafiki-gold)' }}>
                  Welcome back, {lastUserName}
                </p>
              </div>
            )}

            {/* Header */}
            <div className="text-center mb-6 fade-up">
              <h1 className="login-title">Welcome back!</h1>
              <p className="login-subtitle">
                Let's securely connect to your eCitizen account so I can help you.
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
                />
              </div>

              {/* Forgot Password Link */}
              <div className="text-right fade-up fade-up-delay-3">
                <Link to="/forgot-password" className="auth-link text-sm">
                  Forgot password?
                </Link>
              </div>

              {/* Submit Button */}
              <div className="fade-up fade-up-delay-4 pt-2">
                <AuthButton
                  type="submit"
                  variant="primary"
                  fullWidth
                  loading={loading}
                >
                  <Lock size={18} aria-hidden="true" />
                  <span>Sign in securely</span>
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
                <button
                  type="button"
                  className="ecitizen-button"
                  onClick={handleEcitizenSignIn}
                >
                  <Landmark size={18} aria-hidden="true" />
                  <span>Continue with eCitizen</span>
                </button>
                {showEcitizenNotice && (
                  <p className="ecitizen-notice" role="status">
                    eCitizen sign-in is coming soon.
                  </p>
                )}
              </div>

              {/* Security Note */}
              <div className="login-security-note fade-up fade-up-delay-6">
                <ShieldCheck size={18} aria-hidden="true" />
                <p>
                  Your credentials are only used to access your eCitizen account with your
                  permission.{' '}
                  <Link to="/privacy" className="auth-link">
                    Learn more
                  </Link>
                </p>
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
      </div>

      <div className="login-footer-bar">Proudly Kenyan 🇰🇪</div>
    </div>
  );
}

export default LoginPage;
