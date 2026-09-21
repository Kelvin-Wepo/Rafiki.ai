import { describe, expect, it } from 'vitest';
import {
  IDLE_SHAPE,
  lerpShape,
  shapeAtTime,
  shapeForViseme,
  type VisemeCue,
} from './visemeShapes';

describe('viseme shape lookup', () => {
  it('maps rest to a closed mouth', () => {
    expect(shapeForViseme('X').open).toBeLessThan(shapeForViseme('D').open);
    expect(shapeForViseme('A').open).toBeLessThan(shapeForViseme('C').open);
    expect(shapeForViseme('F').width).toBeLessThan(shapeForViseme('C').width);
  });

  it('lerps between shapes without jumping', () => {
    const a = shapeForViseme('X');
    const b = shapeForViseme('D');
    const mid = lerpShape(a, b, 0.5);
    expect(mid.open).toBeGreaterThan(a.open);
    expect(mid.open).toBeLessThan(b.open);
  });

  it('holds the current viseme and only crossfades near the next cue', () => {
    const timeline: VisemeCue[] = [
      { time: 0, viseme: 'X', duration: 0.2 },
      { time: 0.2, viseme: 'D', duration: 0.2 },
    ];
    const atStart = shapeAtTime(timeline, 0);
    const held = shapeAtTime(timeline, 0.08);
    const atOpen = shapeAtTime(timeline, 0.2);
    expect(atStart.open).toBeCloseTo(IDLE_SHAPE.open, 2);
    expect(held.open).toBeCloseTo(IDLE_SHAPE.open, 2);
    expect(atOpen.open).toBeGreaterThan(held.open);
    expect(shapeAtTime([], 0.1)).toEqual(IDLE_SHAPE);
  });
});
