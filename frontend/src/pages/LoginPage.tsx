/**
 * LoginPage - Rafiki.ai Sign In
 * "Savanna at Dawn" themed login page
 */

import React, { useState, useCallback, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { User, Lock, AlertCircle } from 'lucide-react';
import { AuthInput, AuthButton, AuthCard } from '../components/Auth/components';
import { useAuth } from '../contexts/AuthContext';
import loginBg from '../assets/login.png';
import rafikiAvatar from '../assets/rafiki_avatar.png';
import '../styles/auth.css';

const API_BASE = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

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

  const handleGoogleSignIn = () => {
    // TODO: Implement Google OAuth
    window.location.href = `${API_BASE}/auth/google`;
  };

  return (
    <div className="auth-page">
      {/* Background Panel - Desktop */}
      <div className="auth-bg-panel">
        <img
          src={loginBg}
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
            Welcome back.
          </h1>
          <h2 className="font-playfair text-4xl lg:text-5xl leading-tight mb-4" style={{ color: '#C8860A' }}>
            Rafiki is ready.
          </h2>
          <p className="font-dm-sans text-base text-white/70 max-w-md">
            Your government services are just a conversation away.
          </p>
        </div>
      </div>

      {/* Mobile Background */}
      <div className="auth-mobile-bg lg:hidden">
        <img src={loginBg} alt="" className="w-full h-full object-cover" />
        <div className="auth-mobile-overlay" />
      </div>

      {/* Form Panel */}
      <div className="auth-form-panel">
        <AuthCard shake={shake}>
          <form onSubmit={handleSubmit} noValidate>
            {/* Returning User Greeting */}
            {lastUserName && (
              <div className="text-center mb-2 fade-up">
                <p className="font-dm-sans text-sm" style={{ color: '#C8860A' }}>
                  Welcome back, {lastUserName}
                </p>
              </div>
            )}

            {/* Header */}
            <div className="text-center mb-8 fade-up">
              <img
                src={rafikiAvatar}
                alt="Rafiki AI"
                className="rafiki-glow-subtle w-12 h-12 mx-auto mb-4"
              />
              <h1 className="font-playfair text-2xl md:text-3xl text-gray-900 mb-2">
                Sign in to Rafiki
              </h1>
              <p className="font-dm-sans text-sm text-gray-500">
                Good to have you back
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
                  label="Email or Phone"
                  placeholder="Email address or 07XX XXX XXX"
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
                  placeholder="Your password"
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
                  Sign In
                </AuthButton>
              </div>

              {/* Divider */}
              <div className="auth-divider fade-up fade-up-delay-5">
                <div className="auth-divider-line" />
                <span className="auth-divider-text">or</span>
                <div className="auth-divider-line" />
              </div>

              {/* Google Button */}
              <div className="fade-up fade-up-delay-5">
                <AuthButton
                  variant="google"
                  fullWidth
                  onClick={handleGoogleSignIn}
                >
                  Continue with Google
                </AuthButton>
              </div>

              {/* Footer Link */}
              <div className="text-center pt-4 fade-up fade-up-delay-6">
                <p className="font-dm-sans text-sm text-gray-600">
                  Don't have an account?{' '}
                  <Link to="/signup" className="auth-link">
                    Create one
                  </Link>
                </p>
              </div>
            </div>
          </form>
        </AuthCard>
      </div>
    </div>
  );
}

export default LoginPage;
