/**
 * Canvas talking avatar. Mouth box is 0–1 of the source PNG, mapped through
 * object-fit: cover. Openness follows the playing audio; visemes set width.
 */
import { useCallback, useEffect, useRef, useState } from 'react';
import {
  IDLE_SHAPE,
  clamp,
  isIdleShape,
  mixPlaybackShape,
  pulseShape,
  shapeAtTime,
  type MouthRegion,
  type MouthShape,
  type VisemeCue,
} from './visemeShapes';
import { coverPlacement, paddedClipRect, regionToCanvas, resolveMouthRegion } from './lipsyncConfig';
import {
  attachMouthMeter,
  closeMouthMeter,
  energyToOpen,
  readMouthEnergy,
  resumeMouthMeter,
  type MouthMeter,
} from './audioMouthMeter';
import './TalkingAvatar.css';

export type TalkingAvatarProps = {
  imageUrl: string;
  audioUrl?: string | null;
  visemeTimeline?: VisemeCue[];
  mouthRegion?: Partial<MouthRegion> | null;
  /** Pulse fallback when speaking without a timeline (live WebRTC voice). */
  isSpeaking?: boolean;
  autoPlay?: boolean;
  className?: string;
  alt?: string;
  /** Bump to replay the same audioUrl. */
  playId?: number;
  /**
   * Draw a red rectangle on the mapped mouthRegion (source-image fractions
   * after object-fit: cover). Default off. `debug` is an alias.
   */
  debug?: boolean;
  debugMouthBox?: boolean;
  onPlay?: () => void;
  onEnded?: () => void;
  onError?: () => void;
};

const imageCache = new Map<string, HTMLImageElement>();
const imagePending = new Map<string, Promise<HTMLImageElement>>();

function loadImage(url: string): Promise<HTMLImageElement> {
  const cached = imageCache.get(url);
  if (cached) return Promise.resolve(cached);
  const pending = imagePending.get(url);
  if (pending) return pending;

  const promise = new Promise<HTMLImageElement>((resolve, reject) => {
    const img = new Image();
    img.crossOrigin = 'anonymous';
    img.onload = () => {
      imageCache.set(url, img);
      imagePending.delete(url);
      resolve(img);
    };
    img.onerror = () => {
      imagePending.delete(url);
      reject(new Error(`Failed to load avatar image: ${url}`));
    };
    img.src = url;
  });
  imagePending.set(url, promise);
  return promise;
}

function sampleSkin(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  canvasW: number,
  canvasH: number
): string {
  const sx = Math.round(clamp(x, 0, canvasW - 1));
  const sy = Math.round(clamp(y, 0, canvasH - 1));
  try {
    const pixel = ctx.getImageData(sx, sy, 1, 1).data;
    return `rgb(${pixel[0]}, ${pixel[1]}, ${pixel[2]})`;
  } catch {
    return 'rgb(168, 92, 54)';
  }
}

function drawFrame(
  ctx: CanvasRenderingContext2D,
  img: HTMLImageElement,
  canvasW: number,
  canvasH: number,
  region: MouthRegion,
  shape: MouthShape,
  debugMouthBox: boolean
) {
  ctx.imageSmoothingEnabled = true;
  ctx.imageSmoothingQuality = 'high';
  ctx.clearRect(0, 0, canvasW, canvasH);

  const place = coverPlacement(img.naturalWidth, img.naturalHeight, canvasW, canvasH);
  ctx.drawImage(img, place.dx, place.dy, place.dw, place.dh);

  const box = regionToCanvas(region, img.naturalWidth, img.naturalHeight, canvasW, canvasH);
  if (box.sw <= 0 || box.sh <= 0) return;

  const cx = box.destX + box.destW / 2;
  const cy = box.destY + box.destH / 2;
  const deform = !isIdleShape(shape);

  if (deform) {
    const jaw = Math.max(0, shape.open - 1) * box.destH * 0.2;
    const clip = paddedClipRect(box, shape.open, shape.width);

    ctx.save();
    ctx.beginPath();
    ctx.rect(clip.x, clip.y + jaw * 0.4, clip.w, clip.h);
    ctx.clip();

    if (shape.open < 0.98) {
      const skin = sampleSkin(ctx, cx, box.destY + box.destH * 1.15, canvasW, canvasH);
      ctx.fillStyle = skin;
      ctx.beginPath();
      ctx.ellipse(cx, cy, box.destW / 2, box.destH / 2, 0, 0, Math.PI * 2);
      ctx.fill();
    }

    // Scale around the mouth-region center, not the canvas origin.
    ctx.translate(cx, cy + jaw);
    ctx.scale(shape.width, shape.open);
    ctx.translate(-cx, -cy);
    ctx.drawImage(img, box.sx, box.sy, box.sw, box.sh, box.destX, box.destY, box.destW, box.destH);

    if (shape.open > 1.08) {
      const cavity = clamp((shape.open - 1) / 0.5, 0, 1);
      ctx.fillStyle = `rgba(42, 14, 14, ${0.14 + cavity * 0.28})`;
      ctx.beginPath();
      ctx.ellipse(
        cx,
        cy + box.destH * 0.08,
        box.destW * 0.32,
        box.destH * 0.2 * cavity,
        0,
        0,
        Math.PI * 2
      );
      ctx.fill();
    }
    ctx.restore();
  }

  if (debugMouthBox) {
    ctx.save();
    ctx.strokeStyle = 'rgba(220, 38, 38, 0.95)';
    ctx.lineWidth = Math.max(2, canvasW * 0.007);
    ctx.strokeRect(box.destX, box.destY, box.destW, box.destH);
    ctx.restore();
  }
}

