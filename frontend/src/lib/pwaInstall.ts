/**
 * Captures the browser install prompt as early as possible.
 *
 * Chrome/Edge fire `beforeinstallprompt` once; if a React component
 * mounts after that, the event is gone. Import this from main.tsx
 * before rendering so a one-tap Install button can still call prompt().
 */

export type BeforeInstallPromptEvent = Event & {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed'; platform: string }>;
};

export type PwaInstallOutcome = 'accepted' | 'dismissed' | 'unavailable';

const DISMISS_KEY = 'rafiki_pwa_install_dismissed';

let deferredPrompt: BeforeInstallPromptEvent | null = null;
let installed = false;
let capturing = false;
const subscribers = new Set<() => void>();
let onBeforeInstall: ((event: Event) => void) | null = null;
let onInstalled: ((event: Event) => void) | null = null;

function notify(): void {
  subscribers.forEach((fn) => fn());
}

export function isIosDevice(): boolean {
  if (typeof navigator === 'undefined') return false;
  const ua = navigator.userAgent;
  const iOS = /iPad|iPhone|iPod/.test(ua) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
  return iOS && !('MSStream' in window);
}

export function isStandaloneDisplay(): boolean {
  if (typeof window === 'undefined') return false;
  const nav = navigator as Navigator & { standalone?: boolean };
  return (
    window.matchMedia('(display-mode: standalone)').matches ||
    window.matchMedia('(display-mode: window-controls-overlay)').matches ||
    window.matchMedia('(display-mode: fullscreen)').matches ||
    nav.standalone === true
  );
}

export function subscribePwaInstall(listener: () => void): () => void {
  subscribers.add(listener);
  return () => {
    subscribers.delete(listener);
  };
}

export function getPwaInstallState(): {
  canPrompt: boolean;
  isInstalled: boolean;
  isIos: boolean;
  dismissed: boolean;
} {
  const isInstalled = installed || isStandaloneDisplay();
  let dismissed = false;
  try {
    dismissed = window.localStorage.getItem(DISMISS_KEY) === '1';
  } catch {
    dismissed = false;
  }
  return {
    canPrompt: Boolean(deferredPrompt) && !isInstalled,
    isInstalled,
    isIos: isIosDevice(),
    dismissed,
  };
}

export function capturePwaInstallEvents(): void {
  if (typeof window === 'undefined' || capturing) return;
  capturing = true;

  if (isStandaloneDisplay()) {
    installed = true;
  }

  onBeforeInstall = (event) => {
    event.preventDefault();
    deferredPrompt = event as BeforeInstallPromptEvent;
    notify();
  };
  onInstalled = () => {
    deferredPrompt = null;
    installed = true;
    try {
      window.localStorage.removeItem(DISMISS_KEY);
    } catch {
      /* ignore quota / private mode */
    }
    notify();
  };

  window.addEventListener('beforeinstallprompt', onBeforeInstall);
  window.addEventListener('appinstalled', onInstalled);
}

/** Clears captured prompt state. Used by unit tests. */
export function resetPwaInstallForTests(): void {
  if (typeof window !== 'undefined') {
    if (onBeforeInstall) window.removeEventListener('beforeinstallprompt', onBeforeInstall);
    if (onInstalled) window.removeEventListener('appinstalled', onInstalled);
  }
  deferredPrompt = null;
  installed = false;
  capturing = false;
  onBeforeInstall = null;
  onInstalled = null;
  subscribers.clear();
}

export async function promptPwaInstall(): Promise<PwaInstallOutcome> {
  if (!deferredPrompt) return 'unavailable';
  const promptEvent = deferredPrompt;
  deferredPrompt = null;
  await promptEvent.prompt();
  const { outcome } = await promptEvent.userChoice;
  if (outcome === 'accepted') {
    installed = true;
  }
  notify();
  return outcome;
}

export function dismissPwaInstall(): void {
  try {
    window.localStorage.setItem(DISMISS_KEY, '1');
  } catch {
    /* ignore quota / private mode */
  }
  notify();
}
