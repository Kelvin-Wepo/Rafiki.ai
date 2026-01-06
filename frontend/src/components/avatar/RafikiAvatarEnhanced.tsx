/**
 * Rafiki Avatar - Enhanced Main Component
 * Government AI Voice Assistant Avatar
 * 
 * Features:
 * - Animation-ready layered structure
 * - Real-time audio-driven lip-sync with phoneme analysis
 * - Natural blinking and micro-movements
 * - Breathing animation for lifelike appearance
 * - Eye tracking following cursor
 * - Emotional expressions
 * - Particle effects and voice waveform visualization
 * - Professional jewelry accessories
 * - State-based glow effects
 * - Accessible design with keyboard navigation
 */

import React, { useMemo, useRef, useCallback, useEffect, useState } from 'react';
import type { RafikiAvatarProps, EyeState } from '../../types/avatar.types';
import { STATE_CONFIGS } from '../../types/avatar.types';
import { useBlinking } from '../../hooks/useBlinking';
import { useMicroMovements } from '../../hooks/useMicroMovements';
import { useBreathing } from '../../hooks/useBreathing';
import { useEyeTracking } from '../../hooks/useEyeTracking';
import { useEmotions, type Emotion } from '../../hooks/useEmotions';
import Background from './Background';
import FaceBase from './FaceBase';
import Eye from './Eye';
import Mouth from './Mouth';
import GlowOverlay from './GlowOverlay';
import Hair from './Hair';
import Jewelry from './Jewelry';
import ParticleEffects from './ParticleEffects';
import VoiceWaveform from './VoiceWaveform';
import './RafikiAvatar.css';

// Extended props interface
interface EnhancedRafikiAvatarProps extends RafikiAvatarProps {
  showParticles?: boolean;
  showWaveform?: boolean;
  showJewelry?: boolean;
  jewelryStyle?: 'gold-studs' | 'pearl-drops' | 'hoops' | 'none';
  hairStyle?: 'professional' | 'natural' | 'braided';
  emotion?: Emotion;
  followCursor?: boolean;
  onEmotionChange?: (emotion: Emotion) => void;
}

