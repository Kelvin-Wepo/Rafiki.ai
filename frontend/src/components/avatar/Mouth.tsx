/**
 * Mouth Component
 * Lip-sync capable mouth with viseme shapes
 */

import React, { useMemo } from 'react';
import type { MouthProps, Viseme } from '../../types/avatar.types';
import { RAFIKI_COLORS } from '../../types/avatar.types';

// Mouth shape configurations for each viseme
const VISEME_SHAPES: Record<Viseme, {
  width: number;
  height: number;
  openness: number;
  lipCurve: number;
  path: string;
}> = {
  neutral: {
    width: 28,
    height: 4,
    openness: 0,
    lipCurve: 0.2,
    path: 'M 36 72 Q 50 74 64 72'
  },
  aa: {
    width: 32,
    height: 16,
    openness: 0.8,
    lipCurve: 0,
    path: 'M 34 68 Q 50 88 66 68 Q 50 72 34 68'
  },
  ee: {
    width: 34,
    height: 8,
    openness: 0.4,
    lipCurve: 0.3,
    path: 'M 33 70 Q 50 78 67 70 Q 50 73 33 70'
  },
  oo: {
    width: 18,
    height: 18,
    openness: 0.7,
    lipCurve: -0.2,
    path: 'M 41 68 Q 50 86 59 68 Q 50 70 41 68'
  },
  oh: {
    width: 24,
    height: 14,
    openness: 0.6,
    lipCurve: 0,
    path: 'M 38 69 Q 50 84 62 69 Q 50 72 38 69'
  },
  consonant: {
    width: 28,
    height: 2,
    openness: 0.1,
    lipCurve: 0,
    path: 'M 36 72 Q 50 73 64 72'
  },
  th: {
    width: 26,
    height: 6,
    openness: 0.3,
    lipCurve: 0.1,
    path: 'M 37 71 Q 50 77 63 71 Q 50 73 37 71'
  },
  ff: {
    width: 30,
    height: 4,
    openness: 0.2,
    lipCurve: -0.1,
    path: 'M 35 72 Q 50 76 65 72'
  },
  smile: {
    width: 34,
    height: 6,
    openness: 0.3,
    lipCurve: 0.5,
    path: 'M 33 70 Q 50 80 67 70 Q 50 74 33 70'
  }
};

