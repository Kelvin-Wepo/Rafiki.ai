import { describe, expect, it } from 'vitest';
import { LIVE_MOUTH_REST, liveMouthStep, type LiveMouthState } from './liveMouthShape';

const BINS = 1024;
const hzToBin = (hz: number) => Math.round(((hz - 100) / 7900) * BINS);

function spectrum(peaks: Array<[number, number]>): Uint8Array {
  const data = new Uint8Array(BINS);
  for (const [hz, level] of peaks) {
    const centre = hzToBin(hz);
    for (let i = -30; i <= 30; i += 1) {
      const bin = centre + i;
      if (bin >= 0 && bin < BINS) data[bin] = Math.max(data[bin], Math.round(level * (1 - Math.abs(i) / 31)));
    }
  }
  return data;
}

function settle(data: Uint8Array | null, frames = 40): LiveMouthState & { active: boolean } {
  let state = LIVE_MOUTH_REST;
  let active = false;
  for (let i = 0; i < frames; i += 1) {
    const step = liveMouthStep(data, state);
    state = step.state;
    active = step.active;
  }
  return { ...state, active };
}

describe('liveMouthStep', () => {
  it('stays at rest for missing or silent audio', () => {
    expect(liveMouthStep(null, LIVE_MOUTH_REST).active).toBe(false);
    const silent = settle(new Uint8Array(BINS));
    expect(silent.active).toBe(false);
    expect(silent.open).toBeLessThan(1);
  });

  it('opens the jaw wider for loud first-formant energy than for quiet', () => {
    const loud = settle(spectrum([[700, 255]]));
    const quiet = settle(spectrum([[700, 70]]));
    expect(loud.active).toBe(true);
    expect(loud.open).toBeGreaterThan(quiet.open);
    expect(loud.open).toBeGreaterThan(1.25);
  });

  it('spreads the lips for high F2 (ee) and rounds them for low F2 (oo)', () => {
    const ee = settle(spectrum([[300, 120], [2400, 230]]));
    const oo = settle(spectrum([[350, 230], [800, 60]]));
    expect(ee.width).toBeGreaterThan(oo.width);
  });

  it('treats hiss with no voicing as a small gap, not a wide-open vowel', () => {
    const hiss = settle(spectrum([[6000, 200]]));
    const vowel = settle(spectrum([[700, 220], [1400, 160]]));
    expect(hiss.open).toBeLessThan(vowel.open);
  });

  it('closes again when the audio stops', () => {
    let state = settle(spectrum([[700, 255]]));
    for (let i = 0; i < 30; i += 1) state = { ...state, ...liveMouthStep(new Uint8Array(BINS), state).state };
    expect(state.open).toBeLessThan(1);
  });
});
