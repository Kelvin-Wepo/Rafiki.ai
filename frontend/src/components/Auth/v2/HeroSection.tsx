/**
 * HeroSection Component - IMPROVED
 * Right side hero with Kenyan woman actively using voice on phone
 * Reduced gradient opacity, repositioned waveform, better text contrast
 * 
 * Fixes: 45% max gradient, waveform at bottom, text shadows for contrast
 */

import { Mic } from 'lucide-react';

interface HeroSectionProps {
  isMobile?: boolean;
}

export function HeroSection({ isMobile = false }: HeroSectionProps) {
  return (
    <div className={`relative w-full h-full ${isMobile ? '' : 'min-h-screen'} overflow-hidden`}>
      {/* Hero Image - Kenyan woman actively using voice assistant */}
      <img
        src="https://images.unsplash.com/photo-1589156191108-c762ff4b96ab?ixlib=rb-4.0.3&auto=format&fit=crop&w=1920&q=80"
        alt="Kenyan woman using voice assistant on smartphone"
        className="absolute inset-0 w-full h-full object-cover"
        style={{ objectPosition: isMobile ? 'center 20%' : 'center center' }}
      />

      {/* Green Gradient Overlay - Left edge only, max 45% */}
      <div 
        className="absolute inset-0 bg-gradient-to-r from-green-900/45 via-green-900/15 to-transparent"
        style={{
          background: isMobile 
            ? 'linear-gradient(to bottom, rgba(20, 83, 45, 0.55) 0%, rgba(20, 83, 45, 0.25) 50%, transparent 100%)'
            : undefined
        }}
      />

      {/* Animated Waveform - Bottom center, very subtle, doesn't cover face */}
      {!isMobile && (
        <div 
          className="absolute bottom-32 left-1/2 -translate-x-1/2 opacity-20 pointer-events-none"
          style={{ width: '280px', height: '50px' }}
        >
          <svg 
            viewBox="0 0 280 50" 
            className="w-full h-full"
            preserveAspectRatio="xMidYMid meet"
          >
            {[...Array(28)].map((_, i) => {
              const height = Math.sin(i * 0.5) * 15 + 20;
              return (
                <rect
                  key={i}
                  x={i * 10}
                  y={(50 - height) / 2}
                  width="4"
                  height={height}
                  fill="white"
                  rx="2"
                  className="animate-pulse"
                  style={{ 
                    animationDelay: `${i * 0.05}s`,
                    animationDuration: '1.4s'
                  }}
                />
              );
            })}
          </svg>
        </div>
      )}

      {/* Bottom overlay text - Safe area positioning */}
      {!isMobile && (
        <div className="absolute bottom-10 right-10 text-right max-w-md">
          {/* Mic Button */}
          <div className="flex items-center justify-end mb-4">
            <button
              className="w-12 h-12 bg-white/20 backdrop-blur-sm rounded-full flex items-center justify-center border border-white/25 hover:bg-white/30 transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-white/40"
              aria-label="Voice assistant"
            >
              <Mic className="w-6 h-6 text-white drop-shadow" />
            </button>
          </div>
          
          {/* Quote - Text shadow for readability */}
          <p 
            className="text-white text-xl lg:text-2xl font-semibold italic leading-relaxed drop-shadow-lg"
          >
            "Sema tu… Rafiki atakusaidia."
          </p>
          <p 
            className="text-white/85 text-sm mt-1 drop-shadow"
          >
            Just speak… Rafiki will help you.
          </p>
        </div>
      )}

      {/* Mobile text overlay */}
      {isMobile && (
        <div className="absolute bottom-4 left-4 right-4 text-center">
          <p 
            className="text-white text-lg font-semibold"
            style={{ textShadow: '0 2px 8px rgba(0,0,0,0.5)' }}
          >
            Sema tu… Rafiki atakusaidia
          </p>
        </div>
      )}

      {/* Kenya Flag Stripe at Bottom - Slightly thicker */}
      <div className="absolute bottom-0 left-0 right-0 h-2.5 flex">
        <div className="flex-1 bg-black"></div>
        <div className="w-0.5 bg-white"></div>
        <div className="flex-1 bg-[#BB0000]"></div>
        <div className="w-0.5 bg-white"></div>
        <div className="flex-1 bg-[#006600]"></div>
      </div>
    </div>
  );
}

export default HeroSection;