const RafikiAvatar: React.FC<EnhancedRafikiAvatarProps> = ({
  state,
  audioData,
  size = 400,
  className = '',
  accessible = true,
  showParticles = true,
  showWaveform = true,
  showJewelry = true,
  jewelryStyle = 'gold-studs',
  hairStyle = 'professional',
  emotion: externalEmotion,
  followCursor = true,
  onEmotionChange
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [isKeyboardFocused, setIsKeyboardFocused] = useState(false);

  // Animation hooks
  const { eyeState } = useBlinking({ avatarState: state });
  const microMovement = useMicroMovements({ avatarState: state });
  const { breathing } = useBreathing({ avatarState: state });
  const { eyePosition } = useEyeTracking({ 
    containerRef: containerRef as React.RefObject<HTMLElement>, 
    followCursor,
    avatarState: state 
  });
  const { 
    currentEmotion, 
    expression, 
    setEmotion 
  } = useEmotions({ avatarState: state });

  // Handle external emotion changes
  useEffect(() => {
    if (externalEmotion && externalEmotion !== currentEmotion) {
      setEmotion(externalEmotion);
    }
  }, [externalEmotion, currentEmotion, setEmotion]);

  // Notify parent of emotion changes
  useEffect(() => {
    if (onEmotionChange) {
      onEmotionChange(currentEmotion);
    }
  }, [currentEmotion, onEmotionChange]);

  // Compute mouth viseme from audio data or state
  const currentViseme = useMemo(() => {
    if (state === 'speaking' && audioData?.isSpeaking) {
      return audioData.viseme;
    }
    // Use expression-based mouth shape for other states
    if (expression.smileIntensity > 0.3) return 'smile';
    if (state === 'idle') return 'neutral';
    if (state === 'listening') return 'neutral';
    if (state === 'thinking') return 'neutral';
    if (state === 'error') return 'neutral';
    return 'neutral';
  }, [state, audioData, expression.smileIntensity]);

  // Mouth intensity based on audio amplitude or expression
  const mouthIntensity = useMemo(() => {
    if (state === 'speaking' && audioData) {
      return audioData.amplitude;
    }
    return Math.abs(expression.smileIntensity);
  }, [state, audioData, expression.smileIntensity]);

  // Combined eye look direction (cursor tracking + micro-movements + expression)
  const eyeLookDirection = useMemo(() => ({
    x: eyePosition.x + microMovement.eyeShift.x * 0.3,
    y: eyePosition.y + microMovement.eyeShift.y * 0.3
  }), [eyePosition, microMovement.eyeShift]);

  // Combined head movement (micro-movements + breathing + expression)
  const headMovement = useMemo(() => ({
    tilt: microMovement.headTilt + expression.headTilt * 0.5,
    nod: microMovement.headNod + breathing.headBob + expression.headNod * 0.5
  }), [microMovement, breathing, expression]);

  // Combined brow position
  const browPosition = useMemo(() => ({
    raise: microMovement.browRaise + expression.browRaise,
    furrow: expression.browFurrow,
    tilt: expression.browTilt
  }), [microMovement.browRaise, expression]);

  // Eye openness combining blink state and expression
  const effectiveEyeState = useMemo((): EyeState => {
    if (eyeState === 'closed') return 'closed';
    if (expression.eyeSquint > 0.5) return 'squint';
    if (expression.eyeOpenness < 0.8 || eyeState === 'half') return 'half';
    return 'open';
  }, [eyeState, expression]);

  // Glow color based on state
  const glowColor = STATE_CONFIGS[state].glow.color;

  // Accessibility label
  const ariaLabel = STATE_CONFIGS[state].ariaLabel;

  // Size handling
  const sizeValue = typeof size === 'number' ? `${size}px` : size;

  // Keyboard handlers for accessibility
  const handleKeyDown = useCallback((event: React.KeyboardEvent) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      // Trigger interaction - this would be handled by parent
    }
  }, []);

  const handleFocus = useCallback(() => {
    setIsKeyboardFocused(true);
  }, []);

  const handleBlur = useCallback(() => {
    setIsKeyboardFocused(false);
  }, []);

  return (
    <div
      ref={containerRef}
      className={`rafiki-avatar rafiki-avatar--${state} ${isKeyboardFocused ? 'rafiki-avatar--focused' : ''} ${className}`}
      style={{ width: sizeValue, height: sizeValue }}
      role={accessible ? 'img' : undefined}
      aria-label={accessible ? ariaLabel : undefined}
      aria-live={accessible ? 'polite' : undefined}
      tabIndex={accessible ? 0 : undefined}
      onKeyDown={accessible ? handleKeyDown : undefined}
      onFocus={accessible ? handleFocus : undefined}
      onBlur={accessible ? handleBlur : undefined}
    >
      <svg
        viewBox="0 0 100 100"
        preserveAspectRatio="xMidYMid meet"
        className="rafiki-avatar__svg"
        aria-hidden="true"
      >
        {/* Layer 1: Background */}
        <Background state={state} />

        {/* Layer 2: Voice Waveform (behind avatar) */}
        {showWaveform && (
          <VoiceWaveform 
            state={state} 
            audioData={audioData}
          />
        )}

        {/* Layer 3: Particle Effects (behind face) */}
        {showParticles && (
          <ParticleEffects 
            state={state} 
            intensity={state === 'thinking' ? 1 : 0.6}
          />
        )}

        {/* Layer 4: Glow Overlay (behind face) */}
        <GlowOverlay state={state} />

        {/* Layer 5: Face Base with combined movements */}
        <g
          className="rafiki-face-group"
          style={{
            transform: `translateY(${breathing.chestRise * 0.5}px)`,
            transition: 'transform 0.1s ease-out'
          }}
        >
          {/* Hair (back layer) */}
          <Hair 
            headTilt={headMovement.tilt}
            headNod={headMovement.nod}
            style={hairStyle}
          />

          <FaceBase
            headTilt={headMovement.tilt}
            headNod={headMovement.nod}
            browRaise={browPosition.raise}
            browFurrow={browPosition.furrow}
            browTilt={browPosition.tilt}
            cheekRaise={expression.cheekRaise}
          />

          {/* Layer 6: Eyes with tracking */}
          <g
            className="rafiki-eyes"
            transform={`translate(0, ${headMovement.nod * 2})`}
          >
            <Eye
              state={effectiveEyeState}
              position="left"
              lookDirection={eyeLookDirection}
              glowColor={glowColor}
              pupilDilation={eyePosition.pupilDilation}
              expressionSquint={expression.eyeSquint}
            />
            <Eye
              state={effectiveEyeState}
              position="right"
              lookDirection={eyeLookDirection}
              glowColor={glowColor}
              pupilDilation={eyePosition.pupilDilation}
              expressionSquint={expression.eyeSquint}
            />
          </g>

          {/* Layer 7: Mouth with expression */}
          <g
            className="rafiki-mouth-container"
            transform={`translate(0, ${headMovement.nod * 2})`}
          >
            <Mouth
              viseme={currentViseme}
              intensity={mouthIntensity}
              state={state}
              smileIntensity={expression.smileIntensity}
              lipCornerPull={expression.lipCornerPull}
            />
          </g>

          {/* Layer 8: Jewelry */}
          {showJewelry && (
            <Jewelry
              headTilt={headMovement.tilt}
              headNod={headMovement.nod}
              style={jewelryStyle}
            />
          )}
        </g>

        {/* Layer 9: Front Glow Overlay (for emphasis) */}
        {(state === 'speaking' || state === 'error') && (
          <circle
            cx="50"
            cy="50"
            r="48"
            fill="none"
            stroke={glowColor}
            strokeWidth="1"
            opacity="0.3"
            style={{ filter: 'blur(2px)' }}
          >
            <animate
              attributeName="opacity"
              values="0.2;0.4;0.2"
              dur="1s"
              repeatCount="indefinite"
            />
          </circle>
        )}

        {/* Keyboard focus indicator */}
        {isKeyboardFocused && (
          <circle
            cx="50"
            cy="50"
            r="49"
            fill="none"
            stroke="#4169E1"
            strokeWidth="2"
            strokeDasharray="4 2"
          >
            <animate
              attributeName="stroke-dashoffset"
              values="0;12"
              dur="0.5s"
              repeatCount="indefinite"
            />
          </circle>
        )}
      </svg>

      {/* Screen reader status announcements */}
      {accessible && (
        <span className="rafiki-avatar__sr-only" role="status">
          {ariaLabel}
        </span>
      )}

      {/* Emotion indicator for debugging - uncomment to enable
      <div className="rafiki-avatar__debug" style={{ display: 'none' }}>
        <p>State: {state}</p>
        <p>Emotion: {currentEmotion}</p>
        <p>Eye: {effectiveEyeState}</p>
      </div>
      */}
    </div>
  );
};

export default RafikiAvatar;
