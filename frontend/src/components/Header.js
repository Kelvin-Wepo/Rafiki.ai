/**
 * Header Component
 * Accessible navigation header with keyboard support
 */

import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAccessibility } from '../context/AccessibilityContext';
import AccessibilityControls from './AccessibilityControls';

function Header() {
  const location = useLocation();
  const { announce } = useAccessibility();

  const navLinks = [
    { path: '/', label: 'Home' },
    { path: '/services', label: 'Services' },
    { path: '/booking', label: 'Book Appointment' },
  ];

  const handleNavClick = (label) => {
    announce(`Navigating to ${label}`);
  };

  return (
    <header className="header" role="banner">
      <div className="header-container">
        <Link 
          to="/" 
          className="header-logo"
          aria-label="eCitizen Voice Assistant - Home"
          onClick={() => handleNavClick('Home')}
        >
          <svg 
            className="header-logo-icon" 
            viewBox="0 0 48 48" 
            fill="currentColor"
            aria-hidden="true"
          >
            <path d="M24 4C12.954 4 4 12.954 4 24s8.954 20 20 20 20-8.954 20-20S35.046 4 24 4zm0 36c-8.837 0-16-7.163-16-16S15.163 8 24 8s16 7.163 16 16-7.163 16-16 16z"/>
            <path d="M24 14c-5.523 0-10 4.477-10 10s4.477 10 10 10 10-4.477 10-10-4.477-10-10-10zm0 16c-3.314 0-6-2.686-6-6s2.686-6 6-6 6 2.686 6 6-2.686 6-6 6z"/>
            <circle cx="24" cy="24" r="3"/>
          </svg>
          <span className="header-title">eCitizen Voice</span>
        </Link>

        <nav className="header-nav" role="navigation" aria-label="Main navigation">
          {navLinks.map((link) => (
            <Link
              key={link.path}
              to={link.path}
              className={`header-nav-link ${location.pathname === link.path ? 'active' : ''}`}
              aria-current={location.pathname === link.path ? 'page' : undefined}
              onClick={() => handleNavClick(link.label)}
            >
              {link.label}
            </Link>
          ))}
        </nav>

        <AccessibilityControls />
      </div>
    </header>
  );
}

export default Header;
