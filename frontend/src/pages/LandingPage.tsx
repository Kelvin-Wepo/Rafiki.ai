/**
 * LandingPage — public marketing home ("/" for unauthenticated visitors).
 * eCitizen-green redesign: hero + service grid + trust footer.
 */

import { Link } from 'react-router-dom';
import {
  Mic,
  MessageSquare,
  ShieldCheck,
  FileText,
  Car,
  Briefcase,
  Baby,
  Shield,
  Home,
  Globe,
  PersonStanding,
  Clock,
  Heart,
} from 'lucide-react';
import { RafikiLogo } from '../components/RafikiLogo';
import '../styles/auth.css';

const SERVICES = [
  { label: 'Apply for', name: 'Passport', desc: 'New applications & renewals', icon: FileText, bg: '#17603A' },
  { label: 'Renew', name: 'Driving Licence', desc: 'Book your NTSA slot', icon: Car, bg: '#C8860A' },
  { label: 'Register', name: 'Business', desc: 'Names, permits & filings', icon: Briefcase, bg: '#17603A' },
  { label: 'Birth', name: 'Certificate', desc: 'Order official copies', icon: Baby, bg: '#C8102E' },
  { label: 'Police', name: 'Clearance', desc: 'Good conduct certificate', icon: Shield, bg: '#161616' },
  { label: 'Land', name: 'Services', desc: 'Searches & land rates', icon: Home, bg: '#C8860A' },
];

const TRUST_ITEMS = [
  { icon: ShieldCheck, title: 'Secure', sub: 'Your data is protected' },
  { icon: PersonStanding, title: 'Accessible', sub: 'For everyone, everywhere' },
  { icon: Clock, title: 'Reliable', sub: 'Always here to help' },
  { icon: Heart, title: 'Kenyan', sub: 'Built for Kenyans' },
];

