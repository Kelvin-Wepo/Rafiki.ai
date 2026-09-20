import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import {
  capturePwaInstallEvents,
  dismissPwaInstall,
  getPwaInstallState,
  isIosDevice,
  isStandaloneDisplay,
  promptPwaInstall,
  resetPwaInstallForTests,
} from './pwaInstall';

function stubMatchMedia(matches: boolean) {
  window.matchMedia = vi.fn().mockImplementation((query: string) => ({
    matches,
    media: query,
    onchange: null,
    addListener: () => undefined,
    removeListener: () => undefined,
    addEventListener: () => undefined,
    removeEventListener: () => undefined,
    dispatchEvent: () => false,
  }));
}

class FakeInstallEvent extends Event {
  prompt = vi.fn(async () => undefined);
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed'; platform: string }>;

  constructor(outcome: 'accepted' | 'dismissed' = 'accepted') {
    super('beforeinstallprompt', { cancelable: true });
    this.userChoice = Promise.resolve({ outcome, platform: 'web' });
  }
}

describe('pwaInstall', () => {
  const originalUserAgent = navigator.userAgent;

  beforeEach(() => {
    resetPwaInstallForTests();
    stubMatchMedia(false);
    window.localStorage.clear();
    Object.defineProperty(window.navigator, 'userAgent', {
      configurable: true,
      value: 'Mozilla/5.0 (X11; Linux x86_64) Chrome/120.0.0.0',
    });
  });

  afterEach(() => {
    resetPwaInstallForTests();
    Object.defineProperty(window.navigator, 'userAgent', {
      configurable: true,
      value: originalUserAgent,
    });
  });

  it('detects standalone display mode', () => {
    stubMatchMedia(true);
    expect(isStandaloneDisplay()).toBe(true);
  });

  it('detects iOS devices from the user agent', () => {
    Object.defineProperty(window.navigator, 'userAgent', {
      configurable: true,
      value: 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)',
    });
    expect(isIosDevice()).toBe(true);
  });

  it('captures beforeinstallprompt so install can be triggered later', async () => {
    capturePwaInstallEvents();
    const event = new FakeInstallEvent('accepted');
    window.dispatchEvent(event);

    expect(getPwaInstallState().canPrompt).toBe(true);

    const outcome = await promptPwaInstall();
    expect(event.prompt).toHaveBeenCalledTimes(1);
    expect(outcome).toBe('accepted');
    expect(getPwaInstallState().canPrompt).toBe(false);
    expect(getPwaInstallState().isInstalled).toBe(true);
  });

  it('returns unavailable when no prompt was captured', async () => {
    capturePwaInstallEvents();
    await expect(promptPwaInstall()).resolves.toBe('unavailable');
  });

  it('remembers when the banner is dismissed', () => {
    dismissPwaInstall();
    expect(getPwaInstallState().dismissed).toBe(true);
  });
});
