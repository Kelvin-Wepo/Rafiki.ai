/**
 * ForgotPasswordPage — placeholder until the backend reset flow exists.
 * Keeps the "Forgot password?" link honest instead of a dead loop.
 */

import { Link } from 'react-router-dom';
import { KeyRound } from 'lucide-react';
import { AuthCard } from '../components/Auth/components';
import { RafikiLogo } from '../components/RafikiLogo';
import '../styles/auth.css';

export function ForgotPasswordPage() {
  return (
    <div className="auth-page">
      <div className="auth-topbar">
        <span className="kenya-badge">🇰🇪 Kenya</span>
      </div>

      <main className="auth-form-panel">
        <AuthCard>
          <div className="text-center">
            <RafikiLogo size={34} showTagline className="mb-4" />
            <h1 className="font-playfair text-2xl md:text-3xl text-gray-900 mb-3">
              Reset your password
            </h1>
            <div className="auth-trust-box my-6">
              <KeyRound size={20} aria-hidden="true" />
              <span>
                Self-service password reset is coming soon. For now, please
                create a new account or contact support at{' '}
                <a href="mailto:support@rafiki.ai" className="auth-link">
                  support@rafiki.ai
                </a>{' '}
                to regain access.
              </span>
            </div>
            <p className="font-dm-sans text-sm text-gray-600">
              Remembered it?{' '}
              <Link to="/login" className="auth-link">
                Back to sign in
              </Link>
            </p>
          </div>
        </AuthCard>
      </main>

      <div className="kenya-stripe" aria-hidden="true" />
      <div className="proudly-kenyan">Proudly Kenyan 🇰🇪</div>
    </div>
  );
}

export default ForgotPasswordPage;
