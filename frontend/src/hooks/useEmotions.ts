/**
 * Emotion Expression Hook
 * Manages emotional states and facial expressions
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import type { AvatarState } from '../types/avatar.types';

// Emotion types beyond basic states
export type Emotion = 
  | 'neutral'
  | 'happy'
  | 'concerned'
  | 'empathetic'
  | 'curious'
  | 'confident'
  | 'thoughtful'
  | 'attentive'
  | 'apologetic';

// Facial expression parameters
export interface FacialExpression {
  // Mouth
  smileIntensity: number;    // -1 (frown) to 1 (smile)
  mouthOpenness: number;     // 0 to 1
  lipCornerPull: number;     // -1 to 1
  
  // Eyes
  eyeOpenness: number;       // 0.5 to 1.2
  eyeSquint: number;         // 0 to 1
  pupilSize: number;         // 0.8 to 1.2
  
  // Eyebrows
  browRaise: number;         // 0 to 1
  browFurrow: number;        // 0 to 1
  browTilt: number;          // -1 (sad) to 1 (surprised)
  
  // Head
  headTilt: number;          // -1 to 1
  headNod: number;           // -1 to 1
  
  // Cheeks
  cheekRaise: number;        // 0 to 1 (for genuine smile)
}

// Preset expressions for each emotion
const EMOTION_EXPRESSIONS: Record<Emotion, FacialExpression> = {
  neutral: {
    smileIntensity: 0,
    mouthOpenness: 0,
    lipCornerPull: 0,
    eyeOpenness: 1,
    eyeSquint: 0,
    pupilSize: 1,
    browRaise: 0,
    browFurrow: 0,
    browTilt: 0,
    headTilt: 0,
    headNod: 0,
    cheekRaise: 0
  },
  happy: {
    smileIntensity: 0.7,
    mouthOpenness: 0.1,
    lipCornerPull: 0.6,
    eyeOpenness: 0.9,
    eyeSquint: 0.3,
    pupilSize: 1.05,
    browRaise: 0.2,
    browFurrow: 0,
    browTilt: 0.1,
    headTilt: 0.1,
    headNod: 0,
    cheekRaise: 0.5
  },
  concerned: {
    smileIntensity: -0.2,
    mouthOpenness: 0,
    lipCornerPull: -0.2,
    eyeOpenness: 1.1,
    eyeSquint: 0,
    pupilSize: 1.05,
    browRaise: 0.3,
    browFurrow: 0.4,
    browTilt: -0.3,
    headTilt: -0.1,
    headNod: 0.1,
    cheekRaise: 0
  },
  empathetic: {
    smileIntensity: 0.2,
    mouthOpenness: 0,
    lipCornerPull: 0.1,
    eyeOpenness: 0.95,
    eyeSquint: 0.1,
    pupilSize: 1.08,
    browRaise: 0.15,
    browFurrow: 0.2,
    browTilt: -0.15,
    headTilt: 0.15,
    headNod: 0.1,
    cheekRaise: 0.1
  },
  curious: {
    smileIntensity: 0.15,
    mouthOpenness: 0.05,
    lipCornerPull: 0.1,
    eyeOpenness: 1.15,
    eyeSquint: 0,
    pupilSize: 1.1,
    browRaise: 0.5,
    browFurrow: 0,
    browTilt: 0.2,
    headTilt: 0.2,
    headNod: -0.1,
    cheekRaise: 0
  },
  confident: {
    smileIntensity: 0.3,
    mouthOpenness: 0,
    lipCornerPull: 0.2,
    eyeOpenness: 0.95,
    eyeSquint: 0.15,
    pupilSize: 1,
    browRaise: 0,
    browFurrow: 0,
    browTilt: 0,
    headTilt: 0,
    headNod: -0.1,
    cheekRaise: 0.2
  },
  thoughtful: {
    smileIntensity: 0,
    mouthOpenness: 0,
    lipCornerPull: 0.05,
    eyeOpenness: 0.85,
    eyeSquint: 0.2,
    pupilSize: 0.95,
    browRaise: 0.1,
    browFurrow: 0.3,
    browTilt: 0,
    headTilt: 0.1,
    headNod: -0.1,
    cheekRaise: 0
  },
  attentive: {
    smileIntensity: 0.1,
    mouthOpenness: 0,
    lipCornerPull: 0,
    eyeOpenness: 1.1,
    eyeSquint: 0,
    pupilSize: 1.05,
    browRaise: 0.2,
    browFurrow: 0,
    browTilt: 0,
    headTilt: 0.05,
    headNod: 0.15,
    cheekRaise: 0
  },
  apologetic: {
    smileIntensity: 0.1,
    mouthOpenness: 0,
    lipCornerPull: -0.1,
    eyeOpenness: 0.9,
    eyeSquint: 0.1,
    pupilSize: 1,
    browRaise: 0.3,
    browFurrow: 0.3,
    browTilt: -0.2,
    headTilt: -0.15,
    headNod: 0.2,
    cheekRaise: 0
  }
};

// Map avatar states to default emotions
const STATE_EMOTIONS: Record<AvatarState, Emotion> = {
  idle: 'neutral',
  listening: 'attentive',
  thinking: 'thoughtful',
  speaking: 'confident',
  error: 'apologetic'
};

interface UseEmotionsOptions {
  transitionDuration?: number;
  avatarState?: AvatarState;
}

export const useEmotions = (options: UseEmotionsOptions = {}) => {
  const {
    transitionDuration = 500,
    avatarState = 'idle'
  } = options;

  const [currentEmotion, setCurrentEmotion] = useState<Emotion>('neutral');
  const [expression, setExpression] = useState<FacialExpression>(EMOTION_EXPRESSIONS.neutral);
  const [isTransitioning, setIsTransitioning] = useState(false);

  const targetExpressionRef = useRef<FacialExpression>(EMOTION_EXPRESSIONS.neutral);
  const animationRef = useRef<number>(0);
  const transitionStartRef = useRef<number>(0);
  const startExpressionRef = useRef<FacialExpression>(EMOTION_EXPRESSIONS.neutral);

  // Easing function for smooth transitions
  const easeOutCubic = (t: number): number => 1 - Math.pow(1 - t, 3);

  // Interpolate between two expressions
  const interpolateExpression = (
    start: FacialExpression,
    end: FacialExpression,
    progress: number
  ): FacialExpression => {
    const t = easeOutCubic(progress);
    
    return {
      smileIntensity: start.smileIntensity + (end.smileIntensity - start.smileIntensity) * t,
      mouthOpenness: start.mouthOpenness + (end.mouthOpenness - start.mouthOpenness) * t,
      lipCornerPull: start.lipCornerPull + (end.lipCornerPull - start.lipCornerPull) * t,
      eyeOpenness: start.eyeOpenness + (end.eyeOpenness - start.eyeOpenness) * t,
      eyeSquint: start.eyeSquint + (end.eyeSquint - start.eyeSquint) * t,
      pupilSize: start.pupilSize + (end.pupilSize - start.pupilSize) * t,
      browRaise: start.browRaise + (end.browRaise - start.browRaise) * t,
      browFurrow: start.browFurrow + (end.browFurrow - start.browFurrow) * t,
      browTilt: start.browTilt + (end.browTilt - start.browTilt) * t,
      headTilt: start.headTilt + (end.headTilt - start.headTilt) * t,
      headNod: start.headNod + (end.headNod - start.headNod) * t,
      cheekRaise: start.cheekRaise + (end.cheekRaise - start.cheekRaise) * t
    };
  };

  // Animation loop for transitions
  const animate = useCallback((timestamp: number) => {
    if (!isTransitioning) return;

    const elapsed = timestamp - transitionStartRef.current;
    const progress = Math.min(1, elapsed / transitionDuration);

    const newExpression = interpolateExpression(
      startExpressionRef.current,
      targetExpressionRef.current,
      progress
    );

    setExpression(newExpression);

    if (progress < 1) {
      animationRef.current = requestAnimationFrame(animate);
    } else {
      setIsTransitioning(false);
    }
  }, [isTransitioning, transitionDuration]);

  // Start transition animation
  useEffect(() => {
    if (isTransitioning) {
      transitionStartRef.current = performance.now();
      animationRef.current = requestAnimationFrame(animate);
    }

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [isTransitioning, animate]);

  // Set emotion
  const setEmotion = useCallback((emotion: Emotion) => {
    if (emotion === currentEmotion && !isTransitioning) return;

    setCurrentEmotion(emotion);
    startExpressionRef.current = { ...expression };
    targetExpressionRef.current = EMOTION_EXPRESSIONS[emotion];
    setIsTransitioning(true);
  }, [currentEmotion, expression, isTransitioning]);

  // Update emotion based on avatar state
  useEffect(() => {
    const defaultEmotion = STATE_EMOTIONS[avatarState];
    setEmotion(defaultEmotion);
  }, [avatarState, setEmotion]);

  // Blend emotions
  const blendEmotions = useCallback((
    primaryEmotion: Emotion,
    secondaryEmotion: Emotion,
    blendFactor: number // 0 = primary, 1 = secondary
  ) => {
    const primary = EMOTION_EXPRESSIONS[primaryEmotion];
    const secondary = EMOTION_EXPRESSIONS[secondaryEmotion];
    
    startExpressionRef.current = { ...expression };
    targetExpressionRef.current = interpolateExpression(primary, secondary, blendFactor);
    setIsTransitioning(true);
  }, [expression]);

  // Add micro-expression (brief expression flash)
  const flashMicroExpression = useCallback((emotion: Emotion, duration = 200) => {
    const originalExpression = { ...expression };
    const microExpression = EMOTION_EXPRESSIONS[emotion];
    
    // Quick transition to micro-expression
    startExpressionRef.current = originalExpression;
    targetExpressionRef.current = microExpression;
    setIsTransitioning(true);
    
    // Return to original after duration
    setTimeout(() => {
      startExpressionRef.current = microExpression;
      targetExpressionRef.current = originalExpression;
      setIsTransitioning(true);
    }, duration);
  }, [expression]);

  return {
    currentEmotion,
    expression,
    isTransitioning,
    setEmotion,
    blendEmotions,
    flashMicroExpression
  };
};

export default useEmotions;
