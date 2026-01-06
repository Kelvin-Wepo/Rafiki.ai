/**
 * Hair Component with Animation
 * Professional African hairstyle with subtle movement
 */

import React, { useMemo } from 'react';
import { RAFIKI_COLORS } from '../../types/avatar.types';

interface HairProps {
  headTilt?: number;
  headNod?: number;
  windEffect?: number;
  style?: 'professional' | 'natural' | 'braided';
}

const Hair: React.FC<HairProps> = ({
  headTilt = 0,
  headNod = 0,
  windEffect = 0,
  style = 'professional'
}) => {
  // Calculate hair movement based on head motion
  const hairMovement = useMemo(() => ({
    leftSway: -headTilt * 2 + windEffect * 3,
    rightSway: -headTilt * 2 - windEffect * 3,
    topBounce: -headNod * 0.5,
    volumeScale: 1 + Math.abs(headNod) * 0.02
  }), [headTilt, headNod, windEffect]);

  // Hair strand animation delays
  const strandDelays = useMemo(() => 
    Array.from({ length: 12 }, (_, i) => i * 0.05),
    []
  );

  return (
    <g className="rafiki-hair">
      <defs>
        {/* Hair gradients */}
        <radialGradient id="hair-gradient-main" cx="50%" cy="30%" r="70%">
          <stop offset="0%" stopColor="#2a2a2a" />
          <stop offset="40%" stopColor="#1a1a1a" />
          <stop offset="100%" stopColor="#0a0a0a" />
        </radialGradient>

        <linearGradient id="hair-highlight" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="rgba(255, 255, 255, 0.15)" />
          <stop offset="50%" stopColor="rgba(255, 255, 255, 0.05)" />
          <stop offset="100%" stopColor="rgba(255, 255, 255, 0)" />
        </linearGradient>

        <radialGradient id="hair-shine" cx="35%" cy="25%" r="30%">
          <stop offset="0%" stopColor="rgba(255, 255, 255, 0.2)" />
          <stop offset="100%" stopColor="rgba(255, 255, 255, 0)" />
        </radialGradient>

        {/* Hair texture filter */}
        <filter id="hair-texture" x="-5%" y="-5%" width="110%" height="110%">
          <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="4" result="noise" />
          <feComposite in="SourceGraphic" in2="noise" operator="in" result="textured" />
          <feBlend in="SourceGraphic" in2="textured" mode="soft-light" />
        </filter>

        {/* Clip path for hair volume */}
        <clipPath id="hair-clip">
          <ellipse cx="50" cy="35" rx="42" ry="35" />
        </clipPath>
      </defs>

      {/* Hair shadow */}
      <ellipse
        cx="50"
        cy="52"
        rx="40"
        ry="8"
        fill="rgba(0, 0, 0, 0.15)"
        style={{ filter: 'blur(3px)' }}
      />

      {/* Main hair mass */}
      <g
        transform={`translate(0, ${hairMovement.topBounce}) scale(${hairMovement.volumeScale})`}
        style={{ transformOrigin: '50px 50px' }}
      >
        {/* Back hair layer */}
        <path
          d={`
            M 8 52 
            Q 5 38 10 22 
            Q 18 5 50 2 
            Q 82 5 90 22 
            Q 95 38 92 52
            Q 88 60 75 58
            Q 50 55 25 58
            Q 12 60 8 52
          `}
          fill="url(#hair-gradient-main)"
          style={{ filter: 'url(#hair-texture)' }}
        />

        {/* Hair volume - top */}
        <path
          d={`
            M 12 48 
            Q 8 35 15 18 
            Q 25 3 50 1 
            Q 75 3 85 18 
            Q 92 35 88 48
            Q 82 38 70 32
            Q 55 25 50 24
            Q 45 25 30 32
            Q 18 38 12 48
          `}
          fill="url(#hair-gradient-main)"
          style={{
            transform: `translateX(${hairMovement.leftSway * 0.3}px)`,
            transition: 'transform 0.3s ease-out'
          }}
        />

        {/* Hair highlights */}
        <ellipse
          cx="35"
          cy="20"
          rx="15"
          ry="10"
          fill="url(#hair-shine)"
          style={{
            transform: `translateX(${hairMovement.leftSway * 0.2}px)`,
            transition: 'transform 0.3s ease-out'
          }}
        />

        {/* Individual hair strands for movement */}
        {style === 'professional' && (
          <g className="hair-strands">
            {/* Left side strands */}
            {[0, 1, 2, 3].map((i) => (
              <path
                key={`left-strand-${i}`}
                d={`M ${15 + i * 3} ${35 + i * 3} Q ${12 + i * 2} ${45 + i * 2} ${14 + i * 3} ${52 + i}`}
                fill="none"
                stroke={RAFIKI_COLORS.primary.black}
                strokeWidth="2"
                opacity={0.6 - i * 0.1}
                style={{
                  transform: `rotate(${hairMovement.leftSway * (0.5 + i * 0.2)}deg)`,
                  transformOrigin: `${15 + i * 3}px ${35 + i * 3}px`,
                  transition: `transform ${0.3 + strandDelays[i]}s ease-out`
                }}
              />
            ))}

            {/* Right side strands */}
            {[0, 1, 2, 3].map((i) => (
              <path
                key={`right-strand-${i}`}
                d={`M ${85 - i * 3} ${35 + i * 3} Q ${88 - i * 2} ${45 + i * 2} ${86 - i * 3} ${52 + i}`}
                fill="none"
                stroke={RAFIKI_COLORS.primary.black}
                strokeWidth="2"
                opacity={0.6 - i * 0.1}
                style={{
                  transform: `rotate(${hairMovement.rightSway * (0.5 + i * 0.2)}deg)`,
                  transformOrigin: `${85 - i * 3}px ${35 + i * 3}px`,
                  transition: `transform ${0.3 + strandDelays[i]}s ease-out`
                }}
              />
            ))}
          </g>
        )}

        {/* Braided style elements */}
        {style === 'braided' && (
          <g className="hair-braids">
            {/* Cornrow patterns */}
            {[0, 1, 2, 3, 4].map((i) => (
              <path
                key={`braid-${i}`}
                d={`M ${25 + i * 12} 10 Q ${26 + i * 12} 25 ${25 + i * 12} 40`}
                fill="none"
                stroke="rgba(0, 0, 0, 0.3)"
                strokeWidth="3"
                strokeLinecap="round"
              />
            ))}
          </g>
        )}

        {/* Hair edge/baby hairs */}
        <g className="hair-edges" opacity="0.4">
          <path
            d="M 22 32 Q 25 30 28 31"
            fill="none"
            stroke={RAFIKI_COLORS.primary.black}
            strokeWidth="1"
          />
          <path
            d="M 72 31 Q 75 30 78 32"
            fill="none"
            stroke={RAFIKI_COLORS.primary.black}
            strokeWidth="1"
          />
        </g>

        {/* Hair part line */}
        <path
          d="M 50 5 Q 51 15 50 25"
          fill="none"
          stroke="rgba(60, 40, 30, 0.2)"
          strokeWidth="0.5"
        />
      </g>

      {/* Ambient hair movement animation */}
      <style>
        {`
          @keyframes hair-sway {
            0%, 100% { transform: translateX(0) rotate(0deg); }
            25% { transform: translateX(0.5px) rotate(0.2deg); }
            75% { transform: translateX(-0.5px) rotate(-0.2deg); }
          }
          
          .hair-strands path {
            animation: hair-sway 4s ease-in-out infinite;
          }
          
          .hair-strands path:nth-child(odd) {
            animation-delay: -1s;
          }
        `}
      </style>
    </g>
  );
};

export default Hair;
