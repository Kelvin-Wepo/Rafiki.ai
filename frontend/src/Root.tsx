/**
 * Application Entry Point with Authentication
 * Wraps the main app with AuthProvider and handles auth routing.
 */


import { AuthProvider, useAuth } from './contexts/AuthContext';
import { LoginForm, OTPVerification } from './components/Auth';
import { Dashboard } from './components/Dashboard';

// Import original App for the main functionality
import OriginalApp from './App';

/**
 * Auth wrapper that conditionally renders login or main app.
 */
function AuthenticatedApp() {
  const { isAuthenticated, isLoading, isVerifying, pendingPhone } = useAuth();

  // Show loading state while validating token
  if (isLoading && !isVerifying) {
    return (
      <div className="auth-loading">
        <div className="auth-loading-content">
          <div className="auth-loading-spinner" />
          <p>Verifying session...</p>
        </div>
      </div>
    );
  }

  // Show OTP verification screen
  if (isVerifying && pendingPhone) {
    return <OTPVerification />;
  }

  // Show login screen if not authenticated
  if (!isAuthenticated) {
    return <LoginForm />;
  }

  // Show main dashboard with original app as content
  return (
    <Dashboard>
      <OriginalApp />
    </Dashboard>
  );
}

/**
 * Root component with providers.
 */
function Root() {
  return (
    <AuthProvider>
      <AuthenticatedApp />
    </AuthProvider>
  );
}

export default Root;
