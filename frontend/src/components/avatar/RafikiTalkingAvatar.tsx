/**
 * Rafiki Talking Avatar Component
 * Combines static image with animated overlays AND SadTalker video lip-sync
 * 
 * How it works:
 * - Idle/Listening/Thinking: Shows static image with animated overlays
 *   (blinking, breathing, eye tracking, particles, waveform)
 * - Speaking: If SadTalker video available, shows lip-synced video
 *   If not available, falls back to image with animated mouth overlay
 * 
 * Features:
 * - Real image with natural animations
 * - SadTalker integration for realistic lip-sync when speaking
 * - Graceful fallback when backend is unavailable
 * - Smooth transitions between modes
 * - All existing effects (particles, waveform, emotions)
 */

import React, { useMemo, useRef, useCallback, useEffect, useState } from 'react';
import type { AvatarState, Viseme } from '../../types/avatar.types';
import { STATE_CONFIGS } from '../../types/avatar.types';
import { useBlinking } from '../../hooks/useBlinking';
import { useMicroMovements } from '../../hooks/useMicroMovements';
import { useBreathing } from '../../hooks/useBreathing';
import { useEyeTracking } from '../../hooks/useEyeTracking';
import { useEmotions, type Emotion } from '../../hooks/useEmotions';
import rafikiImage from '../../assets/rafiki_avatar.png';
import './RafikiImageAvatar.css';

interface AudioAnalysis {
  amplitude: number;
  frequency: number;
  isSpeaking: boolean;
  viseme: Viseme;
}

interface RafikiTalkingAvatarProps {
  state: AvatarState;
  audioData?: AudioAnalysis;
  size?: number | string;
  className?: string;
  accessible?: boolean;
  showParticles?: boolean;
  showWaveform?: boolean;
  emotion?: Emotion;
  followCursor?: boolean;
  onEmotionChange?: (emotion: Emotion) => void;
  // SadTalker video props
  videoUrl?: string | null;
  audioUrl?: string | null;  // Audio fallback when video not available
  onVideoEnd?: () => void;
}

// Particle component for ambient effects
const Particle: React.FC<{
  index: number;
  state: AvatarState;
  time: number;
}> = ({ index, state, time }) => {
  const config = STATE_CONFIGS[state];
  const angle = (index / 16) * Math.PI * 2;
  const baseRadius = 48;
  
  let x, y, opacity, scale;
  
  switch (state) {
    case 'thinking':
      const orbitSpeed = time * 0.5 + index * 0.4;
      x = 50 + Math.cos(angle + orbitSpeed) * (baseRadius + Math.sin(time * 2) * 5);
      y = 50 + Math.sin(angle + orbitSpeed) * (baseRadius * 0.7);
      opacity = 0.4 + Math.sin(time * 3 + index) * 0.3;
      scale = 0.8 + Math.sin(time * 2 + index) * 0.3;
      break;
    case 'listening':
      const pulsePhase = (time * 2 + index * 0.2) % (Math.PI * 2);
      const pulseRadius = baseRadius * (0.8 + Math.sin(pulsePhase) * 0.3);
      x = 50 + Math.cos(angle) * pulseRadius;
      y = 50 + Math.sin(angle) * pulseRadius;
      opacity = 0.3 + Math.sin(pulsePhase) * 0.4;
      scale = 0.6 + Math.sin(pulsePhase) * 0.4;
      break;
    case 'speaking':
      x = 50 + Math.cos(angle + time * 0.3) * (baseRadius - 5 + Math.sin(time * 4 + index) * 8);
      y = 50 + Math.sin(angle + time * 0.3) * (baseRadius - 5 + Math.sin(time * 4 + index) * 8);
      opacity = 0.5 + Math.sin(time * 5 + index) * 0.3;
      scale = 0.7 + Math.sin(time * 4 + index) * 0.3;
      break;
    case 'error':
      x = 50 + Math.cos(angle) * baseRadius + Math.sin(time * 8 + index) * 3;
      y = 50 + Math.sin(angle) * baseRadius + Math.cos(time * 8 + index) * 3;
      opacity = 0.5 + Math.sin(time * 6) * 0.4;
      scale = 1 + Math.sin(time * 6) * 0.2;
      break;
    default:
      x = 50 + Math.cos(angle + time * 0.1) * baseRadius;
      y = 50 + Math.sin(angle + time * 0.1) * baseRadius;
      opacity = 0.2 + Math.sin(time + index * 0.5) * 0.15;
      scale = 0.5 + Math.sin(time + index) * 0.2;
  }

  return (
    <circle
      cx={x}
      cy={y}
      r={1.5 * scale}
      fill={config.glow.color}
      opacity={opacity}
      style={{ filter: 'blur(0.5px)' }}
    />
  );
};

