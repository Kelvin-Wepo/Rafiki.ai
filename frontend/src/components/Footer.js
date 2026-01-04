/**
 * Footer Component
 * Accessible footer with useful links
 */

import React from 'react';
import { Link } from 'react-router-dom';

function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="footer" role="contentinfo">
      <div className="footer-container">
        <nav className="footer-links" aria-label="Footer navigation">
          <Link to="/services" className="footer-link">Services</Link>
          <a 
            href="https://www.ecitizen.go.ke" 
            className="footer-link"
            target="_blank"
            rel="noopener noreferrer"
            aria-label="eCitizen Portal (opens in new tab)"
          >
            eCitizen Portal
          </a>
          <a 
            href="tel:+254-20-2227411" 
            className="footer-link"
            aria-label="Call helpline"
          >
            Helpline
          </a>
        </nav>
        <p className="footer-copyright">
          © {currentYear} eCitizen Voice Assistant. 
          Built for accessibility.
        </p>
        <p className="footer-copyright" style={{ marginTop: '0.5rem', fontSize: '0.85rem' }}>
          For assistance, call the eCitizen helpline or use voice commands.
        </p>
      </div>
    </footer>
  );
}

export default Footer;
