/**
 * Jewelry Component
 * Professional earrings and accessories
 */

import React, { useMemo } from 'react';

interface JewelryProps {
  headTilt?: number;
  headNod?: number;
  style?: 'gold-studs' | 'pearl-drops' | 'hoops' | 'none';
}

const Jewelry: React.FC<JewelryProps> = ({
  headTilt = 0,
  headNod = 0,
  style = 'gold-studs'
}) => {
  // Calculate earring swing based on head movement
  const earringSwing = useMemo(() => ({
    leftRotation: headTilt * 5 + headNod * 2,
    rightRotation: headTilt * 5 - headNod * 2,
    leftTranslate: { x: headTilt * 0.5, y: headNod * 0.3 },
    rightTranslate: { x: -headTilt * 0.5, y: headNod * 0.3 }
  }), [headTilt, headNod]);

  if (style === 'none') return null;

  return (
    <g className="rafiki-jewelry">
      <defs>
        {/* Gold gradient */}
        <linearGradient id="gold-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#FFD700" />
          <stop offset="30%" stopColor="#FFC200" />
          <stop offset="50%" stopColor="#FFE55C" />
          <stop offset="70%" stopColor="#FFC200" />
          <stop offset="100%" stopColor="#B8860B" />
        </linearGradient>

        {/* Pearl gradient */}
        <radialGradient id="pearl-gradient" cx="30%" cy="30%" r="70%">
          <stop offset="0%" stopColor="#FFFFFF" />
          <stop offset="50%" stopColor="#F5F5F5" />
          <stop offset="100%" stopColor="#D4D4D4" />
        </radialGradient>

        {/* Pearl shine */}
        <radialGradient id="pearl-shine" cx="35%" cy="25%" r="30%">
          <stop offset="0%" stopColor="rgba(255, 255, 255, 0.9)" />
          <stop offset="100%" stopColor="rgba(255, 255, 255, 0)" />
        </radialGradient>

        {/* Gold shine */}
        <radialGradient id="gold-shine" cx="30%" cy="30%" r="50%">
          <stop offset="0%" stopColor="rgba(255, 255, 200, 0.8)" />
          <stop offset="100%" stopColor="rgba(255, 200, 0, 0)" />
        </radialGradient>

        {/* Shadow filter */}
        <filter id="earring-shadow" x="-50%" y="-50%" width="200%" height="200%">
          <feDropShadow dx="0.5" dy="1" stdDeviation="0.5" floodColor="rgba(0,0,0,0.3)" />
        </filter>
      </defs>

      {/* Gold Studs */}
      {style === 'gold-studs' && (
        <>
          {/* Left earring */}
          <g
            className="earring-left"
            style={{
              transform: `translate(${earringSwing.leftTranslate.x}px, ${earringSwing.leftTranslate.y}px)`,
              transition: 'transform 0.2s ease-out'
            }}
          >
            <circle
              cx="14"
              cy="55"
              r="2.5"
              fill="url(#gold-gradient)"
              filter="url(#earring-shadow)"
            />
            <circle
              cx="13.5"
              cy="54.5"
              r="1"
              fill="url(#gold-shine)"
            />
          </g>

          {/* Right earring */}
          <g
            className="earring-right"
            style={{
              transform: `translate(${earringSwing.rightTranslate.x}px, ${earringSwing.rightTranslate.y}px)`,
              transition: 'transform 0.2s ease-out'
            }}
          >
            <circle
              cx="86"
              cy="55"
              r="2.5"
              fill="url(#gold-gradient)"
              filter="url(#earring-shadow)"
            />
            <circle
              cx="85.5"
              cy="54.5"
              r="1"
              fill="url(#gold-shine)"
            />
          </g>
        </>
      )}

      {/* Pearl Drop Earrings */}
      {style === 'pearl-drops' && (
        <>
          {/* Left earring */}
          <g
            className="earring-left"
            style={{
              transform: `rotate(${earringSwing.leftRotation}deg)`,
              transformOrigin: '14px 55px',
              transition: 'transform 0.3s ease-out'
            }}
          >
            {/* Gold stud base */}
            <circle
              cx="14"
              cy="55"
              r="1.5"
              fill="url(#gold-gradient)"
            />
            {/* Gold chain */}
            <line
              x1="14"
              y1="56.5"
              x2="14"
              y2="62"
              stroke="url(#gold-gradient)"
              strokeWidth="0.5"
            />
            {/* Pearl */}
            <circle
              cx="14"
              cy="64"
              r="3"
              fill="url(#pearl-gradient)"
              filter="url(#earring-shadow)"
            />
            <circle
              cx="13"
              cy="63"
              r="1.2"
              fill="url(#pearl-shine)"
            />
          </g>

          {/* Right earring */}
          <g
            className="earring-right"
            style={{
              transform: `rotate(${earringSwing.rightRotation}deg)`,
              transformOrigin: '86px 55px',
              transition: 'transform 0.3s ease-out'
            }}
          >
            {/* Gold stud base */}
            <circle
              cx="86"
              cy="55"
              r="1.5"
              fill="url(#gold-gradient)"
            />
            {/* Gold chain */}
            <line
              x1="86"
              y1="56.5"
              x2="86"
              y2="62"
              stroke="url(#gold-gradient)"
              strokeWidth="0.5"
            />
            {/* Pearl */}
            <circle
              cx="86"
              cy="64"
              r="3"
              fill="url(#pearl-gradient)"
              filter="url(#earring-shadow)"
            />
            <circle
              cx="85"
              cy="63"
              r="1.2"
              fill="url(#pearl-shine)"
            />
          </g>
        </>
      )}

      {/* Hoop Earrings */}
      {style === 'hoops' && (
        <>
          {/* Left hoop */}
          <g
            className="earring-left"
            style={{
              transform: `rotate(${earringSwing.leftRotation * 0.5}deg)`,
              transformOrigin: '14px 55px',
              transition: 'transform 0.25s ease-out'
            }}
          >
            <ellipse
              cx="14"
              cy="60"
              rx="4"
              ry="6"
              fill="none"
              stroke="url(#gold-gradient)"
              strokeWidth="1.5"
              filter="url(#earring-shadow)"
            />
            {/* Hoop highlight */}
            <ellipse
              cx="12"
              cy="58"
              rx="2"
              ry="3"
              fill="none"
              stroke="rgba(255, 255, 200, 0.4)"
              strokeWidth="0.5"
            />
          </g>

          {/* Right hoop */}
          <g
            className="earring-right"
            style={{
              transform: `rotate(${earringSwing.rightRotation * 0.5}deg)`,
              transformOrigin: '86px 55px',
              transition: 'transform 0.25s ease-out'
            }}
          >
            <ellipse
              cx="86"
              cy="60"
              rx="4"
              ry="6"
              fill="none"
              stroke="url(#gold-gradient)"
              strokeWidth="1.5"
              filter="url(#earring-shadow)"
            />
            {/* Hoop highlight */}
            <ellipse
              cx="84"
              cy="58"
              rx="2"
              ry="3"
              fill="none"
              stroke="rgba(255, 255, 200, 0.4)"
              strokeWidth="0.5"
            />
          </g>
        </>
      )}

      {/* Subtle swing animation */}
      <style>
        {`
          @keyframes earring-swing {
            0%, 100% { transform: rotate(0deg); }
            25% { transform: rotate(1deg); }
            75% { transform: rotate(-1deg); }
          }
          
          .earring-left, .earring-right {
            animation: earring-swing 3s ease-in-out infinite;
          }
          
          .earring-right {
            animation-delay: -0.5s;
          }
        `}
      </style>
    </g>
  );
};

export default Jewelry;