// Voice waveform bar component
const WaveformBar: React.FC<{
  index: number;
  total: number;
  amplitude: number;
  state: AvatarState;
  isActive: boolean;
}> = ({ index, total, amplitude, state, isActive }) => {
  const config = STATE_CONFIGS[state];
  const angle = (index / total) * Math.PI * 2 - Math.PI / 2;
  const baseRadius = 46;
  
  const barHeight = isActive 
    ? 2 + amplitude * 8 + Math.sin(Date.now() / 100 + index) * 2
    : 2 + Math.sin(Date.now() / 500 + index * 0.3) * 0.5;
  
  const x1 = 50 + Math.cos(angle) * baseRadius;
  const y1 = 50 + Math.sin(angle) * baseRadius;
  const x2 = 50 + Math.cos(angle) * (baseRadius + barHeight);
  const y2 = 50 + Math.sin(angle) * (baseRadius + barHeight);

  return (
    <line
      x1={x1}
      y1={y1}
      x2={x2}
      y2={y2}
      stroke={config.glow.color}
      strokeWidth={1.5}
      strokeLinecap="round"
      opacity={isActive ? 0.6 + amplitude * 0.4 : 0.2}
      style={{ transition: 'opacity 0.1s ease-out' }}
    />
  );
};

const RafikiTalkingAvatar: React.FC<RafikiTalkingAvatarProps> = ({
  state,
  audioData,
  size = 400,
  className = '',
  accessible = true,
  showParticles = true,
  showWaveform = true,
  emotion: externalEmotion,
  followCursor = true,
  onEmotionChange,
  videoUrl,
  audioUrl,
  onVideoEnd
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const audioRef = useRef<HTMLAudioElement>(null);
  const [time, setTime] = useState(0);
  const [isKeyboardFocused, setIsKeyboardFocused] = useState(false);
  const [showVideo, setShowVideo] = useState(false);

  // Animation hooks
  useBlinking({ avatarState: state });
  const microMovement = useMicroMovements({ avatarState: state });
  const { breathing } = useBreathing({ avatarState: state });
  useEyeTracking({ 
    containerRef: containerRef as React.RefObject<HTMLElement>, 
    followCursor,
    avatarState: state 
  });
  const { 
    currentEmotion, 
    setEmotion 
  } = useEmotions({ avatarState: state });

  // Animation loop for particles
  useEffect(() => {
    let animationFrame: number;
    const animate = () => {
      setTime(Date.now() / 1000);
      animationFrame = requestAnimationFrame(animate);
    };
    animationFrame = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(animationFrame);
  }, []);

  // Handle external emotion changes
  useEffect(() => {
    if (externalEmotion && externalEmotion !== currentEmotion) {
      setEmotion(externalEmotion);
    }
  }, [externalEmotion, currentEmotion, setEmotion]);

  // Notify parent of emotion changes
  useEffect(() => {
    if (onEmotionChange) {
      onEmotionChange(currentEmotion);
    }
  }, [currentEmotion, onEmotionChange]);

  // Handle video playback with audio synchronization
  useEffect(() => {
    if (videoUrl && state === 'speaking') {
      setShowVideo(true);
      if (videoRef.current) {
        const video = videoRef.current;
        
        // Set video source
        video.src = videoUrl;
        
        // Ensure audio is enabled
        video.muted = false;
        video.volume = 1.0;
        
        // Load and play video with audio
        video.load();
        
        // Play video when ready, ensuring audio is enabled
        const handleCanPlay = () => {
          video.play().catch(err => {
            console.error('Video playback error:', err);
            // If autoplay fails, try with user interaction
            if (err.name === 'NotAllowedError') {
              console.warn('Autoplay blocked - video will play on user interaction');
            }
          });
        };
        
        const handleLoadedMetadata = () => {
          // Ensure audio is enabled (audioTracks API is deprecated, but we ensure muted is false)
          video.muted = false;
          video.volume = 1.0;
        };
        
        video.addEventListener('canplay', handleCanPlay, { once: true });
        video.addEventListener('loadedmetadata', handleLoadedMetadata, { once: true });
        
        return () => {
          video.removeEventListener('canplay', handleCanPlay);
          video.removeEventListener('loadedmetadata', handleLoadedMetadata);
        };
      }
    } else {
      setShowVideo(false);
      if (videoRef.current) {
        videoRef.current.pause();
        videoRef.current.src = '';
      }
    }
  }, [videoUrl, state]);

  // Handle audio playback (fallback mode - only when video is NOT available)
  useEffect(() => {
    // Only play audio if video is not available
    if (audioUrl && !videoUrl && audioRef.current && state === 'speaking') {
      console.log('Playing audio fallback (video unavailable):', audioUrl);
      audioRef.current.src = audioUrl;
      audioRef.current.volume = 1.0;
      audioRef.current.play().catch(err => {
        console.error('Audio playback error:', err);
      });
    } else if (audioRef.current) {
      // Stop audio if video is available or state changes
      audioRef.current.pause();
      if (videoUrl) {
        // Clear audio source when video is available to prevent conflicts
        audioRef.current.src = '';
      }
    }
  }, [audioUrl, videoUrl, state]);

  // Handle video end
  const handleVideoEnded = useCallback(() => {
    setShowVideo(false);
    if (onVideoEnd) {
      onVideoEnd();
    }
  }, [onVideoEnd]);

  // Combined transformations for image
  const imageTransform = useMemo(() => {
    if (showVideo) return {}; // No transform when showing video
    
    const breathScale = 1 + breathing.chestRise * 0.008;
    const headTilt = microMovement.headTilt * 1.5;
    const headNod = microMovement.headNod * 2 + breathing.headBob * 0.5;
    
    return {
      transform: `
        scale(${breathScale})
        rotate(${headTilt}deg)
        translateY(${headNod}px)
      `,
      transformOrigin: 'center 60%'
    };
  }, [breathing, microMovement, showVideo]);

  // Glow color and config
  const glowConfig = STATE_CONFIGS[state].glow;
  const ariaLabel = STATE_CONFIGS[state].ariaLabel;
  const sizeValue = typeof size === 'number' ? `${size}px` : size;

  // Keyboard handlers
  const handleKeyDown = useCallback((event: React.KeyboardEvent) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
    }
  }, []);

  const handleFocus = useCallback(() => setIsKeyboardFocused(true), []);
  const handleBlur = useCallback(() => setIsKeyboardFocused(false), []);

  // Check if waveform should be active
  const isWaveformActive = state === 'listening' || (state === 'speaking' && (audioData?.isSpeaking ?? false));

  return (
    <div
      ref={containerRef}
      className={`rafiki-image-avatar rafiki-image-avatar--${state} ${isKeyboardFocused ? 'rafiki-image-avatar--focused' : ''} ${className}`}
      style={{ width: sizeValue, height: sizeValue }}
      role={accessible ? 'img' : undefined}
      aria-label={accessible ? ariaLabel : undefined}
      aria-live={accessible ? 'polite' : undefined}
      tabIndex={accessible ? 0 : undefined}
      onKeyDown={accessible ? handleKeyDown : undefined}
      onFocus={accessible ? handleFocus : undefined}
      onBlur={accessible ? handleBlur : undefined}
    >
      {/* Hidden video element for SadTalker output */}
      <video
        ref={videoRef}
        className={`rafiki-talking-avatar__video ${showVideo ? 'rafiki-talking-avatar__video--visible' : ''}`}
        playsInline
        muted={false}
        onEnded={handleVideoEnded}
        onError={(e) => {
          console.error('Video error:', e);
          const video = e.currentTarget;
          if (video.error) {
            console.error('Video error details:', {
              code: video.error.code,
              message: video.error.message
            });
          }
        }}
        onLoadedMetadata={() => {
          // Ensure audio is enabled when metadata loads
          if (videoRef.current) {
            videoRef.current.muted = false;
            videoRef.current.volume = 1.0;
          }
        }}
        style={{
          position: 'absolute',
          width: '88%',
          height: '88%',
          top: '6%',
          left: '6%',
          borderRadius: '50%',
          objectFit: 'cover',
          opacity: showVideo ? 1 : 0,
          transition: 'opacity 0.3s ease-out',
          zIndex: showVideo ? 10 : -1
        }}
      />

      {/* Hidden audio element for fallback mode */}
      <audio
        ref={audioRef}
        onEnded={onVideoEnd}
        style={{ display: 'none' }}
      />

      {/* SVG Overlay Layer */}
      <svg
        viewBox="0 0 100 100"
        preserveAspectRatio="xMidYMid meet"
        className="rafiki-image-avatar__overlay"
      >
        <defs>
          {/* Glow filter */}
          <filter id="avatar-glow" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation={glowConfig.blur / 10} result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
          </filter>

          {/* Circular clip for image */}
          <clipPath id="avatar-circle-clip">
            <circle cx="50" cy="50" r="44" />
          </clipPath>

          {/* Radial gradient for vignette */}
          <radialGradient id="vignette-gradient" cx="50%" cy="50%" r="50%">
            <stop offset="70%" stopColor="transparent" />
            <stop offset="100%" stopColor="rgba(0,0,0,0.3)" />
          </radialGradient>
        </defs>

        {/* Background glow */}
        <circle
          cx="50"
          cy="50"
          r="48"
          fill="none"
          stroke={glowConfig.color}
          strokeWidth="3"
          opacity={glowConfig.intensity * 0.5}
          style={{ filter: `blur(${glowConfig.blur / 5}px)` }}
        >
          <animate
            attributeName="opacity"
            values={`${glowConfig.intensity * 0.3};${glowConfig.intensity * 0.6};${glowConfig.intensity * 0.3}`}
            dur={`${glowConfig.pulseSpeed}ms`}
            repeatCount="indefinite"
          />
        </circle>

        {/* Voice Waveform */}
        {showWaveform && (
          <g className="waveform-layer">
            {Array.from({ length: 32 }).map((_, i) => (
              <WaveformBar
                key={i}
                index={i}
                total={32}
                amplitude={audioData?.amplitude || 0}
                state={state}
                isActive={isWaveformActive}
              />
            ))}
          </g>
        )}

        {/* Particle Effects */}
        {showParticles && (
          <g className="particles-layer">
            {Array.from({ length: 16 }).map((_, i) => (
              <Particle key={i} index={i} state={state} time={time} />
            ))}
          </g>
        )}

        {/* Image container with animations (hidden when video playing) */}
        {!showVideo && (
          <g clipPath="url(#avatar-circle-clip)">
            {/* Pure Rafiki image - no overlays */}
            <image
              href={rafikiImage}
              x="6"
              y="6"
              width="88"
              height="88"
              preserveAspectRatio="xMidYMid slice"
              style={imageTransform}
              className="rafiki-image-avatar__image"
            />
          </g>
        )}

        {/* Outer glow ring */}
        <circle
          cx="50"
          cy="50"
          r="46"
          fill="none"
          stroke={glowConfig.color}
          strokeWidth="1"
          opacity="0.4"
        />

        {/* State indicator ring */}
        <circle
          cx="50"
          cy="50"
          r="44"
          fill="none"
          stroke={glowConfig.color}
          strokeWidth="2"
          opacity="0.6"
          strokeDasharray={state === 'thinking' ? '8 4' : 'none'}
          style={{
            transition: 'all 0.3s ease-out',
            animation: state === 'thinking' ? 'rotate-dash 2s linear infinite' : 'none'
          }}
        />

        {/* Video loading indicator */}
        {state === 'speaking' && videoUrl && !showVideo && (
          <g className="loading-indicator">
            <circle
              cx="50"
              cy="50"
              r="15"
              fill="rgba(0,0,0,0.5)"
            />
            <circle
              cx="50"
              cy="50"
              r="12"
              fill="none"
              stroke={glowConfig.color}
              strokeWidth="2"
              strokeDasharray="20 60"
              style={{ animation: 'rotate-dash 1s linear infinite' }}
            />
          </g>
        )}

        {/* Focus indicator */}
        {isKeyboardFocused && (
          <circle
            cx="50"
            cy="50"
            r="49"
            fill="none"
            stroke="#4169E1"
            strokeWidth="2"
            strokeDasharray="4 2"
          >
            <animate
              attributeName="stroke-dashoffset"
              values="0;12"
              dur="0.5s"
              repeatCount="indefinite"
            />
          </circle>
        )}
      </svg>

      {/* Screen reader announcements */}
      {accessible && (
        <span className="rafiki-image-avatar__sr-only" role="status">
          {ariaLabel}
        </span>
      )}
    </div>
  );
};

export default RafikiTalkingAvatar;
