/**
 * Eyes Component
 * Realistic eye rendering with blinking, look direction, and expression support
 */

import React, { useMemo } from 'react';
import type { EyeProps } from '../../types/avatar.types';
import { RAFIKI_COLORS } from '../../types/avatar.types';

const Eye: React.FC<EyeProps> = ({
  state,
  position,
  lookDirection = { x: 0, y: 0 },
  glowColor = 'rgba(255, 255, 255, 0.3)',
  pupilDilation = 1,
  expressionSquint = 0
}) => {
  const isLeft = position === 'left';
  
  // Calculate eye dimensions based on state and expression
  const eyeDimensions = useMemo(() => {
    const baseHeight = 40;
    const baseWidth = 32;
    
    // Apply expression squint
    const squintFactor = 1 - expressionSquint * 0.4;
    
    switch (state) {
      case 'closed':
        return { height: 2, width: baseWidth, opacity: 1 };
      case 'half':
        return { height: baseHeight * 0.5 * squintFactor, width: baseWidth, opacity: 1 };
      case 'squint':
        return { height: baseHeight * 0.4, width: baseWidth * 0.9, opacity: 1 };
      case 'open':
      default:
        return { height: baseHeight * squintFactor, width: baseWidth, opacity: 1 };
    }
  }, [state, expressionSquint]);

  // Pupil size with dilation
  const pupilSize = useMemo(() => {
    const baseSize = 6;
    return baseSize * Math.max(0.7, Math.min(1.3, pupilDilation));
  }, [pupilDilation]);

  // Iris position based on look direction
  const irisOffset = useMemo(() => ({
    x: lookDirection.x * 4,
    y: lookDirection.y * 3
  }), [lookDirection]);

  // Base positions
  const baseX = isLeft ? 35 : 65;
  const baseY = 45;

  return (
    <g className={`rafiki-eye rafiki-eye--${position}`}>
      {/* Eye white (sclera) */}
      <defs>
        <clipPath id={`eye-clip-${position}`}>
          <ellipse
            cx={baseX}
            cy={baseY}
            rx={eyeDimensions.width / 2}
            ry={eyeDimensions.height / 2}
          />
        </clipPath>
        <radialGradient id={`sclera-gradient-${position}`} cx="50%" cy="30%" r="70%">
          <stop offset="0%" stopColor="#FFFFFF" />
          <stop offset="100%" stopColor="#F0F0F0" />
        </radialGradient>
        <radialGradient id={`iris-gradient-${position}`} cx="40%" cy="30%" r="60%">
          <stop offset="0%" stopColor="#4A3728" />
          <stop offset="60%" stopColor="#2C1810" />
          <stop offset="100%" stopColor="#1A0F0A" />
        </radialGradient>
      </defs>

      {/* Eye shadow */}
      <ellipse
        cx={baseX}
        cy={baseY + 2}
        rx={eyeDimensions.width / 2 + 2}
        ry={eyeDimensions.height / 2 + 1}
        fill="rgba(0, 0, 0, 0.2)"
        style={{
          transition: 'all 0.15s ease-out'
        }}
      />

      {/* Sclera (eye white) */}
      <ellipse
        cx={baseX}
        cy={baseY}
        rx={eyeDimensions.width / 2}
        ry={eyeDimensions.height / 2}
        fill={`url(#sclera-gradient-${position})`}
        style={{
          transition: 'all 0.15s ease-out'
        }}
      />

      {/* Eye contents (clipped) */}
      <g clipPath={`url(#eye-clip-${position})`}>
        {/* Iris */}
        {state !== 'closed' && (
          <circle
            cx={baseX + irisOffset.x}
            cy={baseY + irisOffset.y}
            r={14}
            fill={`url(#iris-gradient-${position})`}
            style={{
              transition: 'cx 0.1s ease-out, cy 0.1s ease-out'
            }}
          />
        )}

        {/* Iris detail ring */}
        {state !== 'closed' && (
          <circle
            cx={baseX + irisOffset.x}
            cy={baseY + irisOffset.y}
            r={14}
            fill="none"
            stroke="rgba(74, 55, 40, 0.3)"
            strokeWidth="1"
          />
        )}

        {/* Pupil */}
        {state !== 'closed' && (
          <circle
            cx={baseX + irisOffset.x}
            cy={baseY + irisOffset.y}
            r={pupilSize}
            fill={RAFIKI_COLORS.primary.black}
            style={{
              transition: 'cx 0.1s ease-out, cy 0.1s ease-out, r 0.3s ease-out'
            }}
          />
        )}

        {/* Pupil highlight (catchlight) */}
        {state !== 'closed' && (
          <>
            <circle
              cx={baseX + irisOffset.x - 3}
              cy={baseY + irisOffset.y - 4}
              r={2.5}
              fill="rgba(255, 255, 255, 0.9)"
            />
            <circle
              cx={baseX + irisOffset.x + 2}
              cy={baseY + irisOffset.y + 2}
              r={1}
              fill="rgba(255, 255, 255, 0.5)"
            />
          </>
        )}
      </g>

      {/* Upper eyelid */}
      <path
        d={`M ${baseX - eyeDimensions.width / 2 - 3} ${baseY - 2}
            Q ${baseX} ${baseY - eyeDimensions.height / 2 - 8}
            ${baseX + eyeDimensions.width / 2 + 3} ${baseY - 2}`}
        fill="none"
        stroke={RAFIKI_COLORS.skin.shadow}
        strokeWidth="3"
        strokeLinecap="round"
      />

      {/* Eyelash hints */}
      <path
        d={`M ${baseX - eyeDimensions.width / 2 - 2} ${baseY - 3}
            Q ${baseX} ${baseY - eyeDimensions.height / 2 - 10}
            ${baseX + eyeDimensions.width / 2 + 2} ${baseY - 3}`}
        fill="none"
        stroke={RAFIKI_COLORS.primary.black}
        strokeWidth="1.5"
        strokeLinecap="round"
        opacity="0.7"
      />

      {/* Eye glow overlay */}
      <ellipse
        cx={baseX}
        cy={baseY}
        rx={eyeDimensions.width / 2 + 5}
        ry={eyeDimensions.height / 2 + 5}
        fill="none"
        stroke={glowColor}
        strokeWidth="2"
        opacity="0.3"
        style={{
          filter: 'blur(3px)',
          transition: 'all 0.3s ease'
        }}
      />
    </g>
  );
};

export default Eye;
