/**
 * Language Toggle Component - Kenya National Design System
 * English / Kiswahili language selector
 */

import { useState, useRef, useEffect, type KeyboardEvent } from 'react';
import { Globe, Check, ChevronDown } from 'lucide-react';

export type Language = 'en' | 'sw';

export interface LanguageOption {
  code: Language;
  name: string;
  nativeName: string;
  flag: string;
}

const languages: LanguageOption[] = [
  { code: 'en', name: 'English', nativeName: 'English', flag: '🇬🇧' },
  { code: 'sw', name: 'Kiswahili', nativeName: 'Kiswahili', flag: '🇰🇪' },
];

export interface LanguageToggleProps {
  currentLanguage: Language;
  onChange: (language: Language) => void;
  variant?: 'dropdown' | 'toggle';
  size?: 'sm' | 'md';
}

export function LanguageToggle({
  currentLanguage,
  onChange,
  variant = 'dropdown',
  size = 'md',
}: LanguageToggleProps) {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const currentLang = languages.find(l => l.code === currentLanguage) || languages[0];

  // Close on click outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleKeyDown = (e: KeyboardEvent) => {
    if (e.key === 'Escape') {
      setIsOpen(false);
    } else if (e.key === 'ArrowDown' && !isOpen) {
      e.preventDefault();
      setIsOpen(true);
    }
  };

  const handleSelect = (code: Language) => {
    onChange(code);
    setIsOpen(false);
  };

  // Toggle variant (simple switch)
  if (variant === 'toggle') {
    return (
      <div
        role="radiogroup"
        aria-label="Select language"
        className="inline-flex rounded-lg bg-[var(--ke-gray-100)] p-1"
      >
        {languages.map((lang) => (
          <button
            key={lang.code}
            role="radio"
            aria-checked={currentLanguage === lang.code}
            onClick={() => onChange(lang.code)}
            className={`
              px-3 py-1.5 text-sm font-medium rounded-md transition-all
              focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--ke-green)]
              ${currentLanguage === lang.code
                ? 'bg-white text-[var(--ke-gray-900)] shadow-sm'
                : 'text-[var(--ke-gray-600)] hover:text-[var(--ke-gray-900)]'
              }
            `}
          >
            <span className="mr-1.5">{lang.flag}</span>
            {lang.code.toUpperCase()}
          </button>
        ))}
      </div>
    );
  }

  // Dropdown variant
  const sizeClasses = {
    sm: 'px-2.5 py-1.5 text-sm min-h-[36px]',
    md: 'px-3 py-2 text-base min-h-[44px]',
  };

  return (
    <div ref={dropdownRef} className="relative">
      <button
        type="button"
        aria-haspopup="listbox"
        aria-expanded={isOpen}
        aria-label={`Language: ${currentLang.name}`}
        onClick={() => setIsOpen(!isOpen)}
        onKeyDown={handleKeyDown}
        className={`
          inline-flex items-center gap-2 rounded-lg border border-[var(--ke-gray-300)]
          bg-white hover:bg-[var(--ke-gray-50)] transition-colors
          focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--ke-green)]
          ${sizeClasses[size]}
        `}
      >
        <Globe className="w-4 h-4 text-[var(--ke-gray-500)]" aria-hidden="true" />
        <span className="font-medium">{currentLang.flag} {currentLang.code.toUpperCase()}</span>
        <ChevronDown
          className={`w-4 h-4 text-[var(--ke-gray-400)] transition-transform ${isOpen ? 'rotate-180' : ''}`}
          aria-hidden="true"
        />
      </button>

      {isOpen && (
        <ul
          role="listbox"
          aria-label="Select language"
          className="absolute right-0 mt-1 w-48 py-1 bg-white rounded-lg border border-[var(--ke-gray-200)] shadow-lg z-[var(--z-dropdown)]"
        >
          {languages.map((lang) => (
            <li
              key={lang.code}
              role="option"
              aria-selected={currentLanguage === lang.code}
              onClick={() => handleSelect(lang.code)}
              className={`
                flex items-center justify-between px-3 py-2 cursor-pointer
                ${currentLanguage === lang.code
                  ? 'bg-[var(--ke-green-bg)] text-[var(--ke-green)]'
                  : 'hover:bg-[var(--ke-gray-50)]'
                }
              `}
            >
              <span className="flex items-center gap-2">
                <span>{lang.flag}</span>
                <span className="font-medium">{lang.nativeName}</span>
              </span>
              {currentLanguage === lang.code && (
                <Check className="w-4 h-4" aria-hidden="true" />
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default LanguageToggle;
