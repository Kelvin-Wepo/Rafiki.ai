/**
 * Viseme → mouth deformation lookup.
 *
 * `open` is vertical scale around the mouth-region center.
 * The source art already has a slightly open smile, so:
 *   1    matches the painted mouth (idle / rest)
 *   < 1  compresses toward closed
 *   > 1  stretches into a wider open
 *
 * `width` is horizontal scale (1 = natural, < 1 pursed/rounded).
 */
export type VisemeId = 'A' | 'B' | 'C' | 'D' | 'E' | 'F' | 'G' | 'H' | 'X';

export type MouthShape = {
  open: number;
  width: number;
};

export type VisemeCue = {
  time: number;
  viseme: string;
  duration: number;
};

export type MouthRegion = {
  x: number;
  y: number;
  width: number;
  height: number;
};

export const IDLE_SHAPE: MouthShape = { open: 1, width: 1 };

/** Rhubarb A–H, X → parametric mouth. */
export const VISEME_SHAPES: Record<VisemeId, MouthShape> = {
  X: { open: 1, width: 1 }, // rest — match the painted smile
  A: { open: 0.78, width: 0.96 }, // p, b, m — lips together
  B: { open: 1.06, width: 1.04 }, // slight open (s, t, d, k)
  C: { open: 1.34, width: 1.22 }, // wide (e, i) — reach lip corners
  D: { open: 1.48, width: 1.18 }, // wide open (a) — chin-down extent
  E: { open: 1.14, width: 0.92 }, // rounded (o)
  F: { open: 1.08, width: 0.8 }, // pursed (u, w)
  G: { open: 0.92, width: 1.02 }, // f, v — teeth on lip
  H: { open: 1.12, width: 1 }, // l — tongue
};

export function isVisemeId(value: string): value is VisemeId {
  return value in VISEME_SHAPES;
}

export function shapeForViseme(viseme: string): MouthShape {
  return isVisemeId(viseme) ? VISEME_SHAPES[viseme] : IDLE_SHAPE;
}

export function lerp(a: number, b: number, t: number): number {
  return a + (b - a) * t;
}

export function clamp(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value));
}

export function lerpShape(from: MouthShape, to: MouthShape, t: number): MouthShape {
  const u = clamp(t, 0, 1);
  return {
    open: lerp(from.open, to.open, u),
    width: lerp(from.width, to.width, u),
  };
}

function smoothstep(t: number): number {
  const u = clamp(t, 0, 1);
  return u * u * (3 - 2 * u);
}

export function isIdleShape(shape: MouthShape): boolean {
  return Math.abs(shape.open - 1) < 0.02 && Math.abs(shape.width - 1) < 0.02;
}

export const VISEME_CROSSFADE_S = 0.055;
/** Sample visemes slightly ahead of audio.currentTime (mouth leads sound). */
export const VISEME_LOOKAHEAD_S = 0.035;

/**
 * Sample the mouth shape at audio time `t` (seconds).
 * Holds the current viseme and only crossfades in the last ~55ms of the cue
 * so the mouth is not always halfway to the next sound.
 */
export function shapeAtTime(timeline: VisemeCue[] | undefined, t: number): MouthShape {
  if (!timeline || timeline.length === 0) {
    return IDLE_SHAPE;
  }

  const sample = t + VISEME_LOOKAHEAD_S;
  let index = 0;
  while (index + 1 < timeline.length && timeline[index + 1].time <= sample) {
    index += 1;
  }

  const current = timeline[index];
  const currentShape = shapeForViseme(current.viseme);
  const next = timeline[index + 1];
  if (!next) {
    const localEnd = current.time + current.duration;
    if (sample >= localEnd) return IDLE_SHAPE;
    return currentShape;
  }

  const remaining = next.time - sample;
  if (remaining >= VISEME_CROSSFADE_S) {
    return currentShape;
  }
  const u = smoothstep(1 - remaining / VISEME_CROSSFADE_S);
  return lerpShape(currentShape, shapeForViseme(next.viseme), u);
}

/** Blend viseme width with openness from the live audio waveform. */
export function mixPlaybackShape(viseme: MouthShape, energyOpen: number): MouthShape {
  return {
    open: lerp(energyOpen, viseme.open, 0.32),
    width: viseme.width,
  };
}

export function pulseShape(elapsedMs: number): MouthShape {
  const wave = 0.5 + 0.5 * Math.sin(elapsedMs * 0.012);
  return {
    open: lerp(0.88, 1.2, wave),
    width: lerp(0.98, 1.06, wave),
  };
}
