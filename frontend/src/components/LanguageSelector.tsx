/**
 * LanguageSelector.tsx
 * 
 * A bilingual greeting component that allows users to select
 * their preferred language (English or Kiswahili).
 * 
 * Shows on first load when language hasn't been set.
 */

import React from 'react';
import '../styles/dashboard.css';

interface LanguageSelectorProps {
  onSelectLanguage: (language: 'en' | 'sw') => void;
  isLoading?: boolean;
}

export const LanguageSelector: React.FC<LanguageSelectorProps> = ({ 
  onSelectLanguage, 
  isLoading = false 
}) => {
  return (
    <div className="language-selector-overlay">
      <div className="language-selector-card">
        {/* Kenya Flag Icon */}
        <div className="language-selector-icon">
          🇰🇪
        </div>
        
        {/* Bilingual Greeting */}
        <h2 className="language-selector-title">
          Welcome to Rafiki.ai!
        </h2>
        <h3 className="language-selector-subtitle">
          Karibu Rafiki.ai!
        </h3>
        
        {/* Language selection prompt */}
        <p className="language-selector-prompt">
          Please choose your language
          <br />
          Tafadhali chagua lugha yako
        </p>
        
        {/* Language buttons */}
        <div className="language-selector-buttons">
          <button
            className="language-btn language-btn-en"
            onClick={() => onSelectLanguage('en')}
            disabled={isLoading}
          >
            {isLoading ? 'Loading...' : 'English'}
          </button>
          <button
            className="language-btn language-btn-sw"
            onClick={() => onSelectLanguage('sw')}
            disabled={isLoading}
          >
            {isLoading ? 'Inapakia...' : 'Kiswahili'}
          </button>
        </div>
        
        {/* Rafiki mascot */}
        <div className="language-selector-mascot">
          <span className="mascot-emoji">🦁</span>
          <span className="mascot-name">Rafiki</span>
        </div>
      </div>
    </div>
  );
};

export default LanguageSelector;
