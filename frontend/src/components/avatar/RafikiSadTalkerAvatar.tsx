/**
 * RafikiSadTalkerAvatar - SadTalker-Integrated Avatar Component
 * 
 * Displays lip-synced video from SadTalker backend, with fallback
 * to RafikiImageAvatar when video is not available.
 * 
 * Features:
 * - Automatic video playback when available
 * - Seamless fallback to RafikiImageAvatar
 * - Loading and progress indicators
 * - State-based styling
 */

import {
  useState,
  useEffect,
  useRef,
  useCallback,
  forwardRef,
  useImperativeHandle,
} from 'react';
import RafikiImageAvatar from './RafikiImageAvatar';
import type { AvatarState } from '../../types/avatar.types';
import type { Emotion } from '../../hooks/useEmotions';
import './RafikiSadTalkerAvatar.css';

export interface RafikiSadTalkerAvatarProps {
  /** Size of the avatar in pixels */
  size?: number;
  /** Current avatar state */
  status?: 'idle' | 'listening' | 'speaking' | 'thinking' | 'error';
  /** SadTalker video URL to play */
  videoUrl?: string | null;
  /** Audio URL (fallback when SadTalker unavailable) */
  audioUrl?: string | null;
  /** Whether using audio fallback mode */
  isFallbackMode?: boolean;
  /** Whether video is being generated */
  isGenerating?: boolean;
  /** Generation progress (0-1) */
  progress?: number;
  /** Progress message */
  progressMessage?: string;
  /** Enable glow effects */
  enableGlow?: boolean;
  /** Show particle effects */
  showParticles?: boolean;
  /** Current emotion */
  emotion?: Emotion;
  /** Callback when video ends */
  onVideoEnd?: () => void;
  /** Callback when video starts */
  onVideoStart?: () => void;
  /** Callback when audio ends (fallback mode) */
  onAudioEnd?: () => void;
  /** CSS class name */
  className?: string;
}

// Map status to AvatarState
const statusToState: Record<string, AvatarState> = {
  idle: 'idle',
  listening: 'listening',
  speaking: 'speaking',
  thinking: 'thinking',
  error: 'error',
};

