/**
 * LandingPage - Rafiki.ai public marketing/home page
 * Shown to logged-out visitors at "/".
 */

import React from 'react';
import { Link } from 'react-router-dom';
import {
  Globe,
  Accessibility,
  Mic,
  MessageSquare,
  ShieldCheck,
  Car,
  Plane,
  FileText,
  Briefcase,
  HeartPulse,
  GraduationCap,
  IdCard,
  Baby,
  Landmark,
  Sparkles,
  Clock,
  Heart,
} from 'lucide-react';
import rafikiAvatar from '../assets/rafiki_avatar.png';
import '../styles/landing.css';

const SERVICE_BADGES = [
  { id: 'ecitizen', label: 'eCitizen', icon: Globe, position: 'badge-top' },
  { id: 'ntsa', label: 'NTSA', icon: Car, position: 'badge-top-right' },
  { id: 'kra', label: 'KRA', icon: FileText, position: 'badge-right' },
  { id: 'health', label: 'Health', icon: HeartPulse, position: 'badge-bottom-right' },
  { id: 'education', label: 'Education', icon: GraduationCap, position: 'badge-bottom' },
  { id: 'business', label: 'Business', icon: Briefcase, position: 'badge-left' },
  { id: 'immigration', label: 'Immigration', icon: Plane, position: 'badge-top-left' },
];

const QUICK_ACTIONS = [
  { id: 'passport', title: 'Apply for\nPassport', icon: IdCard, color: 'qa-green' },
  { id: 'license', title: 'Renew\nDriving Licence', icon: Car, color: 'qa-gold' },
  { id: 'business', title: 'Register\nBusiness', icon: Briefcase, color: 'qa-dark' },
  { id: 'birth', title: 'Birth\nCertificate', icon: Baby, color: 'qa-red' },
  { id: 'police', title: 'Police\nClearance', icon: ShieldCheck, color: 'qa-black' },
  { id: 'land', title: 'Land\nServices', icon: Landmark, color: 'qa-gold' },
];

const TRUST_ITEMS = [
  { icon: ShieldCheck, title: 'Secure', desc: 'Your data is protected' },
  { icon: Accessibility, title: 'Accessible', desc: 'For everyone, everywhere' },
  { icon: Clock, title: 'Reliable', desc: 'Always here to help' },
  { icon: Heart, title: 'Kenyan', desc: 'Built for Kenyans' },
];

export function LandingPage() {
  return (
    <div className="landing-page">
      {/* Top nav */}
      <header className="landing-nav">
        <div className="landing-nav-brand">
          <img src={rafikiAvatar} alt="" className="landing-nav-logo" aria-hidden="true" />
          <div>
            <p className="landing-nav-name">Rafiki</p>
            <p className="landing-nav-tagline">AI Government Assistant</p>
          </div>
        </div>
        <div className="landing-nav-actions">
          <button type="button" className="landing-nav-link">
            <Globe size={16} aria-hidden="true" />
            English
          </button>
          <button type="button" className="landing-nav-link">
            <Accessibility size={16} aria-hidden="true" />
            Accessibility
          </button>
          <Link to="/login" className="landing-nav-link landing-nav-link--signin">
            Sign in
          </Link>
          <Link to="/signup" className="landing-signin-button">
            Sign up
          </Link>
        </div>
      </header>

      <main>
        {/* Hero */}
        <section className="landing-hero">
          <div className="landing-hero-copy">
            <span className="landing-badge-pill">
              <span aria-hidden="true">🇰🇪</span> Proudly built for Kenya
            </span>
            <h1 className="landing-hero-title">
              Your AI Assistant for <span className="landing-hero-highlight">Government Services</span>
            </h1>
            <p className="landing-hero-subtitle">
              Tell Rafiki what you need, and I'll handle the rest. Fast, simple, secure.
            </p>
            <div className="landing-hero-cta">
              <Link to="/login" className="landing-cta-primary">
                <Mic size={18} aria-hidden="true" />
                Ask Rafiki <span className="landing-cta-sub">(Voice)</span>
              </Link>
              <Link to="/login" className="landing-cta-secondary">
                <MessageSquare size={18} aria-hidden="true" />
                Type your request
              </Link>
            </div>
            <p className="landing-hero-note">
              <ShieldCheck size={14} aria-hidden="true" />
              Your data is secure and will only be used with your permission.
            </p>
          </div>

          <div className="landing-hero-visual">
            <div className="landing-mascot-halo">
              <img src={rafikiAvatar} alt="Rafiki, your AI government assistant" className="landing-mascot" />
              {SERVICE_BADGES.map(({ id, label, icon: Icon, position }) => (
                <div key={id} className={`landing-service-badge ${position}`}>
                  <span className="landing-service-icon">
                    <Icon size={18} aria-hidden="true" />
                  </span>
                  <span className="landing-service-label">{label}</span>
                </div>
              ))}
            </div>
            <div className="landing-chat-bubble">
              <p>
                <span aria-hidden="true">👋</span> <strong>Habari, I'm Rafiki</strong>
              </p>
              <p className="landing-chat-bubble-sub">How can I help you today?</p>
            </div>
          </div>
        </section>

        {/* Quick actions */}
        <section className="landing-quick-actions">
          <div className="landing-quick-actions-grid">
            {QUICK_ACTIONS.map(({ id, title, icon: Icon, color }) => (
              <Link key={id} to="/login" className={`landing-action-card ${color}`}>
                <span className="landing-action-icon">
                  <Icon size={22} aria-hidden="true" />
                </span>
                <span className="landing-action-title">
                  {title.split('\n').map((line, i) => (
                    <React.Fragment key={i}>
                      {line}
                      {i === 0 && <br />}
                    </React.Fragment>
                  ))}
                </span>
              </Link>
            ))}
          </div>
          <p className="landing-more-services">
            <Sparkles size={14} aria-hidden="true" />
            More services coming soon. Tell me what you need!
          </p>
        </section>
      </main>

      {/* Trust footer bar */}
      <footer className="landing-trust-bar">
        {TRUST_ITEMS.map(({ icon: Icon, title, desc }) => (
          <div key={title} className="landing-trust-item">
            <Icon size={20} aria-hidden="true" />
            <div>
              <p className="landing-trust-title">{title}</p>
              <p className="landing-trust-desc">{desc}</p>
            </div>
          </div>
        ))}
      </footer>
    </div>
  );
}

export default LandingPage;
