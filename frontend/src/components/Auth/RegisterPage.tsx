/**
 * RegisterPage Component
 * Complete registration/login page with split-screen layout
 * Matches design mockup exactly
 */

import { useState, type FormEvent } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import type { OTPDeliveryMethod } from '../../services/authService';
import { Shield } from 'lucide-react';
import {
  AuthLayout,
  HeroSection,
  PhoneInput,
  OtpSelector,
  PrimaryButton,
  TrustBadges,
  ErrorMessage,
  type OTPMethod,
} from './components';

interface RegisterPageProps {
  onSuccess?: () => void;
}

export function RegisterPage({ onSuccess }: RegisterPageProps) {
  const { login, isLoading, error, clearError } = useAuth();
  const [phoneNumber, setPhoneNumber] = useState('');
  const [deliveryMethod, setDeliveryMethod] = useState<OTPMethod>('both');
  const [localError, setLocalError] = useState<string | null>(null);

  const validatePhoneNumber = (phone: string): boolean => {
    const cleaned = phone.replace(/[\s-]/g, '');
    const patterns = [/^\+254\d{9}$/, /^254\d{9}$/, /^0\d{9}$/, /^\d{9}$/];
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
      setLocalError('Please enter a valid Kenyan phone number (e.g., 712345678)');
      return;
    }

    try {
      const formattedPhone = formatPhoneNumber(phoneNumber);
      const response = await login(formattedPhone, deliveryMethod as OTPDeliveryMethod);
      if (response.success) onSuccess?.();
    } catch {
      // Error handled by context
    }
  };

  const displayError = localError || error;

  return (
    <AuthLayout heroContent={<HeroSection />}>
      {/* Form Header */}
      <div className="text-center mb-8">
        {/* Mobile Logo (hidden on desktop) */}
        <div className="lg:hidden flex items-center justify-center gap-2 mb-6">
          <div className="w-10 h-10 bg-[#006600] rounded-xl flex items-center justify-center">
            <Shield className="w-6 h-6 text-white" />
          </div>
          <span className="text-xl font-bold text-gray-900">Rafiki.ai</span>
        </div>

        <h1 className="text-2xl lg:text-3xl font-bold text-gray-900 mb-2">
          Karibu Nyumbani
          <span className="ml-2" role="img" aria-label="Kenya flag">🇰🇪</span>
        </h1>
        <p className="text-gray-600">
          Sign in to access government services
        </p>
      </div>

      {/* Login Form */}
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Phone Input */}
        <PhoneInput
          value={phoneNumber}
          onChange={(value) => {
            setPhoneNumber(value);
            if (localError) setLocalError(null);
            if (error) clearError();
          }}
          error={!!displayError}
          disabled={isLoading}
        />

        {/* OTP Method Selector */}
        <OtpSelector
          value={deliveryMethod}
          onChange={setDeliveryMethod}
          disabled={isLoading}
        />

        {/* Error Message */}
        {displayError && <ErrorMessage message={displayError} />}

        {/* Submit Button */}
        <PrimaryButton
          type="submit"
          isLoading={isLoading}
          loadingText="Sending OTP..."
        >
          Continue
        </PrimaryButton>
      </form>

      {/* Trust Badges */}
      <TrustBadges />

      {/* Footer Links */}
      <div className="mt-6 text-center text-xs text-gray-500">
        <p>
          By continuing, you agree to our{' '}
          <a href="/terms" className="text-[#006600] hover:underline">
            Terms of Service
          </a>{' '}
          and{' '}
          <a href="/privacy" className="text-[#006600] hover:underline">
            Privacy Policy
          </a>
        </p>
      </div>
    </AuthLayout>
  );
}

export default RegisterPage;
