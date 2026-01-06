/**
 * Eye Tracking Hook
 * Smooth eye movement following cursor or attention points
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import type { AvatarState } from '../types/avatar.types';

interface EyePosition {
  x: number; // -1 to 1 (left to right)
  y: number; // -1 to 1 (up to down)
  pupilDilation: number; // 0.8 to 1.2 (interest/surprise)
}

interface UseEyeTrackingOptions {
  containerRef?: React.RefObject<HTMLElement>;
  followCursor?: boolean;
  smoothing?: number;
  avatarState?: AvatarState;
}

// Attention points for different states
const STATE_ATTENTION: Record<AvatarState, { lookAt: EyePosition; variance: number }> = {
  idle: { lookAt: { x: 0, y: 0, pupilDilation: 1 }, variance: 0.3 },
  listening: { lookAt: { x: 0, y: 0.1, pupilDilation: 1.05 }, variance: 0.1 },
  thinking: { lookAt: { x: 0.2, y: -0.2, pupilDilation: 0.95 }, variance: 0.4 },
  speaking: { lookAt: { x: 0, y: 0, pupilDilation: 1 }, variance: 0.15 },
  error: { lookAt: { x: 0, y: 0.2, pupilDilation: 1.1 }, variance: 0.05 }
};

export const useEyeTracking = (options: UseEyeTrackingOptions = {}) => {
  const {
    containerRef,
    followCursor = true,
    smoothing = 0.1,
    avatarState = 'idle'
  } = options;

  const [eyePosition, setEyePosition] = useState<EyePosition>({
    x: 0,
    y: 0,
    pupilDilation: 1
  });

  const targetRef = useRef<EyePosition>({ x: 0, y: 0, pupilDilation: 1 });
  const currentRef = useRef<EyePosition>({ x: 0, y: 0, pupilDilation: 1 });
  const animationRef = useRef<number>(0);
  const lastMouseMoveRef = useRef<number>(0);
  const isIdleRef = useRef<boolean>(true);

  // Smooth interpolation
  const lerp = (start: number, end: number, t: number) => start + (end - start) * t;

  // Calculate look direction from mouse position
  const calculateLookDirection = useCallback((mouseX: number, mouseY: number) => {
    if (!containerRef?.current) {
      return { x: 0, y: 0 };
    }

    const rect = containerRef.current.getBoundingClientRect();
    const centerX = rect.left + rect.width / 2;
    const centerY = rect.top + rect.height / 2;

    // Normalize to -1 to 1 range, with some dampening
    const maxDistance = Math.max(window.innerWidth, window.innerHeight) / 2;
    const x = Math.max(-1, Math.min(1, (mouseX - centerX) / maxDistance));
    const y = Math.max(-1, Math.min(1, (mouseY - centerY) / maxDistance));

    // Apply non-linear mapping for more natural eye movement
    const mapNonLinear = (value: number) => Math.sign(value) * Math.pow(Math.abs(value), 0.7);

    return {
      x: mapNonLinear(x) * 0.6, // Limit horizontal range
      y: mapNonLinear(y) * 0.4  // Limit vertical range
    };
  }, [containerRef]);

  // Handle mouse movement
  const handleMouseMove = useCallback((event: MouseEvent) => {
    if (!followCursor) return;

    lastMouseMoveRef.current = performance.now();
    isIdleRef.current = false;

    const lookDir = calculateLookDirection(event.clientX, event.clientY);
    targetRef.current = {
      ...targetRef.current,
      x: lookDir.x,
      y: lookDir.y
    };
  }, [followCursor, calculateLookDirection]);

  // Add random micro-saccades (small eye movements)
  const addMicroSaccade = useCallback(() => {
    const stateConfig = STATE_ATTENTION[avatarState];
    const variance = stateConfig.variance;

    // Random small movement
    targetRef.current = {
      x: stateConfig.lookAt.x + (Math.random() - 0.5) * variance,
      y: stateConfig.lookAt.y + (Math.random() - 0.5) * variance,
      pupilDilation: stateConfig.lookAt.pupilDilation + (Math.random() - 0.5) * 0.1
    };
  }, [avatarState]);

  // Animation loop
  const animate = useCallback(() => {
    // Check if mouse has been idle for more than 2 seconds
    if (performance.now() - lastMouseMoveRef.current > 2000 && !isIdleRef.current) {
      isIdleRef.current = true;
      // Return to state-based look direction
      const stateConfig = STATE_ATTENTION[avatarState];
      targetRef.current = stateConfig.lookAt;
    }

    // Smooth interpolation towards target
    currentRef.current = {
      x: lerp(currentRef.current.x, targetRef.current.x, smoothing),
      y: lerp(currentRef.current.y, targetRef.current.y, smoothing),
      pupilDilation: lerp(currentRef.current.pupilDilation, targetRef.current.pupilDilation, smoothing * 0.5)
    };

    setEyePosition({ ...currentRef.current });

    animationRef.current = requestAnimationFrame(animate);
  }, [avatarState, smoothing]);

  // Mouse event listener
  useEffect(() => {
    if (followCursor) {
      window.addEventListener('mousemove', handleMouseMove);
    }

    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
    };
  }, [followCursor, handleMouseMove]);

  // Animation loop
  useEffect(() => {
    animationRef.current = requestAnimationFrame(animate);

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [animate]);

  // Micro-saccades interval
  useEffect(() => {
    const saccadeInterval = setInterval(() => {
      if (isIdleRef.current && Math.random() < 0.3) {
        addMicroSaccade();
      }
    }, 500 + Math.random() * 1000);

    return () => clearInterval(saccadeInterval);
  }, [addMicroSaccade]);

  // Update target when avatar state changes
  useEffect(() => {
    const stateConfig = STATE_ATTENTION[avatarState];
    targetRef.current = {
      ...stateConfig.lookAt,
      x: stateConfig.lookAt.x + (Math.random() - 0.5) * stateConfig.variance * 0.5,
      y: stateConfig.lookAt.y + (Math.random() - 0.5) * stateConfig.variance * 0.5
    };
  }, [avatarState]);

  // Force look at specific position
  const lookAt = useCallback((x: number, y: number, dilation?: number) => {
    isIdleRef.current = false;
    lastMouseMoveRef.current = performance.now();
    targetRef.current = {
      x: Math.max(-1, Math.min(1, x)),
      y: Math.max(-1, Math.min(1, y)),
      pupilDilation: dilation ?? 1
    };
  }, []);

  // Return to idle position
  const lookNeutral = useCallback(() => {
    isIdleRef.current = true;
    const stateConfig = STATE_ATTENTION[avatarState];
    targetRef.current = stateConfig.lookAt;
  }, [avatarState]);

  return {
    eyePosition,
    lookAt,
    lookNeutral
  };
};

export default useEyeTracking;
