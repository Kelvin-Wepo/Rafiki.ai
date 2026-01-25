/**
 * Hook for managing idle animations between avatar interactions
 */
import { useState, useEffect, useRef } from 'react';

export interface IdleAnimationConfig {
  enabled?: boolean;
  idleTimeout?: number; // ms before starting idle animation
  blinkInterval?: number; // ms between blinks
  subtleMovements?: boolean;
}

export const useIdleAnimation = (config: IdleAnimationConfig = {}) => {
  const {
    enabled = true,
    idleTimeout = 3000,
    blinkInterval = 4000,
    subtleMovements = true
  } = config;

  const [isIdle, setIsIdle] = useState(false);
  const [shouldBlink, setShouldBlink] = useState(false);
  const [headTilt, setHeadTilt] = useState({ x: 0, y: 0 });
  
  const idleTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const blinkTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const movementTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const lastActivityRef = useRef<number>(Date.now());

  // Reset activity timestamp
  const resetActivity = () => {
    lastActivityRef.current = Date.now();
    setIsIdle(false);
  };

  // Start idle state after timeout
  useEffect(() => {
    if (!enabled) return;

    idleTimerRef.current = setInterval(() => {
      const timeSinceActivity = Date.now() - lastActivityRef.current;
      if (timeSinceActivity >= idleTimeout) {
        setIsIdle(true);
      }
    }, 1000);

    return () => {
      if (idleTimerRef.current) clearInterval(idleTimerRef.current);
    };
  }, [enabled, idleTimeout]);

  // Periodic blinking when idle
  useEffect(() => {
    if (!enabled || !isIdle) return;

    const startBlinking = () => {
      setShouldBlink(true);
      setTimeout(() => setShouldBlink(false), 150); // Blink duration
    };

    startBlinking(); // Initial blink
    blinkTimerRef.current = setInterval(startBlinking, blinkInterval);

    return () => {
      if (blinkTimerRef.current) clearInterval(blinkTimerRef.current);
    };
  }, [enabled, isIdle, blinkInterval]);

  // Subtle head movements when idle
  useEffect(() => {
    if (!enabled || !isIdle || !subtleMovements) return;

    const moveHead = () => {
      const x = (Math.random() - 0.5) * 3; // -1.5 to 1.5 degrees
      const y = (Math.random() - 0.5) * 2; // -1 to 1 degrees
      setHeadTilt({ x, y });
    };

    moveHead(); // Initial movement
    movementTimerRef.current = setInterval(moveHead, 5000);

    return () => {
      if (movementTimerRef.current) clearInterval(movementTimerRef.current);
    };
  }, [enabled, isIdle, subtleMovements]);

  return {
    isIdle,
    shouldBlink,
    headTilt,
    resetActivity
  };
};
