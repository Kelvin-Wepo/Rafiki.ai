/**
 * AuthLayout Component
 * Split-screen layout for authentication pages
 * Left: Hero section with branding (40%)
 * Right: Form content (60%)
 */

import type { ReactNode } from 'react';

interface AuthLayoutProps {
  children: ReactNode;
  heroContent?: ReactNode;
}

export function AuthLayout({ children, heroContent }: AuthLayoutProps) {
  return (
    <div className="min-h-screen flex flex-col lg:flex-row">
      {/* Hero Section - Left Side (40%) */}
      <div className="hidden lg:flex lg:w-[40%] relative bg-gradient-to-br from-[#004d00] via-[#006600] to-[#008800] overflow-hidden">
        {/* Waveform overlay pattern */}
        <div className="absolute inset-0 opacity-10">
          <svg className="w-full h-full" viewBox="0 0 400 800" preserveAspectRatio="none">
            <defs>
              <pattern id="wavePattern" x="0" y="0" width="100" height="20" patternUnits="userSpaceOnUse">
                <path d="M0 10 Q25 0, 50 10 T100 10" stroke="white" strokeWidth="1" fill="none"/>
              </pattern>
            </defs>
            <rect width="100%" height="100%" fill="url(#wavePattern)"/>
          </svg>
        </div>
        
        {/* Sound wave visualization */}
        <div className="absolute bottom-0 left-0 right-0 h-40 opacity-20">
          <svg className="w-full h-full" viewBox="0 0 400 100" preserveAspectRatio="none">
            {[...Array(50)].map((_, i) => (
              <rect
                key={i}
                x={i * 8}
                y={50 - Math.random() * 40}
                width="4"
                height={Math.random() * 80 + 10}
                fill="white"
                rx="2"
                className="animate-pulse"
                style={{ animationDelay: `${i * 0.05}s` }}
              />
            ))}
          </svg>
        </div>
        
        {/* Hero content */}
        <div className="relative z-10 flex flex-col justify-center px-12 py-16 w-full">
          {heroContent}
        </div>
        
        {/* Kenya flag accent at bottom */}
        <div className="absolute bottom-0 left-0 right-0 h-3 flex">
          <div className="flex-1 bg-black"></div>
          <div className="w-1 bg-white"></div>
          <div className="flex-1 bg-[#bb0000]"></div>
          <div className="w-1 bg-white"></div>
          <div className="flex-1 bg-[#006600]"></div>
        </div>
      </div>

      {/* Form Section - Right Side (60%) */}
      <div className="flex-1 lg:w-[60%] flex items-center justify-center bg-white relative">
        {/* Mobile: Kenya flag at top */}
        <div className="lg:hidden absolute top-0 left-0 right-0 h-2 flex">
          <div className="flex-1 bg-black"></div>
          <div className="w-0.5 bg-white"></div>
          <div className="flex-1 bg-[#bb0000]"></div>
          <div className="w-0.5 bg-white"></div>
          <div className="flex-1 bg-[#006600]"></div>
        </div>
        
        <div className="w-full max-w-md mx-auto px-6 py-12 lg:py-8">
          {children}
        </div>
      </div>
    </div>
  );
}

export default AuthLayout;
