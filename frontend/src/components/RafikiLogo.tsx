/**
 * RafikiLogo
 */

import { useId } from 'react';

// Kenya flag palette
const BLACK = '#161616';
const RED = '#C8102E';
const GREEN = '#007A33';

const LETTERS: Array<[string, string]> = [
  ['r', BLACK],
  ['a', RED],
  ['f', BLACK],
  ['i', GREEN],
  ['k', RED],
  ['i', BLACK],
];

interface RafikiLogoProps {
  /** Wordmark text height in px (arc scales with it) */
  size?: number;
  /** Show the "AI Government Assistant" tagline under the wordmark */
  showTagline?: boolean;
  className?: string;
}

export function RafikiLogo({ size = 40, showTagline = false, className = '' }: RafikiLogoProps) {
  const gradientId = useId();

  return (
    <span
      role="img"
      aria-label="Rafiki — AI Government Assistant"
      className={className}
      style={{
        display: 'inline-flex',
        flexDirection: 'column',
        alignItems: 'center',
        lineHeight: 1,
      }}
    >
      {/* Flag-coloured arc */}
      <svg
        viewBox="0 0 100 20"
        aria-hidden="true"
        style={{ width: size * 2.1, height: size * 0.42, display: 'block' }}
      >
        <defs>
          <linearGradient id={gradientId} x1="0" y1="0" x2="1" y2="0">
            <stop offset="0" stopColor={BLACK} />
            <stop offset="0.36" stopColor={BLACK} />
            <stop offset="0.40" stopColor={RED} />
            <stop offset="0.60" stopColor={RED} />
            <stop offset="0.64" stopColor={GREEN} />
            <stop offset="1" stopColor={GREEN} />
          </linearGradient>
        </defs>
        <path
          d="M5 17 Q50 -9 95 17"
          fill="none"
          stroke={`url(#${gradientId})`}
          strokeWidth="5.5"
          strokeLinecap="round"
        />
      </svg>

      {/* Wordmark */}
      <span
        style={{
          fontFamily: "'Baloo 2', 'DM Sans', system-ui, sans-serif",
          fontWeight: 700,
          fontSize: size,
          letterSpacing: '-0.02em',
          marginTop: -size * 0.08,
        }}
      >
        {LETTERS.map(([letter, color], i) => (
          <span key={i} style={{ color }}>
            {letter}
          </span>
        ))}
      </span>

      {showTagline && (
        <span
          style={{
            fontFamily: "'DM Sans', system-ui, sans-serif",
            fontSize: Math.max(size * 0.26, 10),
            color: '#6B7280',
            marginTop: size * 0.14,
            whiteSpace: 'nowrap',
          }}
        >
          AI Government Assistant
        </span>
      )}
    </span>
  );
}

export default RafikiLogo;
