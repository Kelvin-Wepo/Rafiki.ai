/**
 * Glow Overlay Component
 * Ambient glow effects for different avatar states
 */

import React, { useMemo } from 'react';
import type { AvatarState, GlowConfig } from '../../types/avatar.types';
import { STATE_CONFIGS } from '../../types/avatar.types';

interface GlowOverlayProps {
  state: AvatarState;
  customConfig?: Partial<GlowConfig>;
}

const GlowOverlay: React.FC<GlowOverlayProps> = ({ state, customConfig }) => {
  const glowConfig = useMemo(() => {
    const baseConfig = STATE_CONFIGS[state].glow;
    return { ...baseConfig, ...customConfig };
  }, [state, customConfig]);

  const { color, intensity, pulseSpeed, blur } = glowConfig;

  // Generate unique IDs for gradients
  const gradientId = `glow-gradient-${state}`;
  const filterId = `glow-blur-${state}`;

  return (
    <g className="rafiki-glow-overlay">
      <defs>
        {/* Blur filter */}
        <filter id={filterId} x="-50%" y="-50%" width="200%" height="200%">
          <feGaussianBlur stdDeviation={blur / 4} result="blur" />
          <feMerge>
            <feMergeNode in="blur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>

        {/* Radial gradient for glow */}
        <radialGradient id={gradientId} cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor={color} stopOpacity={intensity}>
            <animate
              attributeName="stop-opacity"
              values={`${intensity};${intensity * 0.5};${intensity}`}
              dur={`${pulseSpeed}ms`}
              repeatCount="indefinite"
            />
          </stop>
          <stop offset="70%" stopColor={color} stopOpacity={intensity * 0.3}>
            <animate
              attributeName="stop-opacity"
              values={`${intensity * 0.3};${intensity * 0.1};${intensity * 0.3}`}
              dur={`${pulseSpeed}ms`}
              repeatCount="indefinite"
            />
          </stop>
          <stop offset="100%" stopColor={color} stopOpacity="0" />
        </radialGradient>
      </defs>

      {/* Main glow circle */}
      <circle
        cx="50"
        cy="50"
        r="55"
        fill={`url(#${gradientId})`}
        filter={`url(#${filterId})`}
        style={{
          mixBlendMode: 'screen',
          transition: 'all 0.5s ease-out'
        }}
      >
        <animate
          attributeName="r"
          values="53;57;53"
          dur={`${pulseSpeed}ms`}
          repeatCount="indefinite"
        />
      </circle>

      {/* Secondary ambient glow */}
      <ellipse
        cx="50"
        cy="85"
        rx="40"
        ry="15"
        fill={color}
        opacity={intensity * 0.2}
        style={{
          filter: `blur(${blur / 2}px)`,
          transition: 'all 0.5s ease-out'
        }}
      >
        <animate
          attributeName="opacity"
          values={`${intensity * 0.2};${intensity * 0.1};${intensity * 0.2}`}
          dur={`${pulseSpeed * 1.2}ms`}
          repeatCount="indefinite"
        />
      </ellipse>

      {/* State-specific additional effects */}
      {state === 'listening' && (
        <>
          {/* Sound wave indicators */}
          {[0, 1, 2].map((i) => (
            <circle
              key={i}
              cx="50"
              cy="50"
              r="45"
              fill="none"
              stroke={color}
              strokeWidth="1"
              opacity="0"
            >
              <animate
                attributeName="r"
                values="45;65"
                dur="1.5s"
                begin={`${i * 0.5}s`}
                repeatCount="indefinite"
              />
              <animate
                attributeName="opacity"
                values="0.5;0"
                dur="1.5s"
                begin={`${i * 0.5}s`}
                repeatCount="indefinite"
              />
            </circle>
          ))}
        </>
      )}

      {state === 'thinking' && (
        <>
          {/* Rotating dots */}
          <g>
            <animateTransform
              attributeName="transform"
              type="rotate"
              from="0 50 50"
              to="360 50 50"
              dur="3s"
              repeatCount="indefinite"
            />
            {[0, 1, 2].map((i) => (
              <circle
                key={i}
                cx={50 + 35 * Math.cos((i * 2 * Math.PI) / 3)}
                cy={50 + 35 * Math.sin((i * 2 * Math.PI) / 3)}
                r="3"
                fill={color}
                opacity={0.6}
              >
                <animate
                  attributeName="opacity"
                  values="0.3;0.8;0.3"
                  dur="1s"
                  begin={`${i * 0.33}s`}
                  repeatCount="indefinite"
                />
              </circle>
            ))}
          </g>
        </>
      )}

      {state === 'speaking' && (
        <>
          {/* Sound emanation effect */}
          <g opacity="0.4">
            {[0, 1, 2, 3].map((i) => (
              <path
                key={i}
                d={`M ${65 + i * 5} ${50 - 5 - i * 2} Q ${70 + i * 5} 50 ${65 + i * 5} ${50 + 5 + i * 2}`}
                fill="none"
                stroke={color}
                strokeWidth="2"
                strokeLinecap="round"
              >
                <animate
                  attributeName="opacity"
                  values="0;0.6;0"
                  dur="0.8s"
                  begin={`${i * 0.2}s`}
                  repeatCount="indefinite"
                />
              </path>
            ))}
          </g>
        </>
      )}

      {state === 'error' && (
        <>
          {/* Warning pulse */}
          <circle
            cx="50"
            cy="50"
            r="48"
            fill="none"
            stroke={color}
            strokeWidth="3"
            strokeDasharray="10 5"
          >
            <animate
              attributeName="stroke-dashoffset"
              values="0;30"
              dur="1s"
              repeatCount="indefinite"
            />
            <animate
              attributeName="opacity"
              values="0.8;0.3;0.8"
              dur="0.5s"
              repeatCount="indefinite"
            />
          </circle>
        </>
      )}
    </g>
  );
};

export default GlowOverlay;
