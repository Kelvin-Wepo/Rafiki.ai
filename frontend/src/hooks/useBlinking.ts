/**
 * Blinking Animation Hook
 * Natural blinking behavior for avatar eyes
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import type { EyeState, AvatarState } from '../types/avatar.types';
import { DEFAULT_ANIMATION_CONFIG } from '../types/avatar.types';

interface UseBlinkingOptions {
  minInterval?: number;
  maxInterval?: number;
  blinkDuration?: number;
  avatarState?: AvatarState;
}

export const useBlinking = (options: UseBlinkingOptions = {}) => {
  const {
    minInterval = DEFAULT_ANIMATION_CONFIG.blinkInterval.min,
    maxInterval = DEFAULT_ANIMATION_CONFIG.blinkInterval.max,
    blinkDuration = DEFAULT_ANIMATION_CONFIG.blinkDuration,
    avatarState = 'idle'
  } = options;

  const [eyeState, setEyeState] = useState<EyeState>('open');
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const blinkTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const getRandomInterval = useCallback(() => {
    return Math.random() * (maxInterval - minInterval) + minInterval;
  }, [minInterval, maxInterval]);

  const blink = useCallback(() => {
    // Close eyes
    setEyeState('closed');
    
    // Open eyes after blink duration
    blinkTimeoutRef.current = setTimeout(() => {
      setEyeState('open');
    }, blinkDuration);
  }, [blinkDuration]);

  const scheduleNextBlink = useCallback(() => {
    const interval = getRandomInterval();
    timeoutRef.current = setTimeout(() => {
      blink();
      scheduleNextBlink();
    }, interval);
  }, [blink, getRandomInterval]);

  // Adjust blinking based on avatar state
  useEffect(() => {
    // Clear existing timeouts
    if (timeoutRef.current) clearTimeout(timeoutRef.current);
    if (blinkTimeoutRef.current) clearTimeout(blinkTimeoutRef.current);

    // Don't blink during error state - keep eyes squinted
    if (avatarState === 'error') {
      setEyeState('squint');
      return;
    }

    // Thinking state - occasional half-closed eyes
    if (avatarState === 'thinking') {
      const thinkingBlink = () => {
        setEyeState('half');
        setTimeout(() => {
          setEyeState('open');
          timeoutRef.current = setTimeout(thinkingBlink, getRandomInterval() * 0.5);
        }, 300);
      };
      timeoutRef.current = setTimeout(thinkingBlink, 1000);
      return;
    }

    // Normal blinking for other states
    setEyeState('open');
    scheduleNextBlink();

    return () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
      if (blinkTimeoutRef.current) clearTimeout(blinkTimeoutRef.current);
    };
  }, [avatarState, scheduleNextBlink, getRandomInterval]);

  // Force blink function for external control
  const forceBlink = useCallback(() => {
    blink();
  }, [blink]);

  return {
    eyeState,
    forceBlink
  };
};

export default useBlinking;
