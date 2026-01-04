/**
 * Real Talking Avatar Component
 * Displays a realistic Kenyan woman avatar (Rafiki) with:
 * - Real generated portrait image
 * - SadTalker video animation for speaking
 * - Audio sync and lip-sync
 * - Fallback to static image if video unavailable
 */

import React, { useState, useEffect, useRef } from 'react';
import { useAccessibility } from '../context/AccessibilityContext';
import './RealTalkingAvatar.css';

const AVATAR_STATES = {
  IDLE: 'idle',
  LISTENING: 'listening',
  SPEAKING: 'speaking',
  THINKING: 'thinking',
  LOADING: 'loading',
};

function RealTalkingAvatar({ 
  isListening = false, 
  isSpeaking = false, 
  isThinking = false,
  videoUrl = null,
  audioUrl = null,
  size = 'large',
  onVideoEnd = null
}) {
  const { settings } = useAccessibility();
  const [currentState, setCurrentState] = useState(AVATAR_STATES.IDLE);
  const [videoLoading, setVideoLoading] = useState(false);
  const [videoError, setVideoError] = useState(null);
  const videoRef = useRef(null);
  const audioRef = useRef(null);

  // Determine avatar state
  useEffect(() => {
    if (isSpeaking && videoUrl) {
      setCurrentState(AVATAR_STATES.SPEAKING);
      setVideoLoading(true);
    } else if (isListening) {
      setCurrentState(AVATAR_STATES.LISTENING);
    } else if (isThinking) {
      setCurrentState(AVATAR_STATES.THINKING);
    } else {
      setCurrentState(AVATAR_STATES.IDLE);
    }
  }, [isListening, isSpeaking, isThinking, videoUrl]);

  // Auto-play video when it's ready
  useEffect(() => {
    if (currentState === AVATAR_STATES.SPEAKING && videoRef.current && videoUrl) {
      videoRef.current.src = videoUrl;
      videoRef.current.play().catch(err => {
        console.warn('Could not autoplay video:', err);
        setVideoError('Video playback failed');
      });
    }
  }, [currentState, videoUrl]);

  // Sync audio with video
  useEffect(() => {
    if (currentState === AVATAR_STATES.SPEAKING && audioUrl) {
      if (audioRef.current) {
        audioRef.current.src = audioUrl;
        audioRef.current.play().catch(err => {
          console.warn('Could not autoplay audio:', err);
        });
      }
    }
  }, [currentState, audioUrl]);

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
        return settings.language === 'sw' ? 'Habari anazungumza...' : 'Rafiki is speaking...';
      case AVATAR_STATES.LISTENING:
        return settings.language === 'sw' ? 'Inasikiliza...' : 'Listening...';
      case AVATAR_STATES.THINKING:
        return settings.language === 'sw' ? 'Inafikiria...' : 'Thinking...';
      default:
        return settings.language === 'sw' ? 'Habari' : 'Rafiki';
    }
  };

  return (
    <div className={`real-talking-avatar-container ${getSizeClass()}`}>
      {/* Avatar Display */}
      <div className={`avatar-display-wrapper ${currentState}`}>
        {/* Video (when speaking with animation) */}
        {currentState === AVATAR_STATES.SPEAKING && videoUrl && (
          <div className="video-container">
            {videoLoading && (
              <div className="video-loading">
                <div className="spinner" />
                <p>Preparing video...</p>
              </div>
            )}
            <video
              ref={videoRef}
              className="avatar-video"
              muted={false}
              playsInline
              onLoadedData={() => setVideoLoading(false)}
              onError={() => {
                setVideoError('Failed to load video');
                setVideoLoading(false);
              }}
              onEnded={() => {
                if (onVideoEnd) onVideoEnd();
              }}
              aria-label="Rafiki speaking with animated avatar"
            />
            {videoError && (
              <div className="video-error">
                <p>{videoError}</p>
                <p>(Falling back to static image)</p>
              </div>
            )}
          </div>
        )}

        {/* Static Image (idle, listening, thinking, or fallback) */}
        {(currentState !== AVATAR_STATES.SPEAKING || !videoUrl || videoError) && (
          <div className="image-container">
            <img
              src={`${process.env.REACT_APP_API_URL || ''}/api/avatar/image`}
              alt="Rafiki, your virtual assistant"
              className="avatar-image"
              onError={(e) => {
                // Fallback to placeholder
                e.target.src = 'data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 200 200%22%3E%3Ccircle cx=%22100%22 cy=%22100%22 r=%2295%22 fill=%22%23C9825F%22/%3E%3C/svg%3E';
              }}
            />
            
            {/* Status Ring */}
            <div className={`status-ring ${currentState}`} />
            
            {/* Pulse Rings (listening/speaking) */}
            {(currentState === AVATAR_STATES.SPEAKING || currentState === AVATAR_STATES.LISTENING) && (
              <div className="pulse-rings">
                <span className="ring ring-1" />
                <span className="ring ring-2" />
                <span className="ring ring-3" />
              </div>
            )}
          </div>
        )}
      </div>

      {/* Status Text */}
      <p className="avatar-status" aria-live="polite" aria-atomic="true">
        {getStatusText()}
      </p>

      {/* Hidden audio element for syncing */}
      {audioUrl && (
        <audio
          ref={audioRef}
          crossOrigin="anonymous"
          style={{ display: 'none' }}
        />
      )}
    </div>
  );
}

export default RealTalkingAvatar;
