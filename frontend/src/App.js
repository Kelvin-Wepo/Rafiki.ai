import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { AccessibilityProvider } from './context/AccessibilityContext';
import { SessionProvider } from './context/SessionContext';
import { ElevenLabsProvider } from './context/ElevenLabsContext';
import Header from './components/Header';
import Footer from './components/Footer';
import HomePage from './components/HomePage';
import ServicesPage from './components/ServicesPage';
import BookingPage from './components/BookingPage';
import './styles/App.css';

function App() {
  return (
    <AccessibilityProvider>
      <SessionProvider>
        <ElevenLabsProvider>
          <Router>
            <div className="app">
              <Header />
              <main id="main-content" tabIndex="-1">
                <Routes>
                  <Route path="/" element={<HomePage />} />
                  <Route path="/services" element={<ServicesPage />} />
                  <Route path="/booking/:serviceType?" element={<BookingPage />} />
                </Routes>
              </main>
              <Footer />
              <Toaster
                position="top-center"
                toastOptions={{
                  duration: 5000,
                  style: {
                    fontSize: '1.1rem',
                    padding: '16px',
                  },
                  success: {
                    iconTheme: {
                      primary: '#10B981',
                      secondary: '#FFFFFF',
                    },
                  },
                  error: {
                    iconTheme: {
                      primary: '#EF4444',
                      secondary: '#FFFFFF',
                    },
                  },
                }}
                // Announce toasts to screen readers
                ariaProps={{
                  role: 'alert',
                  'aria-live': 'assertive',
                }}
              />
            </div>
          </Router>
        </ElevenLabsProvider>
      </SessionProvider>
    </AccessibilityProvider>
  );
}

export default App;
