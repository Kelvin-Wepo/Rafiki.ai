/**
 * Talking Avatar Component
 * Displays an African woman avatar with lip-sync animations
 * Uses CSS animations for basic lip sync and can integrate with SadTalker API
 */

import React, { useState, useEffect, useRef } from 'react';
import { useAccessibility } from '../context/AccessibilityContext';

// Avatar states
const AVATAR_STATES = {
  IDLE: 'idle',
  LISTENING: 'listening',
  SPEAKING: 'speaking',
  THINKING: 'thinking',
};

function TalkingAvatar({ 
  isListening = false, 
  isSpeaking = false, 
  isThinking = false,
  size = 'large' // 'small', 'medium', 'large'
}) {
  const { settings } = useAccessibility();
  const [currentState, setCurrentState] = useState(AVATAR_STATES.IDLE);
  const [mouthOpen, setMouthOpen] = useState(false);
  const animationRef = useRef(null);

  // Determine avatar state
  useEffect(() => {
    if (isSpeaking) {
      setCurrentState(AVATAR_STATES.SPEAKING);
    } else if (isListening) {
      setCurrentState(AVATAR_STATES.LISTENING);
    } else if (isThinking) {
      setCurrentState(AVATAR_STATES.THINKING);
    } else {
      setCurrentState(AVATAR_STATES.IDLE);
    }
  }, [isListening, isSpeaking, isThinking]);

  // Lip sync animation when speaking
  useEffect(() => {
    if (currentState === AVATAR_STATES.SPEAKING) {
      // Simulate lip movement with varying intervals
      const animateMouth = () => {
        setMouthOpen(prev => !prev);
        // Random interval between 80-200ms for natural speech
        const nextInterval = Math.random() * 120 + 80;
        animationRef.current = setTimeout(animateMouth, nextInterval);
      };
      animateMouth();
    } else {
      setMouthOpen(false);
      if (animationRef.current) {
        clearTimeout(animationRef.current);
      }
    }

    return () => {
      if (animationRef.current) {
        clearTimeout(animationRef.current);
      }
    };
  }, [currentState]);

  const getSizeClass = () => {
    switch (size) {
      case 'small': return 'avatar-small';
      case 'medium': return 'avatar-medium';
      case 'large': return 'avatar-large';
      default: return 'avatar-large';
    }
  };

  const getStatusText = () => {
    switch (currentState) {
      case AVATAR_STATES.SPEAKING:
        return settings.language === 'sw' ? 'Habari anazungumza...' : 'Habari is speaking...';
      case AVATAR_STATES.LISTENING:
        return settings.language === 'sw' ? 'Inasikiliza...' : 'Listening...';
      case AVATAR_STATES.THINKING:
        return settings.language === 'sw' ? 'Inafikiria...' : 'Thinking...';
      default:
        return settings.language === 'sw' ? 'Habari' : 'Habari';
    }
  };

  return (
    <div className={`talking-avatar-container ${getSizeClass()}`}>
      {/* Avatar SVG - African Woman */}
      <div className={`avatar-wrapper ${currentState}`}>
        <svg 
          viewBox="0 0 200 200" 
          className="avatar-svg"
          role="img"
          aria-label="Habari, your virtual assistant"
        >
          {/* Background circle */}
          <defs>
            <linearGradient id="bgGradient" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#10B981" />
              <stop offset="100%" stopColor="#059669" />
            </linearGradient>
            <linearGradient id="skinTone" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#8B5A3C" />
              <stop offset="100%" stopColor="#6B4423" />
            </linearGradient>
          </defs>
          
          {/* Background */}
          <circle cx="100" cy="100" r="95" fill="url(#bgGradient)" />
          
          {/* Hair - African braids/locs style */}
          <ellipse cx="100" cy="75" rx="65" ry="55" fill="#1a1a1a" />
          <ellipse cx="100" cy="85" rx="60" ry="50" fill="#1a1a1a" />
          {/* Hair details - braids */}
          <path d="M45 70 Q40 90 35 120" stroke="#2a2a2a" strokeWidth="4" fill="none" />
          <path d="M55 65 Q48 85 42 115" stroke="#2a2a2a" strokeWidth="4" fill="none" />
          <path d="M145 65 Q152 85 158 115" stroke="#2a2a2a" strokeWidth="4" fill="none" />
          <path d="M155 70 Q160 90 165 120" stroke="#2a2a2a" strokeWidth="4" fill="none" />
          
          {/* Face */}
          <ellipse cx="100" cy="105" rx="50" ry="55" fill="url(#skinTone)" />
          
          {/* Ears */}
          <ellipse cx="52" cy="105" rx="8" ry="12" fill="#8B5A3C" />
          <ellipse cx="148" cy="105" rx="8" ry="12" fill="#8B5A3C" />
          {/* Earrings */}
          <circle cx="52" cy="115" r="4" fill="#FFD700" />
          <circle cx="148" cy="115" r="4" fill="#FFD700" />
          
          {/* Eyebrows */}
          <path d="M70 82 Q80 78 90 82" stroke="#1a1a1a" strokeWidth="2.5" fill="none" />
          <path d="M110 82 Q120 78 130 82" stroke="#1a1a1a" strokeWidth="2.5" fill="none" />
          
          {/* Eyes */}
          <ellipse cx="80" cy="95" rx="12" ry="8" fill="white" />
          <ellipse cx="120" cy="95" rx="12" ry="8" fill="white" />
          {/* Irises */}
          <circle cx="80" cy="95" r="5" fill="#3D2314" />
          <circle cx="120" cy="95" r="5" fill="#3D2314" />
          {/* Pupils */}
          <circle cx="80" cy="95" r="2.5" fill="#1a1a1a" />
          <circle cx="120" cy="95" r="2.5" fill="#1a1a1a" />
          {/* Eye highlights */}
          <circle cx="82" cy="93" r="1.5" fill="white" />
          <circle cx="122" cy="93" r="1.5" fill="white" />
          
          {/* Eyelashes */}
          <path d="M68 90 L65 86" stroke="#1a1a1a" strokeWidth="1" />
          <path d="M72 88 L70 84" stroke="#1a1a1a" strokeWidth="1" />
          <path d="M128 88 L130 84" stroke="#1a1a1a" strokeWidth="1" />
          <path d="M132 90 L135 86" stroke="#1a1a1a" strokeWidth="1" />
          
          {/* Nose */}
          <path d="M100 100 Q95 115 92 118 Q100 122 108 118 Q105 115 100 100" 
                fill="#7A4A2A" opacity="0.6" />
          
          {/* Mouth - animated */}
          <g className="mouth-group">
            {mouthOpen ? (
              // Speaking mouth
              <>
                <ellipse cx="100" cy="135" rx="15" ry="10" fill="#8B0000" />
                <ellipse cx="100" cy="132" rx="12" ry="4" fill="white" opacity="0.9" />
                <path d="M88 138 Q100 142 112 138" fill="#CC6666" />
              </>
            ) : (
              // Closed/Smile mouth
              <>
                <path d="M85 132 Q100 142 115 132" stroke="#5C3317" strokeWidth="3" fill="none" />
                <path d="M88 132 Q100 138 112 132" fill="#CC6666" opacity="0.5" />
              </>
            )}
          </g>
          
          {/* Lips highlight */}
          <ellipse cx="100" cy="130" rx="12" ry="2" fill="#B35959" opacity="0.4" />
          
          {/* Cheek highlights */}
          <ellipse cx="65" cy="115" rx="8" ry="5" fill="#D4A574" opacity="0.3" />
          <ellipse cx="135" cy="115" rx="8" ry="5" fill="#D4A574" opacity="0.3" />
          
          {/* Neck */}
          <path d="M80 155 L80 180 L120 180 L120 155" fill="url(#skinTone)" />
          
          {/* Clothing - colorful top */}
          <path d="M60 175 Q100 165 140 175 L150 200 L50 200 Z" fill="#E53E3E" />
          <path d="M75 175 Q100 170 125 175 L120 200 L80 200 Z" fill="#DD6B20" />
          
          {/* Necklace */}
          <path d="M75 160 Q100 170 125 160" stroke="#FFD700" strokeWidth="2" fill="none" />
          <circle cx="100" cy="168" r="4" fill="#FFD700" />
          
          {/* Status indicator ring */}
          <circle 
            cx="100" 
            cy="100" 
            r="95" 
            fill="none" 
            stroke={currentState === AVATAR_STATES.SPEAKING ? '#10B981' : 
                   currentState === AVATAR_STATES.LISTENING ? '#3B82F6' : 
                   currentState === AVATAR_STATES.THINKING ? '#F59E0B' : 'transparent'}
            strokeWidth="4"
            className={`status-ring ${currentState}`}
          />
        </svg>
        
        {/* Animated rings for active states */}
        {(currentState === AVATAR_STATES.SPEAKING || currentState === AVATAR_STATES.LISTENING) && (
          <div className="pulse-rings">
            <span className="ring ring-1" />
            <span className="ring ring-2" />
            <span className="ring ring-3" />
          </div>
        )}
      </div>
      
      {/* Status text */}
      <p className="avatar-status" aria-live="polite">
        {getStatusText()}
      </p>

      <style>{`
        .talking-avatar-container {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: var(--spacing-sm);
        }

        .avatar-small .avatar-wrapper { width: 80px; height: 80px; }
        .avatar-medium .avatar-wrapper { width: 120px; height: 120px; }
        .avatar-large .avatar-wrapper { width: 180px; height: 180px; }

        .avatar-wrapper {
          position: relative;
          border-radius: 50%;
          overflow: visible;
        }

        .avatar-svg {
          width: 100%;
          height: 100%;
          display: block;
        }

        /* Blinking animation */
        .avatar-svg ellipse[cy="95"][rx="12"] {
          animation: blink 4s infinite;
        }

        @keyframes blink {
          0%, 96%, 100% { transform: scaleY(1); }
          98% { transform: scaleY(0.1); }
        }

        /* Status ring animations */
        .status-ring {
          transform-origin: center;
        }

        .status-ring.speaking {
          animation: pulse-ring 1.5s infinite;
        }

        .status-ring.listening {
          animation: pulse-ring 2s infinite;
        }

        .status-ring.thinking {
          animation: rotate-ring 2s linear infinite;
          stroke-dasharray: 100 200;
        }

        @keyframes pulse-ring {
          0%, 100% { opacity: 1; stroke-width: 4; }
          50% { opacity: 0.5; stroke-width: 6; }
        }

        @keyframes rotate-ring {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }

        /* Pulse rings */
        .pulse-rings {
          position: absolute;
          top: 50%;
          left: 50%;
          transform: translate(-50%, -50%);
          pointer-events: none;
        }

        .ring {
          position: absolute;
          top: 50%;
          left: 50%;
          transform: translate(-50%, -50%);
          border-radius: 50%;
          border: 2px solid currentColor;
          opacity: 0;
          animation: expand-ring 2s infinite;
        }

        .speaking .ring { color: #10B981; }
        .listening .ring { color: #3B82F6; }

        .ring-1 { animation-delay: 0s; }
        .ring-2 { animation-delay: 0.5s; }
        .ring-3 { animation-delay: 1s; }

        .avatar-small .ring { width: 100px; height: 100px; }
        .avatar-medium .ring { width: 150px; height: 150px; }
        .avatar-large .ring { width: 220px; height: 220px; }

        @keyframes expand-ring {
          0% {
            opacity: 0.6;
            transform: translate(-50%, -50%) scale(0.8);
          }
          100% {
            opacity: 0;
            transform: translate(-50%, -50%) scale(1.3);
          }
        }

        /* Mouth animation enhancement */
        .mouth-group {
          transition: all 0.05s ease;
        }

        .avatar-status {
          font-size: var(--font-size-base);
          font-weight: 600;
          color: var(--color-text-primary);
          margin: 0;
          text-align: center;
        }

        /* Reduced motion */
        @media (prefers-reduced-motion: reduce) {
          .status-ring,
          .ring,
          .avatar-svg ellipse {
            animation: none;
          }
        }

        /* High contrast mode */
        [data-high-contrast="true"] .avatar-wrapper {
          border: 3px solid var(--color-text-primary);
        }
      `}</style>
    </div>
  );
}

export default TalkingAvatar;
