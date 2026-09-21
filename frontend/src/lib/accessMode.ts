const ACCESS_MODE_KEY = 'rafiki_access_mode';
const ACCESS_LANG_KEY = 'rafiki_access_lang';
const ACCESS_SPEAK_KEY = 'rafiki_access_speak';

export type AccessLang = 'en' | 'sw';

function readFlag(key: string, fallback: boolean): boolean {
  try {
    const stored = localStorage.getItem(key);
    if (stored === '1') return true;
    if (stored === '0') return false;
  } catch {
    /* ignore */
  }
  return fallback;
}

export function isAccessModeEnabled(): boolean {
  return readFlag(ACCESS_MODE_KEY, false);
}

export function setAccessModeEnabled(on: boolean): void {
  try {
    localStorage.setItem(ACCESS_MODE_KEY, on ? '1' : '0');
  } catch {
    /* ignore */
  }
}

export function readAccessLang(): AccessLang {
  try {
    return localStorage.getItem(ACCESS_LANG_KEY) === 'sw' ? 'sw' : 'en';
  } catch {
    return 'en';
  }
}

export function writeAccessLang(lang: AccessLang): void {
  try {
    localStorage.setItem(ACCESS_LANG_KEY, lang);
  } catch {
    /* ignore */
  }
}

export function isAccessSpeakEnabled(): boolean {
  return readFlag(ACCESS_SPEAK_KEY, true);
}

export function setAccessSpeakEnabled(on: boolean): void {
  try {
    localStorage.setItem(ACCESS_SPEAK_KEY, on ? '1' : '0');
  } catch {
    /* ignore */
  }
}
