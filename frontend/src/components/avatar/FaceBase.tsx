/**
 * Face Base Component
 * African woman face structure with realistic skin textures
 */

import React, { useMemo } from 'react';
import { RAFIKI_COLORS } from '../../types/avatar.types';

interface FaceBaseProps {
  headTilt?: number;
  headNod?: number;
  browRaise?: number;
  browFurrow?: number;
  browTilt?: number;
  cheekRaise?: number;
}

const FaceBase: React.FC<FaceBaseProps> = ({
  headTilt = 0,
  headNod = 0,
  browRaise = 0,
  browFurrow = 0,
  browTilt = 0,
  cheekRaise = 0
}) => {
  // Transform for micro-movements
  const transform = `rotate(${headTilt * 3} 50 50) translate(0, ${headNod * 2})`;

  // Calculate eyebrow transforms based on expressions
  const leftBrowTransform = useMemo(() => {
    const raise = -browRaise * 3;
    const tilt = browTilt * 2;
    const furrow = browFurrow * 1;
    return `translate(${furrow}, ${raise}) rotate(${tilt} 35 34)`;
  }, [browRaise, browTilt, browFurrow]);

  const rightBrowTransform = useMemo(() => {
    const raise = -browRaise * 3;
    const tilt = -browTilt * 2;
    const furrow = -browFurrow * 1;
    return `translate(${furrow}, ${raise}) rotate(${tilt} 65 34)`;
  }, [browRaise, browTilt, browFurrow]);

  // Cheek raise affects cheek highlight intensity
  const cheekHighlightOpacity = useMemo(() => {
    return 0.2 + cheekRaise * 0.3;
  }, [cheekRaise]);

  return (
    <g className="rafiki-face-base" transform={transform}>
      <defs>
        {/* Skin gradient - realistic African skin tone */}
        <radialGradient id="skin-gradient" cx="50%" cy="40%" r="60%">
          <stop offset="0%" stopColor={RAFIKI_COLORS.skin.highlight} />
          <stop offset="50%" stopColor={RAFIKI_COLORS.skin.base} />
          <stop offset="100%" stopColor={RAFIKI_COLORS.skin.shadow} />
        </radialGradient>

        {/* Forehead highlight */}
        <radialGradient id="forehead-highlight" cx="50%" cy="20%" r="40%">
          <stop offset="0%" stopColor="rgba(255, 255, 255, 0.15)" />
          <stop offset="100%" stopColor="rgba(255, 255, 255, 0)" />
        </radialGradient>

        {/* Cheek highlight */}
        <radialGradient id="cheek-highlight-left" cx="30%" cy="55%" r="25%">
          <stop offset="0%" stopColor="rgba(255, 200, 180, 0.2)" />
          <stop offset="100%" stopColor="rgba(255, 200, 180, 0)" />
        </radialGradient>
        <radialGradient id="cheek-highlight-right" cx="70%" cy="55%" r="25%">
          <stop offset="0%" stopColor="rgba(255, 200, 180, 0.2)" />
          <stop offset="100%" stopColor="rgba(255, 200, 180, 0)" />
        </radialGradient>

        {/* Shadow filter */}
        <filter id="face-shadow" x="-10%" y="-10%" width="120%" height="120%">
          <feDropShadow dx="0" dy="2" stdDeviation="3" floodColor="rgba(0,0,0,0.3)" />
        </filter>

        {/* Skin texture filter */}
        <filter id="skin-texture">
          <feTurbulence type="fractalNoise" baseFrequency="0.8" numOctaves="4" result="noise" />
          <feDiffuseLighting in="noise" lightingColor="white" surfaceScale="1" result="light">
            <feDistantLight azimuth="45" elevation="60" />
          </feDiffuseLighting>
          <feBlend in="SourceGraphic" in2="light" mode="multiply" />
        </filter>
      </defs>

      {/* Head shadow */}
      <ellipse
        cx="50"
        cy="92"
        rx="35"
        ry="8"
        fill="rgba(0, 0, 0, 0.2)"
        style={{ filter: 'blur(4px)' }}
      />

      {/* Neck */}
      <path
        d="M 38 85 L 40 98 Q 50 100 60 98 L 62 85"
        fill={RAFIKI_COLORS.skin.shadow}
      />

      {/* Face shape - oval with African features */}
      <ellipse
        cx="50"
        cy="50"
        rx="38"
        ry="45"
        fill="url(#skin-gradient)"
        filter="url(#face-shadow)"
      />

      {/* Face contour overlay */}
      <ellipse
        cx="50"
        cy="50"
        rx="38"
        ry="45"
        fill="url(#forehead-highlight)"
      />

      {/* Cheekbone highlights */}
      <ellipse
        cx="28"
        cy="55"
        rx="12"
        ry="10"
        fill="url(#cheek-highlight-left)"
        opacity={cheekHighlightOpacity}
        style={{ transition: 'opacity 0.3s ease-out' }}
      />
      <ellipse
        cx="72"
        cy="55"
        rx="12"
        ry="10"
        fill="url(#cheek-highlight-right)"
        opacity={cheekHighlightOpacity}
        style={{ transition: 'opacity 0.3s ease-out' }}
      />

      {/* Nose */}
      <g className="rafiki-nose">
        {/* Nose bridge shadow */}
        <path
          d="M 48 40 Q 50 55 48 60"
          fill="none"
          stroke="rgba(0, 0, 0, 0.1)"
          strokeWidth="2"
        />
        {/* Nose tip */}
        <ellipse
          cx="50"
          cy="62"
          rx="8"
          ry="5"
          fill={RAFIKI_COLORS.skin.base}
        />
        {/* Nose highlight */}
        <ellipse
          cx="50"
          cy="60"
          rx="4"
          ry="2"
          fill="rgba(255, 255, 255, 0.15)"
        />
        {/* Nostrils */}
        <ellipse
          cx="45"
          cy="64"
          rx="3"
          ry="2"
          fill={RAFIKI_COLORS.skin.shadow}
          opacity="0.5"
        />
        <ellipse
          cx="55"
          cy="64"
          rx="3"
          ry="2"
          fill={RAFIKI_COLORS.skin.shadow}
          opacity="0.5"
        />
      </g>

      {/* Eyebrows with expression support */}
      <g className="rafiki-eyebrows">
        {/* Left eyebrow */}
        <path
          d="M 22 35 Q 35 32 45 36"
          fill="none"
          stroke={RAFIKI_COLORS.primary.black}
          strokeWidth="2.5"
          strokeLinecap="round"
          opacity="0.8"
          transform={leftBrowTransform}
          style={{ transition: 'transform 0.2s ease-out' }}
        />
        {/* Right eyebrow */}
        <path
          d="M 78 35 Q 65 32 55 36"
          fill="none"
          stroke={RAFIKI_COLORS.primary.black}
          strokeWidth="2.5"
          strokeLinecap="round"
          opacity="0.8"
          transform={rightBrowTransform}
          style={{ transition: 'transform 0.2s ease-out' }}
        />
        
        {/* Furrow lines between eyebrows (visible when furrowing) */}
        {browFurrow > 0.3 && (
          <g opacity={browFurrow * 0.5} style={{ transition: 'opacity 0.3s ease-out' }}>
            <path
              d="M 48 33 Q 47 36 48 39"
              fill="none"
              stroke={RAFIKI_COLORS.skin.shadow}
              strokeWidth="0.5"
            />
            <path
              d="M 52 33 Q 53 36 52 39"
              fill="none"
              stroke={RAFIKI_COLORS.skin.shadow}
              strokeWidth="0.5"
            />
          </g>
        )}
      </g>

      {/* Hair - Professional African hairstyle */}
      <g className="rafiki-hair">
        <defs>
          <radialGradient id="hair-gradient" cx="50%" cy="30%" r="70%">
            <stop offset="0%" stopColor="#1a1a1a" />
            <stop offset="100%" stopColor="#000000" />
          </radialGradient>
        </defs>
        
        {/* Main hair mass */}
        <path
          d="M 12 50 
             Q 8 35 15 20 
             Q 25 5 50 3 
             Q 75 5 85 20 
             Q 92 35 88 50
             Q 85 40 75 35
             Q 65 25 50 23
             Q 35 25 25 35
             Q 15 40 12 50"
          fill="url(#hair-gradient)"
        />
        
        {/* Hair texture/detail lines */}
        <g stroke="#2a2a2a" strokeWidth="0.5" fill="none" opacity="0.5">
          <path d="M 20 35 Q 35 15 50 12" />
          <path d="M 80 35 Q 65 15 50 12" />
          <path d="M 25 42 Q 37 22 50 18" />
          <path d="M 75 42 Q 63 22 50 18" />
        </g>

        {/* Hair shine */}
        <path
          d="M 30 25 Q 50 15 70 25"
          fill="none"
          stroke="rgba(255, 255, 255, 0.1)"
          strokeWidth="3"
          strokeLinecap="round"
        />
      </g>

      {/* Ears */}
      <g className="rafiki-ears">
        {/* Left ear */}
        <ellipse
          cx="12"
          cy="50"
          rx="4"
          ry="8"
          fill={RAFIKI_COLORS.skin.base}
        />
        <ellipse
          cx="12"
          cy="50"
          rx="2"
          ry="5"
          fill={RAFIKI_COLORS.skin.shadow}
          opacity="0.3"
        />
        {/* Earring hint */}
        <circle
          cx="12"
          cy="56"
          r="1.5"
          fill={RAFIKI_COLORS.accent.gold}
          opacity="0.8"
        />

        {/* Right ear */}
        <ellipse
          cx="88"
          cy="50"
          rx="4"
          ry="8"
          fill={RAFIKI_COLORS.skin.base}
        />
        <ellipse
          cx="88"
          cy="50"
          rx="2"
          ry="5"
          fill={RAFIKI_COLORS.skin.shadow}
          opacity="0.3"
        />
        {/* Earring hint */}
        <circle
          cx="88"
          cy="56"
          r="1.5"
          fill={RAFIKI_COLORS.accent.gold}
          opacity="0.8"
        />
      </g>

      {/* Subtle jaw line definition */}
      <path
        d="M 15 55 Q 25 80 50 88 Q 75 80 85 55"
        fill="none"
        stroke={RAFIKI_COLORS.skin.shadow}
        strokeWidth="0.5"
        opacity="0.3"
      />

      {/* Chin highlight */}
      <ellipse
        cx="50"
        cy="82"
        rx="8"
        ry="4"
        fill="rgba(255, 255, 255, 0.08)"
      />
    </g>
  );
};

export default FaceBase;
