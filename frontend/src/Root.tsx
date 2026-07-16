/**
 * Application Entry Point with Authentication
 * Wraps the main app with AuthProvider and handles auth routing.
 */

import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { OTPVerification } from './components/Auth';
import { Dashboard } from './components/Dashboard';
import { SignUpPage, LoginPage, LandingPage, ForgotPasswordPage } from './pages';

/**
 * Loading Screen Component
 */
function LoadingScreen() {
  // Cream/gold to match both the pre-React splash (index.html) and the
  // auth pages, so session validation reads as one continuous load
  return (
    <div className="min-h-screen flex items-center justify-center" style={{ background: '#FAF3E0' }}>
      <div className="text-center">
        <div
          className="w-12 h-12 mx-auto mb-4 rounded-full border-4 border-t-transparent animate-spin"
          style={{ borderColor: 'rgba(200, 134, 10, 0.25)', borderTopColor: '#C8860A' }}
        />
        <p style={{ color: '#6B7280' }}>Verifying session...</p>
      </div>
    </div>
  );
}

/**
 * Protected Route Wrapper
 */
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();
  
  if (isLoading) {
    return <LoadingScreen />;
  }
  
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  
  return <>{children}</>;
}

/**
 * Auth Route Wrapper - redirects to chat if already authenticated
 */
function AuthRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();
  
  if (isLoading) {
    return <LoadingScreen />;
  }
  
  if (isAuthenticated) {
    return <Navigate to="/chat" replace />;
  }
  
  return <>{children}</>;
}

/**
 * Home Route — marketing landing for visitors, Dashboard once signed in
 */
function HomeRoute() {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return <LoadingScreen />;
  }

  return isAuthenticated ? <Dashboard /> : <LandingPage />;
}

/**
 * Main App Router with all routes
 */
function AppRouter() {
  const { isVerifying, pendingPhone } = useAuth();

  // Show OTP verification if in verifying state
  if (isVerifying && pendingPhone) {
    return <OTPVerification />;
  }

  return (
    <Routes>
      {/* Auth Routes */}
      <Route
        path="/login"
        element={
          <AuthRoute>
            <LoginPage />
          </AuthRoute>
        }
      />
      <Route
        path="/signup"
        element={
          <AuthRoute>
            <SignUpPage />
          </AuthRoute>
        }
      />

      <Route
        path="/forgot-password"
        element={
          <AuthRoute>
            <ForgotPasswordPage />
          </AuthRoute>
        }
      />

      {/* Home: landing page for visitors, Dashboard when signed in */}
      <Route path="/" element={<HomeRoute />} />
      <Route
        path="/chat"
        element={
          <ProtectedRoute>
            <Dashboard />
          </ProtectedRoute>
        }
      />

      {/* Catch all - redirect to login */}
      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  );
}

/**
 * Root component with providers.
 */
function Root() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRouter />
      </AuthProvider>
    </BrowserRouter>
  );
}

export default Root;