const Mouth: React.FC<MouthProps> = ({
  viseme,
  intensity = 1,
  state,
  smileIntensity = 0,
  lipCornerPull = 0
}) => {
  // Get current mouth shape
  const mouthShape = useMemo(() => {
    const shape = VISEME_SHAPES[viseme];
    
    // Calculate combined lip curve from viseme and expression
    let baseLipCurve = shape.lipCurve;
    
    // Apply smile intensity
    if (smileIntensity !== 0) {
      baseLipCurve += smileIntensity * 0.5;
    }
    
    // Apply lip corner pull
    if (lipCornerPull !== 0) {
      baseLipCurve += lipCornerPull * 0.3;
    }
    
    // Modify based on avatar state
    if (state === 'error') {
      return {
        ...shape,
        lipCurve: Math.min(baseLipCurve, -0.2) // Ensure frown in error state
      };
    }
    
    if (state === 'thinking') {
      return {
        ...shape,
        lipCurve: baseLipCurve + 0.05 // Slight pursed
      };
    }
    
    if (state === 'listening') {
      return {
        ...shape,
        lipCurve: baseLipCurve + 0.1 // Slightly attentive
      };
    }
    
    return {
      ...shape,
      lipCurve: baseLipCurve
    };
  }, [viseme, state, smileIntensity, lipCornerPull]);

  // Interpolate shape based on intensity
  const interpolatedShape = useMemo(() => {
    const neutral = VISEME_SHAPES.neutral;
    const target = mouthShape;
    
    return {
      width: neutral.width + (target.width - neutral.width) * intensity,
      height: neutral.height + (target.height - neutral.height) * intensity,
      openness: neutral.openness + (target.openness - neutral.openness) * intensity,
      lipCurve: neutral.lipCurve + (target.lipCurve - neutral.lipCurve) * intensity
    };
  }, [mouthShape, intensity]);

  const baseX = 50;
  const baseY = 72;
  const { width, height, openness, lipCurve } = interpolatedShape;

  // Generate dynamic mouth path
  const generateMouthPath = () => {
    const halfWidth = width / 2;
    const mouthOpen = height * openness;
    const curve = lipCurve * 10;
    
    // Upper lip
    const upperLip = `
      M ${baseX - halfWidth} ${baseY}
      Q ${baseX - halfWidth / 2} ${baseY - 3 - curve}
        ${baseX} ${baseY - 2 - curve}
      Q ${baseX + halfWidth / 2} ${baseY - 3 - curve}
        ${baseX + halfWidth} ${baseY}
    `;
    
    // Lower lip (if mouth is open)
    const lowerLip = mouthOpen > 2 ? `
      Q ${baseX + halfWidth / 2} ${baseY + mouthOpen + curve}
        ${baseX} ${baseY + mouthOpen + curve + 2}
      Q ${baseX - halfWidth / 2} ${baseY + mouthOpen + curve}
        ${baseX - halfWidth} ${baseY}
    ` : `
      Q ${baseX} ${baseY + 2 + curve}
        ${baseX - halfWidth} ${baseY}
    `;
    
    return upperLip + lowerLip;
  };

  return (
    <g className="rafiki-mouth">
      {/* Lip definitions */}
      <defs>
        <linearGradient id="lip-gradient" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stopColor="#8B4557" />
          <stop offset="50%" stopColor="#A0515F" />
          <stop offset="100%" stopColor="#7A3D4D" />
        </linearGradient>
        <linearGradient id="mouth-interior" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stopColor="#4A1A24" />
          <stop offset="100%" stopColor="#2D1015" />
        </linearGradient>
      </defs>

      {/* Mouth shadow */}
      <ellipse
        cx={baseX}
        cy={baseY + 3}
        rx={width / 2 + 2}
        ry={4}
        fill="rgba(0, 0, 0, 0.15)"
        style={{ transition: 'all 0.1s ease-out' }}
      />

      {/* Mouth interior (visible when open) */}
      {interpolatedShape.openness > 0.1 && (
        <ellipse
          cx={baseX}
          cy={baseY + height * openness / 2}
          rx={width / 2 - 2}
          ry={height * openness / 2}
          fill="url(#mouth-interior)"
          style={{ transition: 'all 0.1s ease-out' }}
        />
      )}

      {/* Teeth hint (visible when very open) */}
      {interpolatedShape.openness > 0.5 && (
        <rect
          x={baseX - width / 4}
          y={baseY - 1}
          width={width / 2}
          height={4}
          rx={1}
          fill="rgba(255, 255, 255, 0.9)"
          style={{ transition: 'all 0.1s ease-out' }}
        />
      )}

      {/* Lips */}
      <path
        d={generateMouthPath()}
        fill="url(#lip-gradient)"
        stroke={RAFIKI_COLORS.skin.shadow}
        strokeWidth="0.5"
        style={{
          transition: 'all 0.1s ease-out'
        }}
      />

      {/* Upper lip line */}
      <path
        d={`M ${baseX - width / 2 + 2} ${baseY}
            Q ${baseX} ${baseY - 3 - lipCurve * 8}
            ${baseX + width / 2 - 2} ${baseY}`}
        fill="none"
        stroke="rgba(0, 0, 0, 0.2)"
        strokeWidth="0.5"
        style={{ transition: 'all 0.1s ease-out' }}
      />

      {/* Lip highlight */}
      <ellipse
        cx={baseX}
        cy={baseY + height * openness / 2 + 3}
        rx={width / 4}
        ry={2}
        fill="rgba(255, 255, 255, 0.15)"
        style={{ transition: 'all 0.1s ease-out' }}
      />

      {/* Cupid's bow highlight */}
      <path
        d={`M ${baseX - 4} ${baseY - 2}
            Q ${baseX} ${baseY - 4}
            ${baseX + 4} ${baseY - 2}`}
        fill="none"
        stroke="rgba(255, 255, 255, 0.2)"
        strokeWidth="1"
        strokeLinecap="round"
      />
    </g>
  );
};

export default Mouth;
