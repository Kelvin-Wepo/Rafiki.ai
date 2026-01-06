/**
 * Rafiki Avatar - Main Component
 * Government AI Voice Assistant Avatar
 * 
 * Features:
 * - Animation-ready layered structure
 * - Real-time audio-driven lip-sync
 * - Natural blinking and micro-movements
 * - State-based glow effects
 * - Accessible design
 */

import React, { useMemo } from 'react';
import type { RafikiAvatarProps, EyeState } from '../../types/avatar.types';
import { STATE_CONFIGS } from '../../types/avatar.types';
import { useBlinking } from '../../hooks/useBlinking';
import { useMicroMovements } from '../../hooks/useMicroMovements';
import Background from './Background';
import FaceBase from './FaceBase';
import Eye from './Eye';
import Mouth from './Mouth';
import GlowOverlay from './GlowOverlay';
import './RafikiAvatar.css';

const RafikiAvatar: React.FC<RafikiAvatarProps> = ({
  state,
  audioData,
  size = 400,
  className = '',
  accessible = true
}) => {
  // Animation hooks
  const { eyeState } = useBlinking({ avatarState: state });
  const microMovement = useMicroMovements({ avatarState: state });

  // Compute mouth viseme from audio data or state
  const currentViseme = useMemo(() => {
    if (state === 'speaking' && audioData?.isSpeaking) {
      return audioData.viseme;
    }
    if (state === 'idle') return 'neutral';
    if (state === 'listening') return 'neutral';
    if (state === 'thinking') return 'neutral';
    if (state === 'error') return 'neutral';
    return 'neutral';
  }, [state, audioData]);

  // Mouth intensity based on audio amplitude
  const mouthIntensity = useMemo(() => {
    if (state === 'speaking' && audioData) {
      return audioData.amplitude;
    }
    return 0;
  }, [state, audioData]);

  // Eye look direction from micro-movements
  const eyeLookDirection = useMemo(() => ({
    x: microMovement.eyeShift.x,
    y: microMovement.eyeShift.y
  }), [microMovement.eyeShift]);

  // Glow color based on state
  const glowColor = STATE_CONFIGS[state].glow.color;

  // Accessibility label
  const ariaLabel = STATE_CONFIGS[state].ariaLabel;

  // Size handling
  const sizeValue = typeof size === 'number' ? `${size}px` : size;

  return (
    <div
      className={`rafiki-avatar rafiki-avatar--${state} ${className}`}
      style={{ width: sizeValue, height: sizeValue }}
      role={accessible ? 'img' : undefined}
      aria-label={accessible ? ariaLabel : undefined}
      aria-live={accessible ? 'polite' : undefined}
    >
      <svg
        viewBox="0 0 100 100"
        preserveAspectRatio="xMidYMid meet"
        className="rafiki-avatar__svg"
      >
        {/* Layer 1: Background */}
        <Background state={state} />

        {/* Layer 2: Glow Overlay (behind face) */}
        <GlowOverlay state={state} />

        {/* Layer 3: Face Base with micro-movements */}
        <FaceBase
          headTilt={microMovement.headTilt}
          headNod={microMovement.headNod}
          browRaise={microMovement.browRaise}
        />

        {/* Layer 4: Eyes */}
        <g
          className="rafiki-eyes"
          transform={`translate(0, ${microMovement.headNod * 2})`}
        >
          <Eye
            state={eyeState as EyeState}
            position="left"
            lookDirection={eyeLookDirection}
            glowColor={glowColor}
          />
          <Eye
            state={eyeState as EyeState}
            position="right"
            lookDirection={eyeLookDirection}
            glowColor={glowColor}
          />
        </g>

        {/* Layer 5: Mouth */}
        <g
          className="rafiki-mouth-container"
          transform={`translate(0, ${microMovement.headNod * 2})`}
        >
          <Mouth
            viseme={currentViseme}
            intensity={mouthIntensity}
            state={state}
          />
        </g>

        {/* Layer 6: Front Glow Overlay (for emphasis) */}
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
      </svg>

      {/* Screen reader status announcements */}
      {accessible && (
        <span className="rafiki-avatar__sr-only" role="status">
          {ariaLabel}
        </span>
      )}
    </div>
  );
};

export default RafikiAvatar;
