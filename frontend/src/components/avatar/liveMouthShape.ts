import { IDLE_SHAPE, clamp, lerp, type MouthShape } from './visemeShapes';

/**
 * Mouth shape from the agent's live output spectrum (ElevenLabs
 * `getOutputByteFrequencyData`). The bins are linear over 100–8000 Hz, so the
 * mouth follows what is actually being played, with no timeline to drift.
 *
 *   energy in the first formant (F1)   → jaw opening
 *   F2 relative to F1                  → spread (ee) vs. rounded (oo)
 *   high-band noise with weak voicing  → fricative (s, f, sh): small gap
 */
const MIN_HZ = 100;
const MAX_HZ = 8000;

const BANDS = {
  f1: [250, 900],
  f2: [900, 2800],
  hiss: [4000, 8000],
} as const;

function bandLevel(data: Uint8Array, [lo, hi]: readonly [number, number]): number {
  const hzPerBin = (MAX_HZ - MIN_HZ) / data.length;
  const from = clamp(Math.floor((lo - MIN_HZ) / hzPerBin), 0, data.length - 1);
  const to = clamp(Math.ceil((hi - MIN_HZ) / hzPerBin), from + 1, data.length);
  let sum = 0;
  for (let i = from; i < to; i += 1) sum += data[i];
  return sum / (to - from) / 255;
}

export type LiveMouthState = {
  open: number;
  width: number;
  /** Slow-moving loudness reference so quiet and loud voices both articulate. */
  peak: number;
};

export const LIVE_MOUTH_REST: LiveMouthState = { open: 1, width: 1, peak: 0.25 };

/** Below this overall level the agent is treated as silent and the mouth closes. */
const SILENCE_LEVEL = 0.06;
const ATTACK = 0.62;
const RELEASE = 0.32;

/**
 * One frame of mouth animation from the spectrum. Pure; the caller keeps
 * `state` between frames. `data` may be empty or all zeros (no audio).
 */
export function liveMouthStep(
  data: Uint8Array | null | undefined,
  state: LiveMouthState
): { shape: MouthShape; state: LiveMouthState; active: boolean } {
  if (!data || data.length === 0) {
    return { shape: IDLE_SHAPE, state: { ...state, open: 1, width: 1 }, active: false };
  }

  const f1 = bandLevel(data, BANDS.f1);
  const f2 = bandLevel(data, BANDS.f2);
  const hiss = bandLevel(data, BANDS.hiss);
  const level = Math.max(f1, f2 * 0.9);

  if (level < SILENCE_LEVEL && hiss < SILENCE_LEVEL) {
    const open = lerp(state.open, 0.9, RELEASE);
    const width = lerp(state.width, 1, RELEASE);
    return {
      shape: { open, width },
      state: { open, width, peak: Math.max(0.25, state.peak * 0.995) },
      active: false,
    };
  }

  const peak = Math.max(level, state.peak * 0.992, 0.25);
  const loudness = clamp(level / peak, 0, 1);

  // Voiced sound → jaw drops with F1 energy; fricative → just parted lips.
  const voiced = clamp((f1 + f2) / (f1 + f2 + hiss + 0.001), 0, 1);
  const targetOpen = lerp(1.04, 1.5, loudness * loudness * (0.45 + 0.55 * voiced));

  // Spread vs. rounded: F2 well above F1 → wide (ee); F1-dominant → rounded (oo/aw).
  const spread = clamp((f2 - f1) / (f2 + f1 + 0.001), -1, 1);
  const targetWidth = clamp(1.04 + spread * 0.2 - (1 - voiced) * 0.04, 0.8, 1.24);

  const openRate = targetOpen > state.open ? ATTACK : RELEASE;
  const widthRate = targetWidth > state.width ? ATTACK : RELEASE;
  const open = lerp(state.open, targetOpen, openRate);
  const width = lerp(state.width, targetWidth, widthRate);

  return { shape: { open, width }, state: { open, width, peak }, active: true };
}
