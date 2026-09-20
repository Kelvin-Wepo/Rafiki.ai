import { renderHook, act, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { usePwaInstall } from './usePwaInstall';
import {
  capturePwaInstallEvents,
  resetPwaInstallForTests,
} from '../lib/pwaInstall';

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
  userChoice = Promise.resolve({ outcome: 'accepted' as const, platform: 'web' });

  constructor() {
    super('beforeinstallprompt', { cancelable: true });
  }
}

describe('usePwaInstall', () => {
  beforeEach(() => {
    resetPwaInstallForTests();
    stubMatchMedia(false);
    window.localStorage.clear();
  });

  afterEach(() => {
    resetPwaInstallForTests();
  });

  it('exposes a one-tap install action after the browser prompt is captured', async () => {
    capturePwaInstallEvents();
    const { result } = renderHook(() => usePwaInstall());

    expect(result.current.canPrompt).toBe(false);

    act(() => {
      window.dispatchEvent(new FakeInstallEvent());
    });

    await waitFor(() => {
      expect(result.current.canPrompt).toBe(true);
      expect(result.current.canShowBanner).toBe(true);
    });

    await act(async () => {
      await result.current.install();
    });

    expect(result.current.isInstalled).toBe(true);
    expect(result.current.canShowButton).toBe(false);
  });

  it('hides the banner after dismiss but keeps install available', async () => {
    capturePwaInstallEvents();
    const { result } = renderHook(() => usePwaInstall());

    act(() => {
      window.dispatchEvent(new FakeInstallEvent());
    });

    await waitFor(() => expect(result.current.canShowBanner).toBe(true));

    act(() => {
      result.current.dismiss();
    });

    expect(result.current.canShowBanner).toBe(false);
    expect(result.current.canShowButton).toBe(true);
  });
});
