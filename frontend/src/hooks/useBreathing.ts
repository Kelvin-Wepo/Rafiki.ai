/**
 * Breathing Animation Hook
 * Subtle breathing motion for lifelike appearance
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import type { AvatarState } from '../types/avatar.types';

interface BreathingState {
  chestRise: number;      // 0 to 1 - chest expansion
  shoulderLift: number;   // -0.5 to 0.5 - shoulder movement
  headBob: number;        // subtle head movement from breathing
  phase: 'inhale' | 'hold' | 'exhale' | 'pause';
}

interface UseBreathingOptions {
  breathsPerMinute?: number;
  intensity?: number;
  avatarState?: AvatarState;
}

// Breathing patterns for different states
const BREATHING_PATTERNS: Record<AvatarState, { rate: number; depth: number }> = {
  idle: { rate: 12, depth: 1.0 },      // Normal relaxed breathing
  listening: { rate: 14, depth: 0.8 }, // Slightly faster, shallower
  thinking: { rate: 16, depth: 0.6 },  // Faster, focused
  speaking: { rate: 18, depth: 0.5 },  // Quick, speech breathing
  error: { rate: 20, depth: 0.4 }      // Stressed breathing
};

export const useBreathing = (options: UseBreathingOptions = {}) => {
  const {
    breathsPerMinute: customRate,
    intensity = 1.0,
    avatarState = 'idle'
  } = options;

  const [breathing, setBreathing] = useState<BreathingState>({
    chestRise: 0,
    shoulderLift: 0,
    headBob: 0,
    phase: 'pause'
  });

  const animationRef = useRef<number>(0);
  const startTimeRef = useRef<number>(0);
  const phaseStartRef = useRef<number>(0);

  // Get breathing parameters for current state
  const getBreathingParams = useCallback(() => {
    const pattern = BREATHING_PATTERNS[avatarState];
    const rate = customRate ?? pattern.rate;
    const depth = pattern.depth * intensity;
    
    // Calculate phase durations (in ms)
    const cycleDuration = (60 / rate) * 1000;
    const inhaleDuration = cycleDuration * 0.35;
    const holdDuration = cycleDuration * 0.1;
    const exhaleDuration = cycleDuration * 0.45;
    const pauseDuration = cycleDuration * 0.1;

    return {
      rate,
      depth,
      cycleDuration,
      inhaleDuration,
      holdDuration,
      exhaleDuration,
      pauseDuration
    };
  }, [avatarState, customRate, intensity]);

  // Easing functions
  const easeInOutSine = (t: number): number => {
    return -(Math.cos(Math.PI * t) - 1) / 2;
  };

  const easeOutQuad = (t: number): number => {
    return 1 - (1 - t) * (1 - t);
  };

  // Animate breathing
  const animate = useCallback((timestamp: number) => {
    if (!startTimeRef.current) {
      startTimeRef.current = timestamp;
      phaseStartRef.current = timestamp;
    }

    const params = getBreathingParams();
    const phaseTime = timestamp - phaseStartRef.current;

    setBreathing(prev => {
      let newPhase = prev.phase;
      let progress = 0;
      let chestRise = 0;
      let shoulderLift = 0;
      let headBob = 0;

      switch (prev.phase) {
        case 'inhale':
          progress = Math.min(1, phaseTime / params.inhaleDuration);
          chestRise = easeInOutSine(progress) * params.depth;
          shoulderLift = easeInOutSine(progress) * 0.3 * params.depth;
          headBob = easeInOutSine(progress) * 0.1 * params.depth;
          
          if (phaseTime >= params.inhaleDuration) {
            newPhase = 'hold';
            phaseStartRef.current = timestamp;
          }
          break;

        case 'hold':
          chestRise = params.depth;
          shoulderLift = 0.3 * params.depth;
          headBob = 0.1 * params.depth;
          
          if (phaseTime >= params.holdDuration) {
            newPhase = 'exhale';
            phaseStartRef.current = timestamp;
          }
          break;

        case 'exhale':
          progress = Math.min(1, phaseTime / params.exhaleDuration);
          chestRise = (1 - easeOutQuad(progress)) * params.depth;
          shoulderLift = (1 - easeOutQuad(progress)) * 0.3 * params.depth;
          headBob = (1 - easeOutQuad(progress)) * 0.1 * params.depth;
          
          if (phaseTime >= params.exhaleDuration) {
            newPhase = 'pause';
            phaseStartRef.current = timestamp;
          }
          break;

        case 'pause':
          chestRise = 0;
          shoulderLift = 0;
          headBob = 0;
          
          if (phaseTime >= params.pauseDuration) {
            newPhase = 'inhale';
            phaseStartRef.current = timestamp;
          }
          break;
      }

      return {
        chestRise,
        shoulderLift,
        headBob,
        phase: newPhase
      };
    });

    animationRef.current = requestAnimationFrame(animate);
  }, [getBreathingParams]);

  // Start/stop animation based on state
  useEffect(() => {
    animationRef.current = requestAnimationFrame(animate);

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [animate, avatarState]);

  // Hold breath for speaking
  const holdBreath = useCallback(() => {
    setBreathing(prev => ({
      ...prev,
      phase: 'hold'
    }));
    phaseStartRef.current = performance.now();
  }, []);

  // Resume normal breathing
  const resumeBreathing = useCallback(() => {
    setBreathing(prev => ({
      ...prev,
      phase: 'exhale'
    }));
    phaseStartRef.current = performance.now();
  }, []);

  return {
    breathing,
    holdBreath,
    resumeBreathing
  };
};

export default useBreathing;
