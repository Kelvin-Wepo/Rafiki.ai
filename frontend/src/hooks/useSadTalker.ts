/**
 * useSadTalker Hook
 * Communicates with the SadTalker backend to generate lip-synced videos
 * 
 * Features:
 * - Generate video from text (TTS + lip-sync via /api/avatar/text-to-video)
 * - Generate video from audio file (via /api/avatar/animate)
 * - Track generation progress
 * - Cache generated videos for reuse
 * - Automatic retry on failure
 * - Real-time status updates
 * 
 * Backend endpoints:
 * - POST /api/avatar/animate - Upload audio, get video
 * - POST /api/avatar/text-to-video - Send text, get video with TTS
 * - GET /api/avatar/avatars - List available avatars
 * - GET /api/avatar/health - Health check
 */

import { useState, useCallback, useRef, useEffect } from 'react';

export interface SadTalkerJob {
  jobId: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress: number;
  videoUrl: string | null;
  audioUrl: string | null;  // Audio fallback when SadTalker unavailable
  isFallback: boolean;      // True if using audio-only fallback
  error: string | null;
}

export interface Avatar {
  id: string;
  name: string;
  path: string | null;
}

export interface SadTalkerOptions {
  backendUrl?: string;
  avatarId?: string;
  onProgress?: (progress: number, message: string) => void;
  onComplete?: (videoUrl: string) => void;
  onError?: (error: string) => void;
  cacheEnabled?: boolean;
}

export interface AnimationSettings {
  preprocess?: 'crop' | 'resize' | 'full';
  stillMode?: boolean;
  expressionScale?: number;
}

interface VideoCache {
  [textHash: string]: {
    videoUrl: string;
    blobUrl: string;
    timestamp: number;
  };
}

const DEFAULT_BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';
const CACHE_EXPIRY = 30 * 60 * 1000; // 30 minutes

/**
 * Simple hash function for caching text-to-video results
 */
function hashText(text: string, avatarId: string = ''): string {
  const combined = text + avatarId;
  let hash = 0;
  for (let i = 0; i < combined.length; i++) {
    const char = combined.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash;
  }
  return hash.toString(36);
}

