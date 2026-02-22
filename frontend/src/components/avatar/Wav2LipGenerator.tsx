/**
 * Wav2Lip Generator Component
 * Generates lip-synced talking head videos from avatar image and audio
 */

import React, { useState, useCallback } from 'react';
import {
  generateLipSyncVideo,
  checkLipSyncStatus,
  type LipSyncStatus
} from '../../services/wav2lipService';
import './Wav2LipGenerator.css';

interface Wav2LipGeneratorProps {
  imageSrc: string;
  imageFile?: File;
  audioFile?: File;
  onVideoGenerated?: (videoUrl: string, videoBlob: Blob) => void;
  onError?: (error: Error) => void;
  autoGenerate?: boolean;
  className?: string;
}

interface GenerationState {
  isLoading: boolean;
  progress: number;
  videoUrl: string | null;
  error: string | null;
  status: LipSyncStatus | null;
}

export const Wav2LipGenerator: React.FC<Wav2LipGeneratorProps> = ({
  imageSrc,
  imageFile,
  audioFile,
  onVideoGenerated,
  onError,
  autoGenerate = false,
  className = ''
}) => {
  const [state, setState] = useState<GenerationState>({
    isLoading: false,
    progress: 0,
    videoUrl: null,
    error: null,
    status: null
  });

  const [serviceReady, setServiceReady] = useState<boolean | null>(null);

  // Check service status on mount
  React.useEffect(() => {
    checkServiceStatus();
  }, []);

  // Auto-generate if both files provided
  React.useEffect(() => {
    if (autoGenerate && imageFile && audioFile && !state.videoUrl && !state.isLoading) {
      handleGenerateVideo(imageFile, audioFile);
    }
  }, [autoGenerate, imageFile, audioFile]);

  const checkServiceStatus = useCallback(async () => {
    try {
      const status = await checkLipSyncStatus();
      setState(prev => ({ ...prev, status }));
      setServiceReady(status.available);
    } catch (error) {
      console.error('Failed to check service status:', error);
      setServiceReady(false);
    }
  }, []);

  const handleGenerateVideo = useCallback(
    async (image: File, audio: File) => {
      setState(prev => ({
        ...prev,
        isLoading: true,
        error: null,
        progress: 0
      }));

      try {
        // Simulate progress
        const progressInterval = setInterval(() => {
          setState(prev => ({
            ...prev,
            progress: Math.min(prev.progress + 10, 90)
          }));
        }, 500);

        const blob = await generateLipSyncVideo({
          imageFile: image,
          audioFile: audio
        });

        clearInterval(progressInterval);

        const videoUrl = URL.createObjectURL(blob);
        setState(prev => ({
          ...prev,
          videoUrl,
          isLoading: false,
          progress: 100,
          error: null
        }));

        onVideoGenerated?.(videoUrl, blob);
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Failed to generate video';
        setState(prev => ({
          ...prev,
          isLoading: false,
          error: errorMessage,
          progress: 0
        }));

        onError?.(error instanceof Error ? error : new Error(errorMessage));
      }
    },
    [onVideoGenerated, onError]
  );

  const handleImageUpload = useCallback(
    (file: File) => {
      if (!audioFile) {
        setState(prev => ({
          ...prev,
          error: 'Please select an audio file first'
        }));
        return;
      }
      handleGenerateVideo(file, audioFile);
    },
    [audioFile, handleGenerateVideo]
  );

  const handleAudioUpload = useCallback(
    (file: File) => {
      if (!imageFile && !imageSrc) {
        setState(prev => ({
          ...prev,
          error: 'Please select an image file first'
        }));
        return;
      }
      const image = imageFile || new File([imageSrc], 'avatar.png', { type: 'image/png' });
      handleGenerateVideo(image, file);
    },
    [imageFile, imageSrc, handleGenerateVideo]
  );

  const resetVideo = useCallback(() => {
    if (state.videoUrl) {
      URL.revokeObjectURL(state.videoUrl);
    }
    setState({
      isLoading: false,
      progress: 0,
      videoUrl: null,
      error: null,
      status: null
    });
  }, [state.videoUrl]);

  return (
    <div className={`wav2lip-generator ${className}`}>
      <div className="wav2lip-container">
        {/* Status Indicator */}
        <div className="wav2lip-status">
          {serviceReady === null && <span className="status-checking">Checking service...</span>}
          {serviceReady === true && (
            <span className="status-ready">
              ✓ Wav2Lip Ready ({state.status?.device || 'CPU'})
            </span>
          )}
          {serviceReady === false && (
            <span className="status-unavailable">
              ✗ Wav2Lip Unavailable (will use animated fallback)
            </span>
          )}
        </div>

        {/* Preview/Video Display */}
        <div className="wav2lip-preview">
          {state.videoUrl ? (
            <div className="video-container">
              <video
                src={state.videoUrl}
                autoPlay
                loop
                muted
                controls
                className="generated-video"
              />
              <div className="video-controls">
                <button
                  onClick={resetVideo}
                  className="btn btn-secondary"
                  title="Generate new video"
                >
                  Generate New
                </button>
                <a
                  href={state.videoUrl}
                  download="talking_head.mp4"
                  className="btn btn-primary"
                  title="Download video"
                >
                  Download
                </a>
              </div>
            </div>
          ) : (
            <div className="image-preview">
              <img src={imageSrc} alt="Avatar preview" />
              {state.isLoading && (
                <div className="loading-overlay">
                  <div className="spinner" />
                  <p>Generating video...</p>
                  <div className="progress-bar">
                    <div
                      className="progress-fill"
                      style={{ width: `${state.progress}%` }}
                    />
                  </div>
                  <p className="progress-text">{state.progress}%</p>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Error Message */}
        {state.error && (
          <div className="wav2lip-error">
            <span className="error-icon">⚠</span>
            <div className="error-content">
              <p className="error-title">Generation Failed</p>
              <p className="error-message">{state.error}</p>
              {!serviceReady && (
                <p className="error-hint">
                  Using animated avatar as fallback.
                  Install Wav2Lip to enable lip-sync video generation.
                </p>
              )}
            </div>
          </div>
        )}

        {/* File Upload Inputs (if files not provided) */}
        {!state.videoUrl && (
          <div className="wav2lip-inputs">
            {!imageFile && (
              <FileUploadInput
                accept="image/*"
                label="Avatar Image"
                onFileSelect={handleImageUpload}
                disabled={state.isLoading}
              />
            )}
            {!audioFile && (
              <FileUploadInput
                accept="audio/*"
                label="Audio File"
                onFileSelect={handleAudioUpload}
                disabled={state.isLoading}
              />
            )}
          </div>
        )}

        {/* Generate Button (if both files provided externally) */}
        {imageFile && audioFile && !state.videoUrl && !state.isLoading && (
          <button
            onClick={() => handleGenerateVideo(imageFile, audioFile)}
            disabled={!serviceReady}
            className="btn btn-primary btn-large"
          >
            {serviceReady === false ? 'Generate (Fallback)' : 'Generate Talking Head'}
          </button>
        )}

        {/* Service Info */}
        {state.status && serviceReady === true && (
          <div className="wav2lip-info">
            <p>
              <strong>GPU:</strong> {state.status.device === 'cuda' ? 'NVIDIA GPU' : 'CPU'}
            </p>
            <p>
              <strong>Cached:</strong> {state.status.cached_videos} video(s)
            </p>
            <p className="info-note">
              💡 First generation will take 15-30 seconds. Cached videos load instantly.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

/**
 * File Upload Input Sub-Component
 */
interface FileUploadInputProps {
  accept: string;
  label: string;
  onFileSelect: (file: File) => void;
  disabled?: boolean;
}

const FileUploadInput: React.FC<FileUploadInputProps> = ({
  accept,
  label,
  onFileSelect,
  disabled = false
}) => {
  const inputRef = React.useRef<HTMLInputElement>(null);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      onFileSelect(file);
    }
  };

  return (
    <div className="file-upload-input">
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        onChange={handleChange}
        disabled={disabled}
        className="file-input"
      />
      <button
        onClick={() => inputRef.current?.click()}
        disabled={disabled}
        className="btn btn-secondary"
      >
        Select {label}
      </button>
    </div>
  );
};

export default Wav2LipGenerator;