export const RafikiSadTalkerAvatar = forwardRef<HTMLDivElement, RafikiSadTalkerAvatarProps>(({
  size = 320,
  status = 'idle',
  videoUrl = null,
  audioUrl = null,
  isFallbackMode = false,
  isGenerating = false,
  progress = 0,
  progressMessage = '',
  enableGlow = true,
  showParticles = true,
  emotion = 'neutral',
  onVideoEnd,
  onVideoStart,
  onAudioEnd,
  className = '',
}, ref) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const audioRef = useRef<HTMLAudioElement>(null);
  
  const [isVideoPlaying, setIsVideoPlaying] = useState(false);
  const [isAudioPlaying, setIsAudioPlaying] = useState(false);
  const [videoError, setVideoError] = useState<string | null>(null);
  const [showVideo, setShowVideo] = useState(false);

  // Convert status to AvatarState for the fallback component
  const avatarState = statusToState[status] || 'idle';

  // Expose container ref
  useImperativeHandle(ref, () => containerRef.current!, []);

  // Handle video URL changes
  useEffect(() => {
    if (videoUrl && videoRef.current) {
      setVideoError(null);
      setShowVideo(true);
      videoRef.current.src = videoUrl;
      videoRef.current.load();
      
      // Auto-play when ready
      videoRef.current.play().catch(err => {
        console.error('Video autoplay failed:', err);
        setVideoError('Autoplay blocked - click to play');
      });
    } else {
      setShowVideo(false);
      setIsVideoPlaying(false);
    }
  }, [videoUrl]);

  // Handle audio URL changes (fallback mode)
  useEffect(() => {
    if (audioUrl && audioRef.current && isFallbackMode) {
      audioRef.current.src = audioUrl;
      audioRef.current.load();
      
      // Auto-play audio
      audioRef.current.play().catch(err => {
        console.error('Audio autoplay failed:', err);
      });
    } else if (!audioUrl && audioRef.current) {
      audioRef.current.pause();
      setIsAudioPlaying(false);
    }
  }, [audioUrl, isFallbackMode]);

  // Audio event handlers
  const handleAudioPlay = useCallback(() => {
    setIsAudioPlaying(true);
    if (onVideoStart) onVideoStart(); // Reuse callback for consistency
  }, [onVideoStart]);

  const handleAudioEnded = useCallback(() => {
    setIsAudioPlaying(false);
    if (onAudioEnd) onAudioEnd();
  }, [onAudioEnd]);

  // Video event handlers
  const handleVideoPlay = useCallback(() => {
    setIsVideoPlaying(true);
    if (onVideoStart) onVideoStart();
  }, [onVideoStart]);

  const handleVideoEnded = useCallback(() => {
    setIsVideoPlaying(false);
    setShowVideo(false);
    if (onVideoEnd) onVideoEnd();
  }, [onVideoEnd]);

  const handleVideoError = useCallback(() => {
    setVideoError('Video playback error');
    setShowVideo(false);
    setIsVideoPlaying(false);
  }, []);

  const handleVideoClick = useCallback(() => {
    if (videoRef.current && videoError) {
      videoRef.current.play().catch(console.error);
      setVideoError(null);
    }
  }, [videoError]);

  return (
    <div
      ref={containerRef}
      className={`rafiki-sadtalker-avatar ${className}`}
      style={{ width: size, height: size }}
      data-status={status}
      data-video-playing={isVideoPlaying}
      data-audio-playing={isAudioPlaying}
      data-fallback={isFallbackMode}
    >
      {/* Hidden audio element for fallback mode */}
      <audio
        ref={audioRef}
        onPlay={handleAudioPlay}
        onEnded={handleAudioEnded}
        style={{ display: 'none' }}
      />

      {/* Video Layer - shown when SadTalker video available */}
      {showVideo && (
        <div className="video-container" onClick={handleVideoClick}>
          <video
            ref={videoRef}
            className="avatar-video"
            playsInline
            onPlay={handleVideoPlay}
            onEnded={handleVideoEnded}
            onError={handleVideoError}
          />
          {videoError && (
            <div className="video-error">
              <span>{videoError}</span>
            </div>
          )}
        </div>
      )}

      {/* SVG Fallback - shown when no video or generating */}
      {!showVideo && !isVideoPlaying && (
        <div className="svg-container" data-glow={enableGlow}>
          <RafikiImageAvatar
            state={isAudioPlaying ? 'speaking' : avatarState}
            size={size}
            showParticles={showParticles}
            showWaveform={status === 'speaking' || isAudioPlaying}
            emotion={emotion}
            followCursor={status === 'idle' || status === 'listening'}
          />
        </div>
      )}

      {/* Fallback Mode Indicator */}
      {isFallbackMode && isAudioPlaying && (
        <div className="fallback-indicator">
          <span className="pulse-dot" />
          <span>Audio Only</span>
        </div>
      )}

      {/* Loading/Progress Overlay */}
      {isGenerating && (
        <div className="generation-overlay">
          <div className="progress-ring">
            <svg viewBox="0 0 100 100">
              <circle
                className="progress-bg"
                cx="50"
                cy="50"
                r="45"
              />
              <circle
                className="progress-fill"
                cx="50"
                cy="50"
                r="45"
                strokeDasharray={`${progress * 283} 283`}
              />
            </svg>
            <div className="progress-text">
              {Math.round(progress * 100)}%
            </div>
          </div>
          {progressMessage && (
            <div className="progress-message">{progressMessage}</div>
          )}
        </div>
      )}

      {/* Status Indicator */}
      <div className={`status-indicator status-${status}`} />
    </div>
  );
});

RafikiSadTalkerAvatar.displayName = 'RafikiSadTalkerAvatar';

export default RafikiSadTalkerAvatar;
