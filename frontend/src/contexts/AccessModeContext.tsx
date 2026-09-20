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
import { playElevenLabsText, stopElevenLabsAudio } from '../lib/elevenlabsAudio';

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
    stopElevenLabsAudio();
  }, []);

  const setLanguage = useCallback((lang: AccessLang) => {
    writeAccessLang(lang);
    setLanguageState(lang);
  }, []);

  const setSpeakOn = useCallback((on: boolean) => {
    setAccessSpeakEnabled(on);
    setSpeakOnState(on);
    if (!on) stopElevenLabsAudio();
  }, []);

  const speak = useCallback(
    (text: string) => {
      if (!speakOn || !text.trim()) return;
      void playElevenLabsText(text);
    },
    [speakOn]
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
      stopSpeaking: stopElevenLabsAudio,
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