export function useSadTalker(options: SadTalkerOptions = {}) {
  const {
    backendUrl = DEFAULT_BACKEND_URL,
    avatarId = 'habari',
    onProgress,
    onComplete,
    onError,
    cacheEnabled = true
  } = options;

  const [isGenerating, setIsGenerating] = useState(false);
  const [currentJob, setCurrentJob] = useState<SadTalkerJob | null>(null);
  const [currentVideoUrl, setCurrentVideoUrl] = useState<string | null>(null);
  const [currentAudioUrl, setCurrentAudioUrl] = useState<string | null>(null);
  const [isFallbackMode, setIsFallbackMode] = useState(false);
  const [isBackendAvailable, setIsBackendAvailable] = useState<boolean | null>(null);
  const [isSadTalkerAvailable, setIsSadTalkerAvailable] = useState<boolean | null>(null);
  const [availableAvatars, setAvailableAvatars] = useState<Avatar[]>([]);
  const [error, setError] = useState<string | null>(null);
  
  const videoCache = useRef<VideoCache>({});
  const abortControllerRef = useRef<AbortController | null>(null);
  const currentAvatarId = useRef(avatarId);

  // Update avatar ref when prop changes
  useEffect(() => {
    currentAvatarId.current = avatarId;
  }, [avatarId]);

  /**
   * Check if the backend is available
   */
  const checkBackendHealth = useCallback(async (): Promise<boolean> => {
    try {
      const response = await fetch(`${backendUrl}/api/avatar/health`, {
        method: 'GET',
        signal: AbortSignal.timeout(5000)
      });
      
      if (response.ok) {
        const data = await response.json();
        setIsBackendAvailable(true);
        setIsSadTalkerAvailable(data.sadtalker_available === true);
        return data.status === 'healthy';
      }
      setIsBackendAvailable(false);
      setIsSadTalkerAvailable(false);
      return false;
    } catch (err) {
      console.warn('SadTalker backend not available:', err);
      setIsBackendAvailable(false);
      setIsSadTalkerAvailable(false);
      return false;
    }
  }, [backendUrl]);

  /**
   * Fetch available avatars from backend
   */
  const fetchAvatars = useCallback(async (): Promise<Avatar[]> => {
    try {
      const response = await fetch(`${backendUrl}/api/avatar/avatars`);
      if (response.ok) {
        const data = await response.json();
        if (data.success && data.avatars) {
          setAvailableAvatars(data.avatars);
          return data.avatars;
        }
      }
      return [];
    } catch (err) {
      console.warn('Failed to fetch avatars:', err);
      return [];
    }
  }, [backendUrl]);

  /**
   * Generate video from text using backend TTS + SadTalker
   */
  const generateFromText = useCallback(async (
    text: string,
    _settings: AnimationSettings = {}
  ): Promise<string | null> => {
    // Settings available for future use with SadTalker API
    // const { preprocess, stillMode, expressionScale } = _settings;

    // Check cache first
    if (cacheEnabled) {
      const cacheKey = hashText(text, currentAvatarId.current);
      const cached = videoCache.current[cacheKey];
      
      if (cached && Date.now() - cached.timestamp < CACHE_EXPIRY) {
        console.log('Using cached video for:', text.substring(0, 30));
        setCurrentVideoUrl(cached.blobUrl);
        if (onComplete) onComplete(cached.blobUrl);
        return cached.blobUrl;
      }
    }

    try {
      setIsGenerating(true);
      setError(null);
      setIsFallbackMode(false);
      setCurrentJob({
        jobId: 'text-to-video',
        status: 'processing',
        progress: 0.1,
        videoUrl: null,
        audioUrl: null,
        isFallback: false,
        error: null
      });
      
      if (onProgress) onProgress(0.1, 'Starting text-to-video generation...');
      
      abortControllerRef.current = new AbortController();
      
      // Create form data for the API
      const formData = new FormData();
      formData.append('text', text);
      formData.append('avatar_id', currentAvatarId.current);
      formData.append('language', 'en');
      formData.append('use_elevenlabs', 'true');
      
      if (onProgress) onProgress(0.3, 'Generating speech and video...');
      
      // Call the text-to-video endpoint
      const response = await fetch(`${backendUrl}/api/avatar/text-to-video`, {
        method: 'POST',
        body: formData,
        signal: abortControllerRef.current.signal
      });
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
        throw new Error(errorData.detail || `Server error: ${response.status}`);
      }
      
      if (onProgress) onProgress(0.8, 'Processing response...');
      
      // Check if this is a fallback audio response
      const fallbackMode = response.headers.get('X-Fallback-Mode');
      const isFallback = fallbackMode === 'audio-only';
      const contentType = response.headers.get('Content-Type') || '';
      
      // Get the media blob
      const mediaBlob = await response.blob();
      const blobUrl = URL.createObjectURL(mediaBlob);
      
      if (isFallback || contentType.includes('audio')) {
        // Audio fallback mode - SadTalker was unavailable
        console.log('Using audio fallback mode');
        setIsFallbackMode(true);
        setCurrentAudioUrl(blobUrl);
        setCurrentVideoUrl(null);
        setCurrentJob({
          jobId: 'text-to-video',
          status: 'completed',
          progress: 1.0,
          videoUrl: null,
          audioUrl: blobUrl,
          isFallback: true,
          error: null
        });
        
        if (onProgress) onProgress(1.0, 'Audio ready (video unavailable)');
        if (onComplete) onComplete(blobUrl);
        
        return blobUrl;
      }
      
      // Video mode - SadTalker generated the video
      setCurrentVideoUrl(blobUrl);
      setCurrentAudioUrl(null);
      
      // Cache the result
      if (cacheEnabled) {
        const cacheKey = hashText(text, currentAvatarId.current);
        videoCache.current[cacheKey] = {
          videoUrl: blobUrl,
          blobUrl,
          timestamp: Date.now()
        };
      }
      
      setCurrentJob({
        jobId: 'text-to-video',
        status: 'completed',
        progress: 1.0,
        videoUrl: blobUrl,
        audioUrl: null,
        isFallback: false,
        error: null
      });
      
      if (onProgress) onProgress(1.0, 'Complete');
      if (onComplete) onComplete(blobUrl);
      
      return blobUrl;
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      console.error('Text-to-video error:', errorMessage);
      setError(errorMessage);
      setCurrentJob({
        jobId: 'text-to-video',
        status: 'failed',
        progress: 0,
        videoUrl: null,
        audioUrl: null,
        isFallback: false,
        error: errorMessage
      });
      if (onError) onError(errorMessage);
      return null;
    } finally {
      setIsGenerating(false);
    }
  }, [backendUrl, cacheEnabled, onProgress, onComplete, onError]);

  /**
   * Generate video from audio file/blob
   */
  const generateFromAudio = useCallback(async (
    audio: File | Blob,
    settings: AnimationSettings = {}
  ): Promise<string | null> => {
    const {
      preprocess = 'crop',
      stillMode = false,
      expressionScale = 1.0
    } = settings;

    try {
      setIsGenerating(true);
      setError(null);
      setIsFallbackMode(false);
      setCurrentJob({
        jobId: 'audio-to-video',
        status: 'processing',
        progress: 0.1,
        videoUrl: null,
        audioUrl: null,
        isFallback: false,
        error: null
      });
      
      if (onProgress) onProgress(0.1, 'Uploading audio...');
      
      abortControllerRef.current = new AbortController();
      
      // Create form data
      const formData = new FormData();
      formData.append('audio_file', audio, 'audio.wav');
      formData.append('avatar_id', currentAvatarId.current);
      formData.append('preprocess', preprocess);
      formData.append('still_mode', String(stillMode));
      formData.append('expression_scale', String(expressionScale));
      
      if (onProgress) onProgress(0.3, 'Generating lip-synced video...');
      
      // Call the animate endpoint
      const response = await fetch(`${backendUrl}/api/avatar/animate`, {
        method: 'POST',
        body: formData,
        signal: abortControllerRef.current.signal
      });
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
        throw new Error(errorData.detail || `Server error: ${response.status}`);
      }
      
      if (onProgress) onProgress(0.8, 'Processing video...');
      
      // Get the video blob
      const videoBlob = await response.blob();
      const blobUrl = URL.createObjectURL(videoBlob);
      
      setCurrentVideoUrl(blobUrl);
      setCurrentJob({
        jobId: 'audio-to-video',
        status: 'completed',
        progress: 1.0,
        videoUrl: blobUrl,
        audioUrl: null,
        isFallback: false,
        error: null
      });
      
      if (onProgress) onProgress(1.0, 'Complete');
      if (onComplete) onComplete(blobUrl);
      
      return blobUrl;
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      console.error('Audio-to-video error:', errorMessage);
      setError(errorMessage);
      setCurrentJob({
        jobId: 'audio-to-video',
        status: 'failed',
        progress: 0,
        videoUrl: null,
        audioUrl: null,
        isFallback: false,
        error: errorMessage
      });
      if (onError) onError(errorMessage);
      return null;
    } finally {
      setIsGenerating(false);
    }
  }, [backendUrl, onProgress, onComplete, onError]);

  /**
   * Generate video from ElevenLabs audio URL
   */
  const generateFromAudioUrl = useCallback(async (
    audioUrl: string,
    settings: AnimationSettings = {}
  ): Promise<string | null> => {
    try {
      // Fetch the audio from URL
      const response = await fetch(audioUrl);
      if (!response.ok) {
        throw new Error('Failed to fetch audio');
      }
      
      const audioBlob = await response.blob();
      return generateFromAudio(audioBlob, settings);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch audio';
      console.error('Audio URL error:', errorMessage);
      if (onError) onError(errorMessage);
      return null;
    }
  }, [generateFromAudio, onError]);

  /**
   * Cancel current generation
   */
  const cancel = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    setIsGenerating(false);
    setCurrentJob(null);
    setError(null);
  }, []);

  /**
   * Clear video cache
   */
  const clearCache = useCallback(() => {
    // Revoke all blob URLs
    Object.values(videoCache.current).forEach(cached => {
      URL.revokeObjectURL(cached.blobUrl);
    });
    videoCache.current = {};
  }, []);

  /**
   * Revoke current video URL
   */
  const revokeCurrentVideo = useCallback(() => {
    if (currentVideoUrl) {
      URL.revokeObjectURL(currentVideoUrl);
      setCurrentVideoUrl(null);
    }
    if (currentAudioUrl) {
      URL.revokeObjectURL(currentAudioUrl);
      setCurrentAudioUrl(null);
    }
    setIsFallbackMode(false);
  }, [currentVideoUrl, currentAudioUrl]);

  // Check backend health on mount
  useEffect(() => {
    checkBackendHealth();
    fetchAvatars();
  }, [checkBackendHealth, fetchAvatars]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      cancel();
    };
  }, [cancel]);

  return {
    // State
    isGenerating,
    currentJob,
    currentVideoUrl,
    currentAudioUrl,
    isFallbackMode,
    isBackendAvailable,
    isSadTalkerAvailable,
    availableAvatars,
    error,
    
    // Actions
    generateFromText,
    generateFromAudio,
    generateFromAudioUrl,
    cancel,
    clearCache,
    revokeCurrentVideo,
    checkBackendHealth,
    fetchAvatars
  };
}

export default useSadTalker;
