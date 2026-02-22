/**
 * Government Footer Component - Kenya National Design System
 * Official footer with government links and accessibility info
 */

import { KenyaFlagStripe, KenyaShieldIcon } from '../ui/KenyaBranding';
import type { Language } from '../ui/LanguageToggle';

interface GovFooterProps {
  language?: Language;
}

export function GovFooter({ language = 'en' }: GovFooterProps) {
  const content = {
    en: {
      tagline: 'Your trusted AI assistant for government services',
      quickLinks: 'Quick Links',
      services: 'Services',
      about: 'About Rafiki',
      help: 'Help Center',
      contact: 'Contact Us',
      legal: 'Legal',
      privacy: 'Privacy Policy',
      terms: 'Terms of Service',
      accessibility: 'Accessibility',
      cookies: 'Cookie Policy',
      support: 'Support',
      feedback: 'Give Feedback',
      reportIssue: 'Report an Issue',
      faq: 'FAQs',
      copyright: '© 2026 Rafiki.ai. All rights reserved.',
      govNotice: 'A Government of Kenya digital initiative.',
      voiceNotice: 'This service uses voice recognition. By using this service, you consent to audio processing for improved service delivery.',
    },
    sw: {
      tagline: 'Msaidizi wako wa AI wa kuamini kwa huduma za serikali',
      quickLinks: 'Viungo vya Haraka',
      services: 'Huduma',
      about: 'Kuhusu Rafiki',
      help: 'Kituo cha Msaada',
      contact: 'Wasiliana Nasi',
      legal: 'Kisheria',
      privacy: 'Sera ya Faragha',
      terms: 'Masharti ya Huduma',
      accessibility: 'Upatikanaji',
      cookies: 'Sera ya Kuki',
      support: 'Msaada',
      feedback: 'Toa Maoni',
      reportIssue: 'Ripoti Tatizo',
      faq: 'Maswali Yanayoulizwa Mara kwa Mara',
      copyright: '© 2026 Rafiki.ai. Haki zote zimehifadhiwa.',
      govNotice: 'Mpango wa kidijitali wa Serikali ya Kenya.',
      voiceNotice: 'Huduma hii inatumia utambuzi wa sauti. Kwa kutumia huduma hii, unakubali usindikaji wa sauti kwa utoaji bora wa huduma.',
    },
  };

  const t = content[language];

  return (
    <footer className="bg-[var(--ke-gray-900)] text-white">
      {/* Main footer content */}
      <div className="container py-12">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          {/* Brand column */}
          <div className="lg:col-span-1">
            <div className="flex items-center gap-3 mb-4">
              <KenyaShieldIcon size={40} />
              <div>
                <h2 className="text-xl font-bold">Rafiki.ai</h2>
              </div>
            </div>
            <p className="text-[var(--ke-gray-400)] text-sm mb-4">
              {t.tagline}
            </p>
            <p className="text-[var(--ke-gray-500)] text-xs">
              {t.govNotice}
            </p>
          </div>

          {/* Quick Links */}
          <div>
            <h3 className="font-semibold text-white mb-4">{t.quickLinks}</h3>
            <ul className="space-y-2">
              <li>
                <a href="#services" className="text-[var(--ke-gray-400)] hover:text-white text-sm transition-colors">
                  {t.services}
                </a>
              </li>
              <li>
                <a href="#about" className="text-[var(--ke-gray-400)] hover:text-white text-sm transition-colors">
                  {t.about}
                </a>
              </li>
              <li>
                <a href="#help" className="text-[var(--ke-gray-400)] hover:text-white text-sm transition-colors">
                  {t.help}
                </a>
              </li>
              <li>
                <a href="#contact" className="text-[var(--ke-gray-400)] hover:text-white text-sm transition-colors">
                  {t.contact}
                </a>
              </li>
            </ul>
          </div>

          {/* Legal */}
          <div>
            <h3 className="font-semibold text-white mb-4">{t.legal}</h3>
            <ul className="space-y-2">
              <li>
                <a href="#privacy" className="text-[var(--ke-gray-400)] hover:text-white text-sm transition-colors">
                  {t.privacy}
                </a>
              </li>
              <li>
                <a href="#terms" className="text-[var(--ke-gray-400)] hover:text-white text-sm transition-colors">
                  {t.terms}
                </a>
              </li>
              <li>
                <a href="#accessibility" className="text-[var(--ke-gray-400)] hover:text-white text-sm transition-colors">
                  {t.accessibility}
                </a>
              </li>
              <li>
                <a href="#cookies" className="text-[var(--ke-gray-400)] hover:text-white text-sm transition-colors">
                  {t.cookies}
                </a>
              </li>
            </ul>
          </div>

          {/* Support */}
          <div>
            <h3 className="font-semibold text-white mb-4">{t.support}</h3>
            <ul className="space-y-2">
              <li>
                <a href="#feedback" className="text-[var(--ke-gray-400)] hover:text-white text-sm transition-colors">
                  {t.feedback}
                </a>
              </li>
              <li>
                <a href="#report" className="text-[var(--ke-gray-400)] hover:text-white text-sm transition-colors">
                  {t.reportIssue}
                </a>
              </li>
              <li>
                <a href="#faq" className="text-[var(--ke-gray-400)] hover:text-white text-sm transition-colors">
                  {t.faq}
                </a>
              </li>
            </ul>
          </div>
        </div>

        {/* Voice/Privacy notice */}
        <div className="mt-8 pt-8 border-t border-[var(--ke-gray-800)]">
          <div className="bg-[var(--ke-gray-800)] rounded-lg p-4">
            <p className="text-xs text-[var(--ke-gray-400)] flex items-start gap-2">
              <span className="text-[var(--ke-green)] font-bold text-sm">🔒</span>
              {t.voiceNotice}
            </p>
          </div>
        </div>
      </div>

      {/* Bottom bar */}
      <div className="border-t border-[var(--ke-gray-800)]">
        <div className="container py-4">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
            <p className="text-xs text-[var(--ke-gray-500)]">
              {t.copyright}
            </p>
            <div className="flex items-center gap-4">
              <span className="text-xs text-[var(--ke-gray-500)]">🇰🇪 Kenya</span>
            </div>
          </div>
        </div>
      </div>

      {/* Kenya flag stripe at bottom */}
      <KenyaFlagStripe />
    </footer>
  );
}

export default GovFooter;
