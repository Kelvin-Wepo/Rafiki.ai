/**
 * Dashboard Sidenav Component
 * Main navigation sidebar for the dashboard.
 * 
 * Responsive behavior:
 * - Desktop (≥1024px): Fixed left sidebar, full height
 * - Tablet (≥768px <1024px): Collapsible/narrower sidebar
 * - Mobile (<768px): Off-canvas drawer with hamburger toggle
 * 
 * Sections:
 * - New Conversation
 * - Conversation History
 * - Transcript Download
 * - User Profile / Logout
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import './Dashboard.css';

export type NavSection = 'new' | 'history' | 'transcripts' | 'profile';

interface SidenavProps {
  activeSection: NavSection;
  onSectionChange: (section: NavSection) => void;
  isMobileOpen?: boolean;
  onMobileClose?: () => void;
}

export function Sidenav({
  activeSection,
  onSectionChange,
  isMobileOpen = false,
  onMobileClose,
}: SidenavProps) {
  const { user, logout, isLoading } = useAuth();
  const [showLogoutConfirm, setShowLogoutConfirm] = useState(false);
  const sidenavRef = useRef<HTMLElement>(null);
  const firstFocusableRef = useRef<HTMLButtonElement>(null);

  // Handle ESC key to close drawer
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isMobileOpen) {
        onMobileClose?.();
      }
    };

    if (isMobileOpen) {
      document.addEventListener('keydown', handleKeyDown);
      // Focus first item when drawer opens
      setTimeout(() => firstFocusableRef.current?.focus(), 100);
      // Prevent body scroll when drawer is open
      document.body.style.overflow = 'hidden';
    }

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = '';
    };
  }, [isMobileOpen, onMobileClose]);

  const handleSectionClick = useCallback((section: NavSection) => {
    onSectionChange(section);
    onMobileClose?.();
  }, [onSectionChange, onMobileClose]);

  const handleLogout = async () => {
    await logout();
  };

  const navItems = [
    {
      id: 'new' as NavSection,
      label: 'New Conversation',
      icon: (
        <svg viewBox="0 0 24 24" fill="currentColor">
          <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z" />
        </svg>
      ),
      description: 'Start a new chat',
    },
    {
      id: 'history' as NavSection,
      label: 'History',
      icon: (
        <svg viewBox="0 0 24 24" fill="currentColor">
          <path d="M13 3c-4.97 0-9 4.03-9 9H1l3.89 3.89.07.14L9 12H6c0-3.87 3.13-7 7-7s7 3.13 7 7-3.13 7-7 7c-1.93 0-3.68-.79-4.94-2.06l-1.42 1.42C8.27 19.99 10.51 21 13 21c4.97 0 9-4.03 9-9s-4.03-9-9-9zm-1 5v5l4.28 2.54.72-1.21-3.5-2.08V8H12z" />
        </svg>
      ),
      description: 'View past conversations',
    },
    {
      id: 'transcripts' as NavSection,
      label: 'Transcripts',
      icon: (
        <svg viewBox="0 0 24 24" fill="currentColor">
          <path d="M19 9h-4V3H9v6H5l7 7 7-7zM5 18v2h14v-2H5z" />
        </svg>
      ),
      description: 'Download conversation logs',
    },
  ];

  return (
    <>
      <aside 
        ref={sidenavRef}
        id="sidenav"
        className={`sidenav ${isMobileOpen ? 'sidenav-open' : ''}`}
        role="navigation"
        aria-label="Main navigation"
        aria-hidden={!isMobileOpen}
      >
        {/* Header */}
        <div className="sidenav-header">
          <div className="sidenav-logo">
            <svg viewBox="0 0 24 24" fill="currentColor" className="shield-icon">
              <path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4zm0 10.99h7c-.53 4.12-3.28 7.79-7 8.94V12H5V6.3l7-3.11v8.8z" />
            </svg>
          </div>
          <div className="sidenav-brand">
            <h1>Rafiki</h1>
            <span>Government Services</span>
          </div>
          
          {/* Mobile close button */}
          <button
            ref={firstFocusableRef}
            className="sidenav-close"
            onClick={onMobileClose}
            aria-label="Close menu"
          >
            <svg viewBox="0 0 24 24" fill="currentColor">
              <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z" />
            </svg>
          </button>
        </div>

        {/* Navigation */}
        <nav className="sidenav-nav">
          <ul className="nav-list">
            {navItems.map((item) => (
              <li key={item.id}>
                <button
                  className={`nav-item ${activeSection === item.id ? 'nav-item-active' : ''}`}
                  onClick={() => handleSectionClick(item.id)}
                >
                  <span className="nav-icon">{item.icon}</span>
                  <span className="nav-label">{item.label}</span>
                </button>
              </li>
            ))}
          </ul>
        </nav>

        {/* User Section */}
        <div className="sidenav-footer">
          <button
            className={`nav-item user-item ${activeSection === 'profile' ? 'nav-item-active' : ''}`}
            onClick={() => handleSectionClick('profile')}
          >
            <span className="user-avatar">
              <svg viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z" />
              </svg>
            </span>
            <div className="user-info">
              <span className="user-phone">{user?.phone_masked || 'User'}</span>
              <span className="user-status">
                <span className="status-dot" />
                Active
              </span>
            </div>
          </button>

          {/* Logout Button */}
          {!showLogoutConfirm ? (
            <button
              className="logout-btn"
              onClick={() => setShowLogoutConfirm(true)}
              disabled={isLoading}
            >
              <svg viewBox="0 0 24 24" fill="currentColor">
                <path d="M17 7l-1.41 1.41L18.17 11H8v2h10.17l-2.58 2.58L17 17l5-5zM4 5h8V3H4c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h8v-2H4V5z" />
              </svg>
              <span>Logout</span>
            </button>
          ) : (
            <div className="logout-confirm">
              <p>Sign out?</p>
              <div className="logout-actions">
                <button
                  className="btn-confirm-cancel"
                  onClick={() => setShowLogoutConfirm(false)}
                >
                  Cancel
                </button>
                <button
                  className="btn-confirm-logout"
                  onClick={handleLogout}
                  disabled={isLoading}
                >
                  {isLoading ? 'Signing out...' : 'Yes, logout'}
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Security Badge */}
        <div className="security-badge">
          <svg viewBox="0 0 24 24" fill="currentColor">
            <path d="M18 8h-1V6c0-2.76-2.24-5-5-5S7 3.24 7 6v2H6c-1.1 0-2 .9-2 2v10c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V10c0-1.1-.9-2-2-2zm-6 9c-1.1 0-2-.9-2-2s.9-2 2-2 2 .9 2 2-.9 2-2 2zm3.1-9H8.9V6c0-1.71 1.39-3.1 3.1-3.1 1.71 0 3.1 1.39 3.1 3.1v2z" />
          </svg>
          <span>Secured Session</span>
        </div>
      </aside>
    </>
  );
}

export default Sidenav;
