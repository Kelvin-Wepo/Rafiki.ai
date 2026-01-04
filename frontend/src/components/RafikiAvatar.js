import React, { useEffect, useRef, useState } from 'react';
import './RafikiAvatar.css';

const RafikiAvatar = ({ 
  audioStream, 
  fallbackImage = '👩',
  avatarId = 'habari',
  onLoadingChange,
  onError,
  autoPlay = true,
  showControls = true 
}) => {
  const videoRef = useRef(null);
  const audioRef = useRef(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [videoUrl, setVideoUrl] = useState(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [progress, setProgress] = useState(0);
  const [duration, setDuration] = useState(0);
  const [volume, setVolume] = useState(100);

  // Notify parent component of loading state
  useEffect(() => {
    if (onLoadingChange) {
      onLoadingChange(loading);
    }
  }, [loading, onLoadingChange]);

  // Generate avatar from audio
  useEffect(() => {
    if (!audioStream) return;

    const generateAvatar = async () => {
      setLoading(true);
      setError(null);
      setProgress(0);

      try {
        // Prepare form data
        const formData = new FormData();
        formData.append('audio_file', audioStream);
        formData.append('avatar_id', avatarId);
        formData.append('preprocess', 'crop');
        formData.append('still_mode', 'false');
        formData.append('expression_scale', '1.0');

        // Send to backend
        const response = await fetch('/api/avatar/animate', {
          method: 'POST',
          body: formData
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || `HTTP ${response.status}`);
        }

        // Get video blob
        const videoBlob = await response.blob();
        const url = URL.createObjectURL(videoBlob);
        setVideoUrl(url);

        // Auto-play if enabled
        if (autoPlay && videoRef.current) {
          videoRef.current.src = url;
          videoRef.current.play();
          setIsPlaying(true);
        }

      } catch (err) {
        const errorMessage = err.message || 'Failed to generate avatar';
        setError(errorMessage);
        if (onError) {
          onError(errorMessage);
        }
        console.error('Avatar generation failed:', err);
      } finally {
        setLoading(false);
      }
    };

    generateAvatar();
  }, [audioStream, avatarId, autoPlay, onError]);

  const handlePlayPause = () => {
    if (videoRef.current) {
      if (isPlaying) {
        videoRef.current.pause();
      } else {
        videoRef.current.play();
      }
      setIsPlaying(!isPlaying);
    }
  };

  const handleTimeUpdate = () => {
    if (videoRef.current) {
      setProgress(videoRef.current.currentTime);
    }
  };

  const handleLoadedMetadata = () => {
    if (videoRef.current) {
      setDuration(videoRef.current.duration);
    }
  };

  const handleSeek = (e) => {
    const time = parseFloat(e.target.value);
    if (videoRef.current) {
      videoRef.current.currentTime = time;
      setProgress(time);
    }
  };

  const handleVolumeChange = (e) => {
    const vol = parseFloat(e.target.value);
    setVolume(vol);
    if (videoRef.current) {
      videoRef.current.volume = vol / 100;
    }
  };

  const handleDownload = () => {
    if (videoUrl) {
      const link = document.createElement('a');
      link.href = videoUrl;
      link.download = `rafiki_avatar_${avatarId}_${Date.now()}.mp4`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  };

  const formatTime = (seconds) => {
    if (!seconds || isNaN(seconds)) return '0:00';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs < 10 ? '0' : ''}${secs}`;
  };

  return (
    <div className="rafiki-avatar-container" role="region" aria-label="Rafiki Avatar Player">
      {/* Loading state */}
      {loading && (
        <div className="avatar-loading" role="status" aria-live="polite">
          <div className="loading-spinner"></div>
          <p>Generating your avatar...</p>
          <div className="loading-progress">
            <div className="progress-bar">
              <div className="progress-fill" style={{ width: `${progress}%` }}></div>
            </div>
            <span className="progress-text">{Math.round(progress)}%</span>
          </div>
        </div>
      )}

      {/* Error state */}
      {error && (
        <div className="avatar-error" role="alert">
          <div className="error-icon">⚠️</div>
          <div className="error-content">
            <h3>Avatar Generation Failed</h3>
            <p>{error}</p>
          </div>
        </div>
      )}

      {/* Video player */}
      {!loading && !error && (
        <div className="avatar-player">
          {videoUrl ? (
            <div className="video-container">
              <video
                ref={videoRef}
                className="avatar-video"
                onTimeUpdate={handleTimeUpdate}
                onLoadedMetadata={handleLoadedMetadata}
                onPlay={() => setIsPlaying(true)}
                onPause={() => setIsPlaying(false)}
                muted={false}
                playsInline
                aria-label={`Animated avatar of Rafiki (${avatarId}) speaking`}
              />

              {/* Video controls */}
              {showControls && (
                <div className="video-controls">
                  {/* Play/Pause button */}
                  <button
                    className="control-button play-pause"
                    onClick={handlePlayPause}
                    aria-label={isPlaying ? 'Pause' : 'Play'}
                    title={isPlaying ? 'Pause (Space)' : 'Play (Space)'}
                  >
                    {isPlaying ? '⏸' : '▶️'}
                  </button>

                  {/* Progress slider */}
                  <div className="progress-slider-container">
                    <input
                      type="range"
                      min="0"
                      max={duration || 0}
                      value={progress}
                      onChange={handleSeek}
                      className="progress-slider"
                      aria-label="Video progress"
                    />
                  </div>

                  {/* Time display */}
                  <span className="time-display">
                    {formatTime(progress)} / {formatTime(duration)}
                  </span>

                  {/* Volume control */}
                  <div className="volume-control">
                    <label htmlFor="volume-slider" className="volume-icon">
                      {volume > 0 ? '🔊' : '🔇'}
                    </label>
                    <input
                      id="volume-slider"
                      type="range"
                      min="0"
                      max="100"
                      value={volume}
                      onChange={handleVolumeChange}
                      className="volume-slider"
                      aria-label="Volume"
                    />
                  </div>

                  {/* Download button */}
                  <button
                    className="control-button download"
                    onClick={handleDownload}
                    aria-label="Download video"
                    title="Download video (D)"
                  >
                    ⬇️
                  </button>

                  {/* Fullscreen button */}
                  <button
                    className="control-button fullscreen"
                    onClick={() => {
                      if (videoRef.current?.requestFullscreen) {
                        videoRef.current.requestFullscreen();
                      }
                    }}
                    aria-label="Fullscreen"
                    title="Fullscreen (F)"
                  >
                    ⛶
                  </button>
                </div>
              )}
            </div>
          ) : (
            <div className="avatar-placeholder">
              <div className="placeholder-icon">{fallbackImage}</div>
              <p>Waiting for audio...</p>
            </div>
          )}
        </div>
      )}

      {/* Accessibility features */}
      <audio
        ref={audioRef}
        style={{ display: 'none' }}
        aria-hidden="true"
      />
    </div>
  );
};

export default RafikiAvatar;
