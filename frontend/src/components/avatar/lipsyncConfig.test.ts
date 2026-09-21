import { describe, expect, it } from 'vitest';
import {
  AVATAR_NATIVE_SIZE,
  MOUTH_CLIP_PADDING,
  coverPlacement,
  paddedClipRect,
  regionToCanvas,
  DEFAULT_MOUTH_REGION,
} from './lipsyncConfig';

describe('mouth region cover mapping', () => {
  it('places the portrait with object-fit cover (width fills, height crops)', () => {
    const { width: imgW, height: imgH } = AVATAR_NATIVE_SIZE;
    const place = coverPlacement(imgW, imgH, 400, 400);
    expect(place.dw).toBeCloseTo(400);
    expect(place.dh).toBeGreaterThan(400);
    expect(place.dx).toBeCloseTo(0);
    expect(place.dy).toBeLessThan(0);
  });

  it('maps the mouth onto the lips, not the chin', () => {
    const { width: imgW, height: imgH } = AVATAR_NATIVE_SIZE;
    const box = regionToCanvas(DEFAULT_MOUTH_REGION, imgW, imgH, 400, 400);
    const left = box.destX / 400;
    const right = (box.destX + box.destW) / 400;
    const top = box.destY / 400;
    const bottom = (box.destY + box.destH) / 400;
    const cy = (top + bottom) / 2;
    expect(left).toBeGreaterThan(0.32);
    expect(left).toBeLessThan(0.45);
    expect(right).toBeGreaterThan(0.55);
    expect(cy).toBeGreaterThan(0.4);
    expect(cy).toBeLessThan(0.52);
    expect(bottom).toBeLessThan(0.58);
  });

  it('expands clip bounds beyond the scaled mouth', () => {
    const box = {
      sx: 0,
      sy: 0,
      sw: 10,
      sh: 10,
      destX: 100,
      destY: 100,
      destW: 80,
      destH: 40,
    };
    const clip = paddedClipRect(box, 1.48, 1.18, MOUTH_CLIP_PADDING);
    expect(clip.w).toBeGreaterThan(box.destW * 1.18);
    expect(clip.h).toBeGreaterThan(box.destH * 1.48);
    expect(clip.cx).toBe(140);
    expect(clip.cy).toBe(120);
  });
});
