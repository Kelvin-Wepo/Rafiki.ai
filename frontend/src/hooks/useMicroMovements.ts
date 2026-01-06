/**
 * Micro-Movement Animation Hook
 * Subtle facial movements for lifelike appearance
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import type { AvatarState } from '../types/avatar.types';
import { STATE_CONFIGS, DEFAULT_ANIMATION_CONFIG } from '../types/avatar.types';

interface MicroMovement {
  headTilt: number;      // -1 to 1
  headNod: number;       // -1 to 1
  eyeShift: { x: number; y: number }; // -1 to 1 each
  browRaise: number;     // 0 to 1
}

interface UseMicroMovementsOptions {
  intensity?: number;
  updateInterval?: number;
  avatarState?: AvatarState;
}

export const useMicroMovements = (options: UseMicroMovementsOptions = {}) => {
  const {
    intensity = DEFAULT_ANIMATION_CONFIG.microMovementIntensity,
    updateInterval = 100,
    avatarState = 'idle'
  } = options;

  const [movement, setMovement] = useState<MicroMovement>({
    headTilt: 0,
    headNod: 0,
    eyeShift: { x: 0, y: 0 },
    browRaise: 0
  });

  const targetRef = useRef<MicroMovement>({
    headTilt: 0,
    headNod: 0,
    eyeShift: { x: 0, y: 0 },
    browRaise: 0
  });
  const animationFrameRef = useRef<number>(0);
  const lastUpdateRef = useRef<number>(0);

  // Get state-specific intensity modifier
  const getStateIntensity = useCallback(() => {
    const config = STATE_CONFIGS[avatarState];
    return (config?.animation?.microMovementIntensity ?? intensity);
  }, [avatarState, intensity]);

  // Generate random target positions
  const updateTarget = useCallback(() => {
    const stateIntensity = getStateIntensity();
    
    targetRef.current = {
      headTilt: (Math.random() - 0.5) * 2 * stateIntensity * 0.3,
      headNod: (Math.random() - 0.5) * 2 * stateIntensity * 0.2,
      eyeShift: {
        x: (Math.random() - 0.5) * 2 * stateIntensity * 0.4,
        y: (Math.random() - 0.5) * 2 * stateIntensity * 0.3
      },
      browRaise: Math.random() * stateIntensity * 0.2
    };
  }, [getStateIntensity]);

  // Smooth interpolation towards target
  const animate = useCallback((timestamp: number) => {
    const elapsed = timestamp - lastUpdateRef.current;
    
    if (elapsed >= updateInterval) {
      lastUpdateRef.current = timestamp;
      
      // Randomly update target occasionally
      if (Math.random() < 0.1) {
        updateTarget();
      }

      setMovement(prev => {
        const lerp = (start: number, end: number, t: number) => 
          start + (end - start) * t;
        const smoothing = 0.1;

        return {
          headTilt: lerp(prev.headTilt, targetRef.current.headTilt, smoothing),
          headNod: lerp(prev.headNod, targetRef.current.headNod, smoothing),
          eyeShift: {
            x: lerp(prev.eyeShift.x, targetRef.current.eyeShift.x, smoothing),
            y: lerp(prev.eyeShift.y, targetRef.current.eyeShift.y, smoothing)
          },
          browRaise: lerp(prev.browRaise, targetRef.current.browRaise, smoothing)
        };
      });
    }

    animationFrameRef.current = requestAnimationFrame(animate);
  }, [updateInterval, updateTarget]);

  // State-specific movement patterns
  useEffect(() => {
    // Reset movements for error state
    if (avatarState === 'error') {
      setMovement({
        headTilt: -0.1,
        headNod: 0,
        eyeShift: { x: 0, y: 0 },
        browRaise: 0.3
      });
      return;
    }

    // Listening state - more attentive positioning
    if (avatarState === 'listening') {
      targetRef.current = {
        headTilt: 0.05,
        headNod: 0.1,
        eyeShift: { x: 0, y: 0.1 },
        browRaise: 0.2
      };
    }

    // Start animation loop
    lastUpdateRef.current = performance.now();
    animationFrameRef.current = requestAnimationFrame(animate);

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [avatarState, animate]);

  return movement;
};

export default useMicroMovements;
