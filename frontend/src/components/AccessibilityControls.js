/**
 * Accessibility Controls Component
 * Toggle controls for accessibility features
 */

import React from 'react';
import { useAccessibility } from '../context/AccessibilityContext';

function AccessibilityControls() {
  const { settings, toggleSetting, updateSetting, announce, speak } = useAccessibility();

  const handleToggle = (setting, label) => {
    toggleSetting(setting);
    const newState = !settings[setting];
    announce(`${label} ${newState ? 'enabled' : 'disabled'}`);
  };

  const handleLanguageChange = (lang) => {
    updateSetting('language', lang);
    const langName = lang === 'sw' ? 'Kiswahili' : 'English';
    announce(`Language changed to ${langName}`);
    
    // Speak confirmation in the selected language
    if (lang === 'sw') {
      speak('Lugha imebadilishwa kuwa Kiswahili');
    } else {
      speak('Language changed to English');
    }
  };

  return (
    <div 
      className="accessibility-controls"
      role="group"
      aria-label="Accessibility controls"
    >
      {/* Language Selection */}
      <div className="language-selector" role="group" aria-label="Language selection">
        <button
          className={`accessibility-btn lang-btn ${settings.language === 'en' ? 'active' : ''}`}
          onClick={() => handleLanguageChange('en')}
          aria-pressed={settings.language === 'en'}
          title="Switch to English"
        >
          <span aria-hidden="true">EN</span>
          <span className="sr-only">English</span>
        </button>
        <button
          className={`accessibility-btn lang-btn ${settings.language === 'sw' ? 'active' : ''}`}
          onClick={() => handleLanguageChange('sw')}
          aria-pressed={settings.language === 'sw'}
          title="Badilisha kuwa Kiswahili"
        >
          <span aria-hidden="true">SW</span>
          <span className="sr-only">Kiswahili</span>
        </button>
      </div>

      <button
        className={`accessibility-btn ${settings.highContrast ? 'active' : ''}`}
        onClick={() => handleToggle('highContrast', 'High contrast mode')}
        aria-pressed={settings.highContrast}
        title="Toggle high contrast mode"
      >
        <svg 
          width="20" 
          height="20" 
          viewBox="0 0 24 24" 
          fill="currentColor"
          aria-hidden="true"
        >
          <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18V4c4.41 0 8 3.59 8 8s-3.59 8-8 8z"/>
        </svg>
        <span className="sr-only">High Contrast</span>
      </button>

      <button
        className={`accessibility-btn ${settings.largeText ? 'active' : ''}`}
        onClick={() => handleToggle('largeText', 'Large text mode')}
        aria-pressed={settings.largeText}
        title="Toggle large text mode"
      >
        <svg 
          width="20" 
          height="20" 
          viewBox="0 0 24 24" 
          fill="currentColor"
          aria-hidden="true"
        >
          <path d="M9 4v3h5v12h3V7h5V4H9zm-6 8h3v7h3v-7h3V9H3v3z"/>
        </svg>
        <span className="sr-only">Large Text</span>
      </button>

      <button
        className={`accessibility-btn ${settings.voiceEnabled ? 'active' : ''}`}
        onClick={() => handleToggle('voiceEnabled', 'Voice feedback')}
        aria-pressed={settings.voiceEnabled}
        title="Toggle voice feedback"
      >
        <svg 
          width="20" 
          height="20" 
          viewBox="0 0 24 24" 
          fill="currentColor"
          aria-hidden="true"
        >
          <path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02zM14 3.23v2.06c2.89.86 5 3.54 5 6.71s-2.11 5.85-5 6.71v2.06c4.01-.91 7-4.49 7-8.77s-2.99-7.86-7-8.77z"/>
        </svg>
        <span className="sr-only">Voice Feedback</span>
      </button>
    </div>
  );
}

export default AccessibilityControls;
