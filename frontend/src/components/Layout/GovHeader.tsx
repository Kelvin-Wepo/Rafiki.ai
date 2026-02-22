/**
 * Government Header Component - Kenya National Design System
 * Official header with app name, tagline, and quick links
 */

import { useState } from 'react';
import { Menu, User, HelpCircle, LogOut, ChevronDown } from 'lucide-react';
import { KenyaFlagStripe, KenyaShieldIcon } from '../ui/KenyaBranding';
import { LanguageToggle, type Language } from '../ui/LanguageToggle';
import type { User as UserType } from '../../services/authService';

interface GovHeaderProps {
  user: UserType | null;
  onLogout: () => void;
  onMenuClick?: () => void;
  language: Language;
  onLanguageChange: (lang: Language) => void;
  showMobileMenu?: boolean;
}

export function GovHeader({
  user,
  onLogout,
  onMenuClick,
  language,
  onLanguageChange,
  showMobileMenu = true,
}: GovHeaderProps) {
  const [userMenuOpen, setUserMenuOpen] = useState(false);

  const tagline = language === 'sw' 
    ? 'Msaidizi wa Huduma za Serikali' 
    : 'Government Services Assistant';

  return (
    <header className="sticky top-0 z-[var(--z-sticky)] bg-white border-b border-[var(--ke-gray-200)]">
      {/* Kenya flag stripe at top */}
      <KenyaFlagStripe />
      
      <div className="container">
        <div className="flex items-center justify-between h-16">
          {/* Left: Logo and Title */}
          <div className="flex items-center gap-3">
            {showMobileMenu && (
              <button
                type="button"
                onClick={onMenuClick}
                className="lg:hidden p-2 -ml-2 text-[var(--ke-gray-600)] hover:text-[var(--ke-gray-900)] hover:bg-[var(--ke-gray-100)] rounded-lg transition-colors min-w-[44px] min-h-[44px] flex items-center justify-center"
                aria-label="Open navigation menu"
              >
                <Menu className="w-6 h-6" />
              </button>
            )}
            
            <a href="/" className="flex items-center gap-3 group">
              <KenyaShieldIcon size={36} className="flex-shrink-0" />
              <div>
                <h1 className="text-xl font-bold text-[var(--ke-black)] group-hover:text-[var(--ke-green)] transition-colors">
                  Rafiki.ai
                </h1>
                <p className="text-xs text-[var(--ke-gray-500)] hidden sm:block">
                  {tagline}
                </p>
              </div>
            </a>
          </div>

          {/* Center: Quick links (desktop) */}
          <nav className="hidden lg:flex items-center gap-6" aria-label="Main navigation">
            <a
              href="#services"
              className="text-sm font-medium text-[var(--ke-gray-600)] hover:text-[var(--ke-green)] transition-colors"
            >
              Services
            </a>
            <a
              href="#about"
              className="text-sm font-medium text-[var(--ke-gray-600)] hover:text-[var(--ke-green)] transition-colors"
            >
              About
            </a>
            <a
              href="#help"
              className="text-sm font-medium text-[var(--ke-gray-600)] hover:text-[var(--ke-green)] transition-colors flex items-center gap-1"
            >
              <HelpCircle className="w-4 h-4" />
              Help
            </a>
          </nav>

          {/* Right: Language + User */}
          <div className="flex items-center gap-2 sm:gap-4">
            <LanguageToggle
              currentLanguage={language}
              onChange={onLanguageChange}
              size="sm"
            />

            {user ? (
              <div className="relative">
                <button
                  type="button"
                  onClick={() => setUserMenuOpen(!userMenuOpen)}
                  className="flex items-center gap-2 p-2 text-[var(--ke-gray-700)] hover:bg-[var(--ke-gray-100)] rounded-lg transition-colors min-h-[44px]"
                  aria-haspopup="menu"
                  aria-expanded={userMenuOpen}
                >
                  <div className="w-8 h-8 rounded-full bg-[var(--ke-green)] flex items-center justify-center">
                    <User className="w-4 h-4 text-white" />
                  </div>
                  <span className="hidden sm:block text-sm font-medium max-w-[120px] truncate">
                    {user.phone_masked}
                  </span>
                  <ChevronDown className={`w-4 h-4 transition-transform ${userMenuOpen ? 'rotate-180' : ''}`} />
                </button>

                {userMenuOpen && (
                  <>
                    <div 
                      className="fixed inset-0 z-10" 
                      onClick={() => setUserMenuOpen(false)}
                      aria-hidden="true"
                    />
                    <div className="absolute right-0 mt-2 w-56 py-1 bg-white rounded-lg border border-[var(--ke-gray-200)] shadow-lg z-20">
                      <div className="px-4 py-3 border-b border-[var(--ke-gray-100)]">
                        <p className="text-sm font-medium text-[var(--ke-gray-900)]">
                          {user.phone_masked}
                        </p>
                        <p className="text-xs text-[var(--ke-gray-500)] mt-0.5">
                          {language === 'sw' ? 'Akaunti Imehakikiwa' : 'Verified Account'}
                        </p>
                      </div>
                      <button
                        type="button"
                        onClick={() => {
                          setUserMenuOpen(false);
                          onLogout();
                        }}
                        className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-[var(--ke-red)] hover:bg-[var(--ke-red-bg)] transition-colors"
                      >
                        <LogOut className="w-4 h-4" />
                        {language === 'sw' ? 'Ondoka' : 'Sign Out'}
                      </button>
                    </div>
                  </>
                )}
              </div>
            ) : (
              <a
                href="/login"
                className="inline-flex items-center px-4 py-2 text-sm font-semibold text-white bg-[var(--ke-green)] hover:bg-[var(--ke-green-dark)] rounded-lg transition-colors min-h-[44px]"
              >
                {language === 'sw' ? 'Ingia' : 'Sign In'}
              </a>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}

export default GovHeader;
