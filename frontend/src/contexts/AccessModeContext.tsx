import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from 'react';
import {
  isAccessModeEnabled,
  isAccessSpeakEnabled,
  readAccessLang,
  setAccessModeEnabled,
  setAccessSpeakEnabled,
  writeAccessLang,
  type AccessLang,
} from '../lib/accessMode';

type AccessModeContextValue = {
  enabled: boolean;
  language: AccessLang;
  speakOn: boolean;
  enable: () => void;
  disable: () => void;
  setLanguage: (lang: AccessLang) => void;
  setSpeakOn: (on: boolean) => void;
  speak: (text: string) => void;
  stopSpeaking: () => void;
};

const AccessModeContext = createContext<AccessModeContextValue | undefined>(undefined);

function cancelSpeech() {
  if (typeof window === 'undefined' || !window.speechSynthesis) return;
  window.speechSynthesis.cancel();
}

export function AccessModeProvider({ children }: { children: ReactNode }) {
  const [enabled, setEnabled] = useState(() => isAccessModeEnabled());
  const [language, setLanguageState] = useState<AccessLang>(() => readAccessLang());
  const [speakOn, setSpeakOnState] = useState(() => isAccessSpeakEnabled());

  const enable = useCallback(() => {
    setAccessModeEnabled(true);
    setEnabled(true);
  }, []);

  const disable = useCallback(() => {
    setAccessModeEnabled(false);
    setEnabled(false);
    cancelSpeech();
  }, []);

  const setLanguage = useCallback((lang: AccessLang) => {
    writeAccessLang(lang);
    setLanguageState(lang);
  }, []);

  const setSpeakOn = useCallback((on: boolean) => {
    setAccessSpeakEnabled(on);
    setSpeakOnState(on);
    if (!on) cancelSpeech();
  }, []);

  const speak = useCallback(
    (text: string) => {
      if (!speakOn || !text.trim() || typeof window === 'undefined' || !window.speechSynthesis) {
        return;
      }
      cancelSpeech();
      const utterance = new SpeechSynthesisUtterance(text.trim());
      utterance.lang = language === 'sw' ? 'sw-KE' : 'en-KE';
      utterance.rate = 0.92;
      window.speechSynthesis.speak(utterance);
    },
    [language, speakOn]
  );

  const value = useMemo(
    () => ({
      enabled,
      language,
      speakOn,
      enable,
      disable,
      setLanguage,
      setSpeakOn,
      speak,
      stopSpeaking: cancelSpeech,
    }),
    [disable, enable, enabled, language, setLanguage, setSpeakOn, speak, speakOn]
  );

  return <AccessModeContext.Provider value={value}>{children}</AccessModeContext.Provider>;
}

export function useAccessMode() {
  const ctx = useContext(AccessModeContext);
  if (!ctx) {
    throw new Error('useAccessMode must be used within AccessModeProvider');
  }
  return ctx;
}
