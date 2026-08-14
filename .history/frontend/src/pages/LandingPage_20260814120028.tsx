/**
 * LandingPage — public marketing home ("/" for unauthenticated visitors).
 * eCitizen-green redesign: hero + service grid + trust footer.
 */

import { Link } from 'react-router-dom';
import {
  Mic,
  Keyboard,
  ShieldCheck,
  BookUser,
  Car,
  IdCard,
  Briefcase,
  Home,
  LayoutGrid,
  Headset,
  Globe,
  ChevronDown,
  Accessibility,
  Volume2,
  Lock,
  Heart,
} from 'lucide-react';
import { RafikiLogo } from '../components/RafikiLogo';
import '../styles/auth.css';
import '../styles/landing.css';

/* Every card shares one treatment — no per-service colour. Each entry still
   navigates to /login exactly as before; only the presentation changed. */
const SERVICES = [
  { name: 'Apply for Passport', icon: BookUser },
  { name: 'Renew Driving Licence', icon: Car },
  { name: 'Replace Lost ID', icon: IdCard },
  { name: 'Register a Business', icon: Briefcase },
  { name: 'Police Clearance', icon: ShieldCheck },
  { name: 'Land Services', icon: Home },
  { name: 'More Services', icon: LayoutGrid },
];

const TRUST_ITEMS = [
  {
    icon: Accessibility,
    title: 'Accessible for Everyone',
    sub: 'Voice, text, screen reader and more.',
  },
  {
    icon: Lock,
    title: 'Secure & Private',
    sub: 'Your information is protected at all times.',
  },
  {
    icon: Heart,
    title: 'Built for Kenyans',
    sub: 'Designed with you in mind, for a better experience.',
  },
];

/* Footer navigation.
 *
 * `href` is present ONLY where a real destination already exists in this
 * project. Every other entry is a label from the approved footer design whose
 * page/route does not exist yet, so it is rendered as plain text — never as a
 * <Link>, <a> or <button>. That matters for two reasons:
 *
 *   1. The router's catch-all ("*") redirects unknown paths to /login, so a
 *      <Link to="/about"> would silently dump visitors on the sign-in screen.
 *   2. A focusable control that does nothing misleads keyboard and screen
 *      reader users.
 *
 * "Accessibility" is one of these labels: the accessibility settings system
 * does not exist, so this is a visual entry point only — exactly like the
 * Accessibility control in the header. Add an `href` (or swap in a <Link>)
 * here as each page ships.
 *
 * Contact Us reuses the support address the app already publishes on
 * ForgotPasswordPage — no new destination was invented for it.
 * Services are deliberately absent: they have their own Popular Services
 * section above and are not duplicated here.
 */
const FOOTER_COLUMNS: Array<{
  heading: string;
  items: Array<{ label: string; href?: string }>;
}> = [
  {
    heading: 'Rafiki',
    items: [
      { label: 'About Rafiki' },
      { label: 'How it Works' },
      { label: 'Accessibility' },
      { label: 'Our Impact' },
    ],
  },
  {
    heading: 'Support',
    items: [
      { label: 'Help Center' },
      { label: 'FAQs' },
      { label: 'Contact Us', href: 'mailto:support@rafiki.ai' },
      { label: 'Feedback' },
    ],
  },
  {
    heading: 'Legal',
    items: [
      { label: 'Privacy Policy' },
      { label: 'Terms of Use' },
      { label: 'Security' },
    ],
  },
];