export function LandingPage() {
  return (
    <div
      className="min-h-screen flex flex-col font-dm-sans"
      style={{
        backgroundColor: '#F8F3E7',
        backgroundImage:
          'repeating-linear-gradient(45deg, rgba(27,67,50,0.010) 0 2px, transparent 2px 16px),' +
          'repeating-linear-gradient(-45deg, rgba(200,134,10,0.008) 0 2px, transparent 2px 16px)',
      }}
    >
      {/* Header */}
      <header className="bg-white/90 shadow-sm">
        <div className="max-w-6xl mx-auto flex items-center justify-between px-4 py-3">
          <Link to="/" aria-label="Rafiki home">
            <RafikiLogo size={26} />
          </Link>
          <nav className="flex items-center gap-2 sm:gap-3" aria-label="Site">
            {/* TODO: wire language + accessibility settings */}
            <button
              type="button"
              className="hidden sm:inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm text-gray-700 hover:bg-gray-100"
            >
              <Globe size={16} aria-hidden="true" /> English
            </button>
            <button
              type="button"
              className="hidden sm:inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm text-gray-700 hover:bg-gray-100"
            >
              <PersonStanding size={16} aria-hidden="true" /> Accessibility
            </button>
            <Link
              to="/login"
              className="inline-flex items-center px-5 py-2 rounded-lg text-sm font-semibold text-white"
              style={{ background: 'var(--rafiki-green-deep)' }}
            >
              Sign in
            </Link>
          </nav>
        </div>
      </header>

      <main className="flex-1">
        {/* Hero */}
        <section className="max-w-6xl mx-auto px-4 pt-4 pb-0 grid md:grid-cols-2 gap-4 items-center">
          <div>
            <span
              className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full text-sm font-medium mb-4"
              style={{ background: '#F3EAD3', color: '#4B3A12' }}
            >
              🇰🇪 Proudly built for Kenya
            </span>
            <h1 className="font-playfair text-4xl lg:text-5xl leading-tight text-gray-900 mb-3">
              Your AI Assistant<br />
              for <span style={{ color: 'var(--rafiki-green-deep)' }}>Government<br />Services</span>
            </h1>
            <p className="text-base text-gray-600 max-w-md mb-5">
              Tell Rafiki what you need, and I'll handle the rest. Fast, simple, secure.
            </p>
            <div className="flex flex-wrap gap-3 mb-4">
              <Link
                to="/login"
                className="inline-flex items-center gap-2 px-6 py-3.5 rounded-xl font-semibold text-white"
                style={{ background: 'var(--rafiki-green-deep)' }}
              >
                <Mic size={18} aria-hidden="true" />
                <span>
                  Ask Rafiki
                  <span className="block text-xs font-normal opacity-80">(Voice)</span>
                </span>
              </Link>
              <Link
                to="/login"
                className="inline-flex items-center gap-2 px-6 py-3.5 rounded-xl font-semibold bg-white text-gray-800 border border-gray-200"
              >
                <MessageSquare size={18} aria-hidden="true" />
                Type your request
              </Link>
            </div>
            <p className="flex items-center gap-2 text-sm text-gray-500 max-w-xs">
              <ShieldCheck size={18} aria-hidden="true" style={{ color: 'var(--rafiki-green-deep)' }} />
              Your data is secure and will only be used with your permission.
            </p>
          </div>

          <div className="relative flex items-center justify-center" aria-hidden="true">
            <img
              src="/rafiki-mascot.png"
              alt=""
              className="landing-mascot w-120 lg:w-xl max-w-full mix-blend-multiply -my-8"
              style={{
                WebkitMaskImage:
                  'radial-gradient(ellipse 74% 72% at 50% 46%, black 60%, transparent 97%)',
                maskImage:
                  'radial-gradient(ellipse 74% 72% at 50% 46%, black 60%, transparent 97%)',
              }}
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
            {/* Greeting bubble */}
            <div
              className="absolute -bottom-6 left-1/2 -translate-x-1/2 bg-white rounded-2xl px-7 py-4 text-center whitespace-nowrap"
              style={{ boxShadow: '0 10px 32px rgba(27, 67, 50, 0.12)' }}
            >
              <p className="font-semibold text-gray-900">👋 Habari, I'm Rafiki</p>
              <p className="text-sm text-gray-500">How can I help you today?</p>
            </div>
          </div>
        </section>

        {/* Services */}
        <section className="max-w-6xl mx-auto px-4 pt-4 pb-4" aria-labelledby="services-heading">
          <h2 id="services-heading" className="sr-only">
            Popular services
          </h2>
          <ul className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4 list-none p-0">
            {SERVICES.map(({ label, name, desc, icon: Icon, bg }) => (
              <li key={name}>
                <Link
                  to="/login"
                  className="flex flex-col items-center gap-3 bg-white rounded-2xl border border-gray-100 shadow-sm px-4 py-6 text-center transition-all duration-200 hover:shadow-lg hover:-translate-y-1 h-full"
                >
                  <span
                    className="w-16 h-16 rounded-full flex items-center justify-center"
                    style={{ background: bg }}
                  >
                    <Icon size={28} color="white" aria-hidden="true" />
                  </span>
                  <span className="text-sm text-gray-700 leading-snug">
                    {label}
                    <strong className="block text-gray-900">{name}</strong>
                  </span>
                  <span className="text-xs text-gray-400 leading-snug">{desc}</span>
                </Link>
              </li>
            ))}
          </ul>
          <p
            className="mt-4 mx-auto w-fit px-6 py-2.5 rounded-full text-sm"
            style={{ background: '#F3EAD3', color: '#4B3A12' }}
          >
            ✨ More services coming soon. Tell me what you need!
          </p>
        </section>
      </main>

      {/* Trust footer */}
      <footer style={{ background: 'var(--rafiki-green-ink)' }}>
        <div className="max-w-6xl mx-auto px-4 py-5 grid grid-cols-2 md:grid-cols-4 gap-6">
          {TRUST_ITEMS.map(({ icon: Icon, title, sub }) => (
            <div key={title} className="flex items-center gap-3 text-white">
              <Icon size={20} aria-hidden="true" className="shrink-0 opacity-90" />
              <span>
                <span className="block text-sm font-semibold">{title}</span>
                <span className="block text-xs opacity-75">{sub}</span>
              </span>
            </div>
          ))}
        </div>
        <div className="kenya-stripe" aria-hidden="true" />
      </footer>
    </div>
  );
}

export default LandingPage;
