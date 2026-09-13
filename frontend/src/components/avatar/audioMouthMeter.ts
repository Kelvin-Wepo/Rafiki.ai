import { clamp, lerp } from './visemeShapes';

export type MouthMeter = {
  ctx: AudioContext;
  analyser: AnalyserNode;
  data: Uint8Array;
  smooth: number;
};

/** Route the playing element through an analyser so openness follows the waveform. */
export function attachMouthMeter(audio: HTMLAudioElement): MouthMeter | null {
  const AudioCtx = window.AudioContext || (window as typeof window & { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
  if (!AudioCtx) return null;
  try {
    const ctx = new AudioCtx();
    const source = ctx.createMediaElementSource(audio);
    const analyser = ctx.createAnalyser();
    analyser.fftSize = 1024;
    analyser.smoothingTimeConstant = 0.38;
    source.connect(analyser);
    analyser.connect(ctx.destination);
    return {
      ctx,
      analyser,
      data: new Uint8Array(analyser.fftSize),
      smooth: 0,
    };
  } catch {
    return null;
  }
}

export async function resumeMouthMeter(meter: MouthMeter | null): Promise<void> {
  if (!meter) return;
  if (meter.ctx.state === 'suspended') {
    try {
      await meter.ctx.resume();
    } catch {
      /* autoplay policies */
    }
  }
}

export function closeMouthMeter(meter: MouthMeter | null): void {
  if (!meter) return;
  try {
    void meter.ctx.close();
  } catch {
    /* already closed */
  }
}

/** Smoothed RMS 0–1 of the audio currently coming out of the speaker. */
export function readMouthEnergy(meter: MouthMeter): number {
  meter.analyser.getByteTimeDomainData(meter.data as Uint8Array<ArrayBuffer>);
  let sum = 0;
  const { data } = meter;
  for (let i = 0; i < data.length; i += 1) {
    const n = (data[i] - 128) / 128;
    sum += n * n;
  }
  const rms = Math.sqrt(sum / data.length);
  meter.smooth += (rms - meter.smooth) * 0.5;
  return meter.smooth;
}

/** Map RMS onto the same open scale as visemes (1 = painted smile). */
export function energyToOpen(energy: number): number {
  const u = clamp((energy - 0.012) / 0.11, 0, 1);
  return lerp(0.88, 1.38, u * u);
}
