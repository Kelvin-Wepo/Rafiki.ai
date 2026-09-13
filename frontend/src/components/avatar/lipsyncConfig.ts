import type { MouthRegion } from './visemeShapes';

/**
 * Mouth box is 0–1 of the **source PNG** (rafiki_avatar.png, 501×667), then
 * mapped through object-fit: cover. Do not copy pixels from a resized preview
 * (e.g. 274×328) as if they were source coordinates — that dropped the box
 * onto the chin.
 *
 * Live box is calibrated on the native file so it covers the full lips
 * (both corners + lower lip) without the chin.
 *
 * Override with Vite env: VITE_AVATAR_MOUTH_X / _Y / _WIDTH / _HEIGHT
 */
const envNumber = (value: unknown, fallback: number): number => {
  if (value === undefined || value === '') return fallback;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
};

export const AVATAR_NATIVE_SIZE = { width: 501, height: 667 };

/** Extra clip padding so wide-open visemes are not cut off. */
export const MOUTH_CLIP_PADDING = 0.28;

export const DEFAULT_MOUTH_REGION: MouthRegion = {
  x: envNumber(import.meta.env.VITE_AVATAR_MOUTH_X, 0.388),
  y: envNumber(import.meta.env.VITE_AVATAR_MOUTH_Y, 0.43),
  width: envNumber(import.meta.env.VITE_AVATAR_MOUTH_WIDTH, 0.222),
  height: envNumber(import.meta.env.VITE_AVATAR_MOUTH_HEIGHT, 0.092),
};

export function resolveMouthRegion(override?: Partial<MouthRegion> | null): MouthRegion {
  return {
    x: override?.x ?? DEFAULT_MOUTH_REGION.x,
    y: override?.y ?? DEFAULT_MOUTH_REGION.y,
    width: override?.width ?? DEFAULT_MOUTH_REGION.width,
    height: override?.height ?? DEFAULT_MOUTH_REGION.height,
  };
}

export function isNormalizedRegion(region: MouthRegion): boolean {
  return region.width <= 1 && region.height <= 1 && region.x <= 1 && region.y <= 1;
}

/** object-fit: cover placement of the source image in the canvas. */
export function coverPlacement(
  imgW: number,
  imgH: number,
  canvasW: number,
  canvasH: number
): { dx: number; dy: number; dw: number; dh: number; scale: number } {
  const scale = Math.max(canvasW / imgW, canvasH / imgH);
  const dw = imgW * scale;
  const dh = imgH * scale;
  return {
    dx: (canvasW - dw) / 2,
    dy: (canvasH - dh) / 2,
    dw,
    dh,
    scale,
  };
}

export type CanvasMouthBox = {
  sx: number;
  sy: number;
  sw: number;
  sh: number;
  destX: number;
  destY: number;
  destW: number;
  destH: number;
};

/** Map a source-image mouth region onto the cover-fitted canvas. */
export function regionToCanvas(
  region: MouthRegion,
  imgW: number,
  imgH: number,
  canvasW: number,
  canvasH: number
): CanvasMouthBox {
  const { dx, dy, dw, dh } = coverPlacement(imgW, imgH, canvasW, canvasH);
  const sx = isNormalizedRegion(region) ? region.x * imgW : region.x;
  const sy = isNormalizedRegion(region) ? region.y * imgH : region.y;
  const sw = isNormalizedRegion(region) ? region.width * imgW : region.width;
  const sh = isNormalizedRegion(region) ? region.height * imgH : region.height;
  return {
    sx,
    sy,
    sw,
    sh,
    destX: dx + (sx / imgW) * dw,
    destY: dy + (sy / imgH) * dh,
    destW: (sw / imgW) * dw,
    destH: (sh / imgH) * dh,
  };
}

/** Clip rect around the mouth, padded and grown by the current viseme scale. */
export function paddedClipRect(
  box: CanvasMouthBox,
  open: number,
  width: number,
  padding: number = MOUTH_CLIP_PADDING
): { x: number; y: number; w: number; h: number; cx: number; cy: number } {
  const cx = box.destX + box.destW / 2;
  const cy = box.destY + box.destH / 2;
  const scaleW = Math.max(1, width);
  const scaleH = Math.max(1, open);
  const w = box.destW * scaleW * (1 + padding * 2);
  const h = box.destH * scaleH * (1 + padding * 2);
  return { x: cx - w / 2, y: cy - h / 2, w, h, cx, cy };
}