export default function TalkingAvatar({
  imageUrl,
  audioUrl,
  visemeTimeline,
  mouthRegion,
  isSpeaking = false,
  autoPlay = true,
  className,
  alt = 'Rafiki',
  playId = 0,
  debug = false,
  debugMouthBox = false,
  onPlay,
  onEnded,
  onError,
}: TalkingAvatarProps) {
  const showDebug = debug || debugMouthBox;
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const wrapRef = useRef<HTMLDivElement>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const rafRef = useRef<number>(0);
  const imgRef = useRef<HTMLImageElement | null>(null);
  const regionRef = useRef(resolveMouthRegion(mouthRegion));
  const timelineRef = useRef(visemeTimeline);
  const speakingRef = useRef(isSpeaking);
  const debugRef = useRef(showDebug);
  const pulseStartRef = useRef(0);
  const meterRef = useRef<MouthMeter | null>(null);
  const [ready, setReady] = useState(false);

  const onPlayRef = useRef(onPlay);
  const onEndedRef = useRef(onEnded);
  const onErrorRef = useRef(onError);
  onPlayRef.current = onPlay;
  onEndedRef.current = onEnded;
  onErrorRef.current = onError;
  regionRef.current = resolveMouthRegion(mouthRegion);
  timelineRef.current = visemeTimeline;
  speakingRef.current = isSpeaking;
  debugRef.current = showDebug;

  const stopLoop = useCallback(() => {
    if (rafRef.current) {
      cancelAnimationFrame(rafRef.current);
      rafRef.current = 0;
    }
  }, []);

  const paint = useCallback((shape: MouthShape) => {
    const canvas = canvasRef.current;
    const img = imgRef.current;
    if (!canvas || !img) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    drawFrame(ctx, img, canvas.width, canvas.height, regionRef.current, shape, debugRef.current);
  }, []);

  const paintIdle = useCallback(() => {
    paint(IDLE_SHAPE);
  }, [paint]);

  const sizeCanvas = useCallback(() => {
    const canvas = canvasRef.current;
    const wrap = wrapRef.current;
    const img = imgRef.current;
    if (!canvas || !wrap || !img) return;
    const rect = wrap.getBoundingClientRect();
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const cssW = Math.max(1, Math.round(rect.width || wrap.clientWidth || 148));
    const cssH = Math.max(1, Math.round(rect.height || wrap.clientHeight || cssW));
    canvas.style.width = `${cssW}px`;
    canvas.style.height = `${cssH}px`;
    canvas.width = Math.round(cssW * dpr);
    canvas.height = Math.round(cssH * dpr);
    paintIdle();
  }, [paintIdle]);

  useEffect(() => {
    let cancelled = false;
    loadImage(imageUrl)
      .then((img) => {
        if (cancelled) return;
        imgRef.current = img;
        setReady(true);
      })
      .catch(() => {
        if (!cancelled) setReady(false);
      });
    return () => {
      cancelled = true;
    };
  }, [imageUrl]);

  useEffect(() => {
    if (!ready) return;
    sizeCanvas();
    const wrap = wrapRef.current;
    if (!wrap || typeof ResizeObserver === 'undefined') return;
    const observer = new ResizeObserver(() => sizeCanvas());
    observer.observe(wrap);
    return () => observer.disconnect();
  }, [ready, sizeCanvas]);

  useEffect(() => {
    paintIdle();
  }, [mouthRegion, showDebug, paintIdle]);

  useEffect(() => {
    if (!showDebug || !ready) return;
    const img = imgRef.current;
    const canvas = canvasRef.current;
    if (!img || !canvas) return;
    const region = resolveMouthRegion(mouthRegion);
    const mapped = regionToCanvas(
      region,
      img.naturalWidth,
      img.naturalHeight,
      canvas.width,
      canvas.height
    );
    console.info('[TalkingAvatar] mouthRegion', {
      configured: region,
      measuredOn: 'native PNG 501×667 (cover-mapped)',
      sourceImage: { width: img.naturalWidth, height: img.naturalHeight },
      canvas: { width: canvas.width, height: canvas.height },
      mappedPx: mapped,
      origin: {
        x: mapped.destX + mapped.destW / 2,
        y: mapped.destY + mapped.destH / 2,
      },
    });
  }, [showDebug, ready, mouthRegion]);

  useEffect(() => {
    stopLoop();
    const canvas = canvasRef.current;
    const img = imgRef.current;
    if (!canvas || !img || !ready) return;

    const hasAudio = Boolean(audioUrl);
    const shouldPulse = !hasAudio && isSpeaking;
    if (!hasAudio && !shouldPulse) {
      paintIdle();
      return;
    }

    const tick = (now: number) => {
      const audio = audioRef.current;
      let shape = IDLE_SHAPE;
      if (audio && !audio.paused && !audio.ended) {
        const timeline = timelineRef.current;
        const viseme =
          timeline && timeline.length > 0 ? shapeAtTime(timeline, audio.currentTime) : null;
        const meter = meterRef.current;
        const energyOpen = meter ? energyToOpen(readMouthEnergy(meter)) : null;
        if (viseme && energyOpen != null) {
          shape = mixPlaybackShape(viseme, energyOpen);
        } else if (viseme) {
          shape = viseme;
        } else if (energyOpen != null) {
          shape = { open: energyOpen, width: 1.02 };
        } else {
          shape = pulseShape(now);
        }
      } else if (speakingRef.current && !audioUrl) {
        if (!pulseStartRef.current) pulseStartRef.current = now;
        shape = pulseShape(now - pulseStartRef.current);
      } else if (audioUrl && audio && !audio.ended) {
        shape = IDLE_SHAPE;
      } else {
        pulseStartRef.current = 0;
        paintIdle();
        stopLoop();
        return;
      }
      paint(shape);
      rafRef.current = requestAnimationFrame(tick);
    };

    rafRef.current = requestAnimationFrame(tick);
    return () => stopLoop();
  }, [audioUrl, playId, isSpeaking, ready, paintIdle, paint, stopLoop]);

  useEffect(() => {
    const previous = audioRef.current;
    if (previous) {
      previous.pause();
      previous.removeAttribute('src');
      previous.load();
      audioRef.current = null;
    }

    if (!audioUrl) return;

    const audio = new Audio(audioUrl);
    audio.preload = 'auto';
    audio.crossOrigin = 'anonymous';
    audioRef.current = audio;
    const meter = attachMouthMeter(audio);
    meterRef.current = meter;
    audio.onplay = () => {
      void resumeMouthMeter(meter);
      onPlayRef.current?.();
    };
    audio.onended = () => {
      stopLoop();
      paintIdle();
      onEndedRef.current?.();
    };
    audio.onerror = () => {
      stopLoop();
      paintIdle();
      onErrorRef.current?.();
    };
    audio.onpause = () => {
      if (audio.ended) return;
      stopLoop();
      paintIdle();
    };

    if (autoPlay) {
      audio.play().catch(() => onErrorRef.current?.());
    }

    return () => {
      audio.pause();
      audio.onplay = null;
      audio.onended = null;
      audio.onerror = null;
      audio.onpause = null;
      closeMouthMeter(meter);
      if (meterRef.current === meter) meterRef.current = null;
    };
  }, [audioUrl, playId, autoPlay, stopLoop, paintIdle]);

  useEffect(() => () => stopLoop(), [stopLoop]);

  return (
    <div ref={wrapRef} className={`talking-avatar${className ? ` ${className}` : ''}`}>
      <canvas ref={canvasRef} role="img" aria-label={alt} />
      {!ready && <img src={imageUrl} alt={alt} className="talking-avatar__fallback" />}
    </div>
  );
}