export function LandingPage() {
  return (
    <div
      className="rl-page min-h-screen flex flex-col font-dm-sans"
      style={{
        backgroundColor: '#F8F3E7',
        backgroundImage:
          'repeating-linear-gradient(45deg, rgba(27,67,50,0.010) 0 2px, transparent 2px 16px),' +
          'repeating-linear-gradient(-45deg, rgba(200,134,10,0.008) 0 2px, transparent 2px 16px)',
      }}
    >
      {/* Header — fixed/persistent. No scroll listeners, no scroll-driven
          resize or transform; .rl-page reserves the offset so content is
          never overlapped. */}
      <header className="rl-header">
        <div className="rl-header-inner">
          {/* Brand: existing RafikiLogo component (unmodified) + tagline.
              Route target unchanged ("/"). */}
          <Link to="/" className="rl-brand" aria-label="Rafiki — AI Government Assistant, home">
            <RafikiLogo size={30} />
            <span className="rl-brand-tagline">AI Government Assistant</span>
          </Link>

          <nav className="rl-controls" aria-label="Site">
            {/* Language + Accessibility are presentation-only entry points.
                Neither was wired before this redesign and neither is wired
                now: there is no translation system for this page, and the
                accessibility settings system does not exist yet. Both are
                intentionally left without an onClick handler so nothing
                claims to work that does not. Wiring them is a separate task. */}
            <button type="button" className="rl-control" aria-label="Language: English">
              <Globe size={19} aria-hidden="true" />
              <span className="rl-control-label">English</span>
              <ChevronDown size={16} aria-hidden="true" className="rl-control-chevron" />
            </button>

            <span className="rl-divider" aria-hidden="true" />

            <button
              type="button"
              className="rl-control rl-control-muted rl-control-kiswahili"
              aria-label="Language: Kiswahili"
            >
              <span className="rl-control-label">Kiswahili</span>
            </button>

            <span className="rl-divider" aria-hidden="true" />

            <button type="button" className="rl-control" aria-label="Accessibility">
              <Accessibility size={19} aria-hidden="true" />
              <span className="rl-control-label">Accessibility</span>
            </button>

            <span className="rl-divider" aria-hidden="true" />

            {/* Voice Mode — reuses the existing voice entry point: the same
                `/login` navigation the hero's voice call to action performs,
                because voice lives behind authentication. No new behaviour. */}
            <Link to="/login" className="rl-voice">
              <span className="rl-voice-label">Sign up</span>
            </Link>
          </nav>
        </div>
      </header>

      <main className="flex-1">
        {/* Hero */}
        <section className="rl-hero" aria-labelledby="hero-heading">
          <div className="rl-hero-inner">
            <div className="rl-hero-copy">
              <p className="rl-hero-pill">
                <ShieldCheck size={18} aria-hidden="true" />
                Rafiki is a secure assistant that helps you access government services on eCitizen.
              </p>

              <h1 id="hero-heading" className="rl-hero-title">
                Hello, I'm Rafiki.
                <span className="rl-hero-title-accent">How can I help you today?</span>
              </h1>

              <p className="rl-hero-lede">
                I make it easy to access government services. Just tell me what you need,
                and I'll take care of the rest.
              </p>

              <div className="rl-hero-actions">
                {/* Route unchanged: /login — same navigation as before. */}
                <Link to="/login" className="rl-hero-cta rl-hero-cta-primary">
                  <Mic size={26} strokeWidth={1.75} aria-hidden="true" />
                  <span>
                    <span className="rl-hero-cta-title">Speak to Rafiki</span>
                    <span className="rl-hero-cta-sub">(Voice Input)</span>
                  </span>
                </Link>
                {/* Route unchanged: /login — same navigation as before. */}
                <Link to="/login" className="rl-hero-cta rl-hero-cta-secondary">
                  <Keyboard size={26} strokeWidth={1.75} aria-hidden="true" />
                  <span>
                    <span className="rl-hero-cta-title">Type your request</span>
                    <span className="rl-hero-cta-sub">(Text Input)</span>
                  </span>
                </Link>
              </div>

              <p className="rl-hero-assure">
                <ShieldCheck size={20} strokeWidth={1.75} aria-hidden="true" />
                <span>
                  Your data is private and secure.
                  <br />
                  You're always in control.
                </span>
              </p>
            </div>

            <figure className="rl-hero-figure">
              <img
                src="/images/hero-citizens.png"
                alt="Four Kenyan citizens using Rafiki on their phones — an older man in a flat cap, a young woman in glasses, a man seated in a wheelchair, and a woman in a patterned headwrap — in front of the Kenyan flag."
                className="rl-hero-art"
                width={612}
                height={408}
                onError={(e) => {
                  const img = e.currentTarget;
                  img.style.display = 'none';
                  img.nextElementSibling?.classList.replace('hidden', 'flex');
                }}
              />
              <div
                className="hidden w-72 h-72 lg:w-80 lg:h-80 rounded-full items-center justify-center"
                style={{
                  background:
                    'radial-gradient(circle at 50% 40%, rgba(45,106,79,0.14), rgba(200,134,10,0.08) 70%, transparent)',
                }}
              >
                <RafikiLogo size={56} />
              </div>
            </figure>
          </div>
        </section>

        {/* Services */}
        <section className="rl-services" aria-labelledby="services-heading">
          <div className="rl-services-inner">
            <div className="rl-services-head">
              <h2 id="services-heading" className="rl-services-title">
                Popular Services
              </h2>
              <p className="rl-services-sub">Tell me which service you need help with.</p>
            </div>

            <ul className="rl-services-grid">
              {SERVICES.map(({ name, icon: Icon }) => (
                <li key={name}>
                  {/* Route unchanged: /login — same navigation as before. */}
                  <Link to="/login" className="rl-service-card">
                    <Icon size={32} strokeWidth={1.75} aria-hidden="true" />
                    <span className="rl-service-name">{name}</span>
                  </Link>
                </li>
              ))}
            </ul>

            <p className="rl-services-more">
              <Headset size={22} strokeWidth={1.75} aria-hidden="true" />
              <span className="rl-services-more-text">
                Rafiki can also help you with NHIF (SHA), KRA, HELB, eAIMS, and more.
              </span>
              <span className="rl-services-more-cue">Just ask.</span>
            </p>
          </div>
        </section>
      </main>

      <footer className="rl-footer">
        {/* Trust / benefits band — one shared treatment for all three items,
            no per-item colour. */}
        <div className="rl-trust">
          <div className="rl-trust-inner">
            <ul className="rl-trust-list">
              {TRUST_ITEMS.map(({ icon: Icon, title, sub }) => (
                <li key={title} className="rl-trust-item">
                  <span className="rl-trust-icon">
                    <Icon size={28} strokeWidth={1.75} aria-hidden="true" />
                  </span>
                  <span className="rl-trust-copy">
                    <span className="rl-trust-title">{title}</span>
                    <span className="rl-trust-sub">{sub}</span>
                  </span>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Deep-green footer */}
        <div className="rl-footer-main">
          {/* Kenyan flag stripe — same treatment as the auth pages' footer
              strip, sitting above the link columns. */}
          <div className="rl-footer-stripe" aria-hidden="true" />

          <div className="rl-footer-inner">
            <div className="rl-footer-grid">
              <div className="rl-footer-brand">
                {/* Same RafikiLogo the header uses, in its own flag colours.
                    It sits on a light chip so those colours stay legible on
                    the dark green — see .rl-footer-logo in styles/landing.css. */}
                <span className="rl-footer-logo">
                  <RafikiLogo size={44} />
                </span>
                <span className="rl-footer-tagline">AI Government Assistant</span>
                <p className="rl-footer-about">
                  Rafiki is your AI companion for navigating Kenya's government
                  services with ease.
                </p>
              </div>

              {FOOTER_COLUMNS.map(({ heading, items }) => (
                <div key={heading} className="rl-footer-col">
                  <h2 className="rl-footer-col-title">{heading}</h2>
                  <ul className="rl-footer-col-list">
                    {items.map(({ label, href }) => (
                      <li key={label}>
                        {href ? (
                          <a href={href} className="rl-footer-link">
                            {label}
                          </a>
                        ) : (
                          /* No destination exists yet — plain text, so it is
                             neither focusable nor clickable. */
                          <span className="rl-footer-label">{label}</span>
                        )}
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>

            <div className="rl-footer-bottom">
              <p className="rl-footer-assurance">
                <ShieldCheck size={21} strokeWidth={1.75} aria-hidden="true" />
                Trusted. Secure. Always here for you.
              </p>

              <p className="rl-footer-copyright">
                © {new Date().getFullYear()} Rafiki. All rights reserved.
              </p>

              {/* Language entry point. As in the header, no translation system
                  exists, so these carry no handler and nothing here claims the
                  page has been translated. */}
              <div className="rl-footer-lang">
                <Globe size={19} aria-hidden="true" />
                <button
                  type="button"
                  className="rl-footer-lang-btn"
                  aria-label="Language: English"
                >
                  English
                </button>
                <span className="rl-footer-lang-sep" aria-hidden="true" />
                <button
                  type="button"
                  className="rl-footer-lang-btn rl-footer-lang-btn-muted"
                  aria-label="Language: Kiswahili"
                >
                  Kiswahili
                </button>
              </div>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default LandingPage;
