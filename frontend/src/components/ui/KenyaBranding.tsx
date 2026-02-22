/**
 * Kenya Flag Stripe SVG Component
 * Decorative element inspired by Kenya national flag
 */

export function KenyaFlagStripe({ className = '', thin = false }: { className?: string; thin?: boolean }) {
  const height = thin ? 3 : 4;
  
  return (
    <svg
      className={className}
      width="100%"
      height={height}
      viewBox="0 0 100 4"
      preserveAspectRatio="none"
      role="img"
      aria-label="Kenya national colors stripe"
    >
      <rect x="0" y="0" width="25" height="4" fill="#1a1a1a" />
      <rect x="24" y="0" width="2" height="4" fill="#ffffff" />
      <rect x="25" y="0" width="25" height="4" fill="#bb0000" />
      <rect x="49" y="0" width="2" height="4" fill="#ffffff" />
      <rect x="50" y="0" width="25" height="4" fill="#006600" />
      <rect x="74" y="0" width="2" height="4" fill="#ffffff" />
      <rect x="75" y="0" width="25" height="4" fill="#1a1a1a" />
    </svg>
  );
}

/**
 * Kenya Coat of Arms Icon (Simplified)
 * Shield motif for government branding
 */
export function KenyaShieldIcon({ className = '', size = 24 }: { className?: string; size?: number }) {
  return (
    <svg
      className={className}
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      role="img"
      aria-label="Kenya shield emblem"
    >
      {/* Shield outline */}
      <path
        d="M12 2L4 6v6c0 5.25 3.4 9.74 8 11 4.6-1.26 8-5.75 8-11V6l-8-4z"
        fill="var(--ke-black)"
        stroke="var(--ke-gray-300)"
        strokeWidth="0.5"
      />
      {/* Inner shield with colors */}
      <path
        d="M12 4L6 7v5c0 4.2 2.72 7.79 6 8.8V4z"
        fill="var(--ke-red)"
      />
      <path
        d="M12 4v15.8c3.28-1.01 6-4.6 6-8.8V7l-6-3z"
        fill="var(--ke-green)"
      />
      {/* Central spear */}
      <line x1="12" y1="5" x2="12" y2="18" stroke="white" strokeWidth="1" />
      {/* Crossed spears */}
      <line x1="9" y1="9" x2="15" y2="14" stroke="white" strokeWidth="0.75" />
      <line x1="15" y1="9" x2="9" y2="14" stroke="white" strokeWidth="0.75" />
    </svg>
  );
}

export default KenyaFlagStripe;
