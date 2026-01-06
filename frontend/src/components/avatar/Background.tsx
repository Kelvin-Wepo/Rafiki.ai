/**
 * Background Component
 * Civic-grade backdrop with subtle Kenyan flag color integration
 */

import React from 'react';
import type { AvatarState } from '../../types/avatar.types';
import { RAFIKI_COLORS, STATE_CONFIGS } from '../../types/avatar.types';

interface BackgroundProps {
  state: AvatarState;
}

const Background: React.FC<BackgroundProps> = ({ state }) => {
  const glowConfig = STATE_CONFIGS[state].glow;

  return (
    <g className="rafiki-background">
      <defs>
        {/* Main background gradient */}
        <radialGradient id="bg-gradient" cx="50%" cy="50%" r="70%">
          <stop offset="0%" stopColor="#2a2a3a" />
          <stop offset="50%" stopColor="#1a1a2a" />
          <stop offset="100%" stopColor="#0f0f1a" />
        </radialGradient>

        {/* Civic pattern overlay */}
        <pattern id="civic-pattern" width="20" height="20" patternUnits="userSpaceOnUse">
          <circle cx="10" cy="10" r="0.5" fill="rgba(255, 255, 255, 0.03)" />
        </pattern>

        {/* Kenya flag accent gradients */}
        <linearGradient id="kenya-accent-top" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stopColor={RAFIKI_COLORS.primary.black} stopOpacity="0.1" />
          <stop offset="50%" stopColor={RAFIKI_COLORS.primary.red} stopOpacity="0.05" />
          <stop offset="100%" stopColor={RAFIKI_COLORS.primary.black} stopOpacity="0.1" />
        </linearGradient>

        <linearGradient id="kenya-accent-bottom" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stopColor={RAFIKI_COLORS.primary.black} stopOpacity="0.1" />
          <stop offset="50%" stopColor={RAFIKI_COLORS.primary.green} stopOpacity="0.05" />
          <stop offset="100%" stopColor={RAFIKI_COLORS.primary.black} stopOpacity="0.1" />
        </linearGradient>

        {/* State-reactive glow */}
        <radialGradient id="state-glow" cx="50%" cy="50%" r="60%">
          <stop offset="0%" stopColor={glowConfig.color} stopOpacity={glowConfig.intensity * 0.3}>
            <animate
              attributeName="stop-opacity"
              values={`${glowConfig.intensity * 0.3};${glowConfig.intensity * 0.15};${glowConfig.intensity * 0.3}`}
              dur={`${glowConfig.pulseSpeed}ms`}
              repeatCount="indefinite"
            />
          </stop>
          <stop offset="100%" stopColor={glowConfig.color} stopOpacity="0" />
        </radialGradient>
      </defs>

      {/* Base background */}
      <rect
        x="0"
        y="0"
        width="100"
        height="100"
        fill="url(#bg-gradient)"
      />

      {/* Civic pattern overlay */}
      <rect
        x="0"
        y="0"
        width="100"
        height="100"
        fill="url(#civic-pattern)"
      />

      {/* Top accent stripe (subtle red) */}
      <rect
        x="0"
        y="0"
        width="100"
        height="3"
        fill="url(#kenya-accent-top)"
      />

      {/* Bottom accent stripe (subtle green) */}
      <rect
        x="0"
        y="97"
        width="100"
        height="3"
        fill="url(#kenya-accent-bottom)"
      />

      {/* Central white accent line */}
      <line
        x1="0"
        y1="50"
        x2="5"
        y2="50"
        stroke={RAFIKI_COLORS.primary.white}
        strokeWidth="0.5"
        opacity="0.1"
      />
      <line
        x1="95"
        y1="50"
        x2="100"
        y2="50"
        stroke={RAFIKI_COLORS.primary.white}
        strokeWidth="0.5"
        opacity="0.1"
      />

      {/* State-reactive ambient glow */}
      <ellipse
        cx="50"
        cy="50"
        rx="60"
        ry="60"
        fill="url(#state-glow)"
        style={{ transition: 'all 0.5s ease-out' }}
      />

      {/* Corner accents - government seal style */}
      <g opacity="0.05">
        {/* Top left corner */}
        <path
          d="M 0 0 L 15 0 L 0 15 Z"
          fill={RAFIKI_COLORS.primary.white}
        />
        {/* Top right corner */}
        <path
          d="M 100 0 L 85 0 L 100 15 Z"
          fill={RAFIKI_COLORS.primary.white}
        />
        {/* Bottom left corner */}
        <path
          d="M 0 100 L 15 100 L 0 85 Z"
          fill={RAFIKI_COLORS.primary.white}
        />
        {/* Bottom right corner */}
        <path
          d="M 100 100 L 85 100 L 100 85 Z"
          fill={RAFIKI_COLORS.primary.white}
        />
      </g>

      {/* Vignette effect */}
      <rect
        x="0"
        y="0"
        width="100"
        height="100"
        fill="none"
        stroke="rgba(0, 0, 0, 0.4)"
        strokeWidth="15"
        style={{ filter: 'blur(10px)' }}
      />
    </g>
  );
};

export default Background;
