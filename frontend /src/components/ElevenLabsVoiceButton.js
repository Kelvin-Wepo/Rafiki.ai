/**
 * ElevenLabs Voice Button Component
 * Voice conversation button using ElevenLabs Conversational AI
 */

import React, { useState, useEffect, useCallback } from 'react';
import { useAccessibility } from '../context/AccessibilityContext';
import elevenLabsService from '../services/elevenLabsService';
import toast from 'react-hot-toast';

function ElevenLabsVoiceButton({ disabled = false }) {
  const [isActive, setIsActive] = useState(false);
  const [status, setStatus] = useState('idle'); // idle, connecting, listening, speaking
  const { settings, announce } = useAccessibility();

  // Setup ElevenLabs callbacks
  useEffect(() => {
    elevenLabsService.onConnect = () => {
      setIsActive(true);
      setStatus('listening');
      announce('Connected to Habari. You can start speaking now.');
      toast.success('Connected! Start speaking...');
    };

    elevenLabsService.onDisconnect = () => {
      setIsActive(false);
      setStatus('idle');
      announce('Conversation ended.');
    };

    elevenLabsService.onModeChange = (mode) => {
      setStatus(mode);
      if (mode === 'speaking') {
        announce('Habari is speaking...');
      } else if (mode === 'listening') {
        announce('Listening...');
      }
    };

    elevenLabsService.onError = (error) => {
      setIsActive(false);
      setStatus('idle');
      toast.error(`Error: ${error}`);
      announce(`Error: ${error}`);
    };

    // Cleanup on unmount
    return () => {
      if (elevenLabsService.isActive()) {
        elevenLabsService.endConversation();
      }
    };
  }, [announce]);

  const toggleConversation = useCallback(async () => {
    if (isActive) {
      // End conversation
      await elevenLabsService.endConversation();
      setIsActive(false);
      setStatus('idle');
      announce('Conversation ended.');
      toast.success('Conversation ended');
    } else {
      // Start conversation
      setStatus('connecting');
      announce('Connecting to Habari...');
      
      const success = await elevenLabsService.startConversation();
      if (!success) {
        setStatus('idle');
        toast.error('Failed to connect. Please check your microphone.');
      }
    }
  }, [isActive, announce]);

  const getStatusText = () => {
    switch (status) {
      case 'connecting':
        return settings.language === 'sw' ? 'Inaunganisha...' : 'Connecting...';
      case 'listening':
        return settings.language === 'sw' ? 'Inasikiliza...' : 'Listening...';
      case 'speaking':
        return settings.language === 'sw' ? 'Habari anazungumza...' : 'Habari is speaking...';
      default:
        return settings.language === 'sw' 
          ? 'Bonyeza kuongea na Habari' 
          : 'Tap to talk to Habari';
    }
  };

  const getButtonClass = () => {
    let className = 'elevenlabs-voice-button';
    if (isActive) className += ' active';
    if (status === 'speaking') className += ' speaking';
    if (status === 'listening') className += ' listening';
    if (status === 'connecting') className += ' connecting';
    return className;
  };

  return (
    <div className="elevenlabs-voice-container">
      <button
        className={getButtonClass()}
        onClick={toggleConversation}
        disabled={disabled || status === 'connecting'}
        aria-label={isActive ? 'End conversation with Habari' : 'Start conversation with Habari'}
        aria-pressed={isActive}
      >
        <div className="voice-button-inner">
          {/* Microphone Icon */}
          <svg
            className="voice-icon"
            width="48"
            height="48"
            viewBox="0 0 24 24"
            fill="currentColor"
            aria-hidden="true"
          >
            {isActive ? (
              // Stop icon when active
              <path d="M6 6h12v12H6z" />
            ) : (
              // Microphone icon when inactive
              <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3zm-1-9c0-.55.45-1 1-1s1 .45 1 1v6c0 .55-.45 1-1 1s-1-.45-1-1V5zm6 6c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z" />
            )}
          </svg>

          {/* Pulse animation rings */}
          {isActive && (
            <>
              <span className="pulse-ring pulse-ring-1" aria-hidden="true" />
              <span className="pulse-ring pulse-ring-2" aria-hidden="true" />
              <span className="pulse-ring pulse-ring-3" aria-hidden="true" />
            </>
          )}
        </div>
      </button>

      {/* Status text */}
      <p className="voice-status-text" aria-live="polite">
        {getStatusText()}
      </p>

      {/* Instructions */}
      {!isActive && (
        <p className="voice-instructions">
          {settings.language === 'sw' 
            ? 'Bonyeza kitufe hapo juu kuanza mazungumzo ya sauti na Habari'
            : 'Press the button above to start a voice conversation with Habari'}
        </p>
      )}

      <style>{`
        .elevenlabs-voice-container {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: var(--spacing-md);
          padding: var(--spacing-xl);
        }

        .elevenlabs-voice-button {
          position: relative;
          width: 120px;
          height: 120px;
          border-radius: 50%;
          border: none;
          background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-primary-dark) 100%);
          color: white;
          cursor: pointer;
          transition: all 0.3s ease;
          box-shadow: 0 8px 32px rgba(0, 59, 74, 0.3);
        }

        .elevenlabs-voice-button:hover:not(:disabled) {
          transform: scale(1.05);
          box-shadow: 0 12px 40px rgba(0, 59, 74, 0.4);
        }

        .elevenlabs-voice-button:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }

        .elevenlabs-voice-button.active {
          background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
          box-shadow: 0 8px 32px rgba(239, 68, 68, 0.4);
        }

        .elevenlabs-voice-button.listening {
          animation: pulse-glow 2s infinite;
        }

        .elevenlabs-voice-button.speaking {
          background: linear-gradient(135deg, #10b981 0%, #059669 100%);
          box-shadow: 0 8px 32px rgba(16, 185, 129, 0.4);
        }

        .elevenlabs-voice-button.connecting {
          background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
          animation: connecting-pulse 1.5s infinite;
        }

        @keyframes pulse-glow {
          0%, 100% {
            box-shadow: 0 8px 32px rgba(239, 68, 68, 0.4);
          }
          50% {
            box-shadow: 0 8px 48px rgba(239, 68, 68, 0.6);
          }
        }

        @keyframes connecting-pulse {
          0%, 100% {
            opacity: 1;
          }
          50% {
            opacity: 0.7;
          }
        }

        .voice-button-inner {
          display: flex;
          align-items: center;
          justify-content: center;
          width: 100%;
          height: 100%;
        }

        .voice-icon {
          z-index: 1;
        }

        .pulse-ring {
          position: absolute;
          top: 50%;
          left: 50%;
          transform: translate(-50%, -50%);
          border-radius: 50%;
          border: 2px solid currentColor;
          opacity: 0;
          animation: pulse-ring 2s infinite;
        }

        .pulse-ring-1 {
          width: 140px;
          height: 140px;
          animation-delay: 0s;
        }

        .pulse-ring-2 {
          width: 160px;
          height: 160px;
          animation-delay: 0.5s;
        }

        .pulse-ring-3 {
          width: 180px;
          height: 180px;
          animation-delay: 1s;
        }

        @keyframes pulse-ring {
          0% {
            opacity: 0.6;
            transform: translate(-50%, -50%) scale(0.8);
          }
          100% {
            opacity: 0;
            transform: translate(-50%, -50%) scale(1.2);
          }
        }

        .voice-status-text {
          font-size: var(--font-size-lg);
          font-weight: 600;
          color: var(--color-text-primary);
          text-align: center;
          min-height: 1.5em;
        }

        .voice-instructions {
          font-size: var(--font-size-base);
          color: var(--color-text-secondary);
          text-align: center;
          max-width: 300px;
        }

        /* High contrast mode */
        [data-high-contrast="true"] .elevenlabs-voice-button {
          border: 3px solid white;
        }

        /* Reduced motion */
        @media (prefers-reduced-motion: reduce) {
          .elevenlabs-voice-button,
          .pulse-ring {
            animation: none;
          }
        }
      `}</style>
    </div>
  );
}

export default ElevenLabsVoiceButton;
