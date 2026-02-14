/**
 * Wav2Lip Service - Frontend API client
 * Handles communication with the Wav2Lip backend service
 */

import { getStoredToken } from './authService';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface GenerateVideoParams {
  imageFile: File;
  audioFile: File;
}

export interface LipSyncStatus {
  success: boolean;
  service: string;
  available: boolean;
  device?: 'cuda' | 'cpu';
  cached_videos?: number;
  cache_dir?: string;
  error?: string;
}

/**
 * Generate a lip-synced video from an image and audio file
 * @param params - Image and audio files to process
 * @returns Blob containing the generated MP4 video
 * @throws Error if generation fails
 */
export async function generateLipSyncVideo(
  params: GenerateVideoParams
): Promise<Blob> {
  const formData = new FormData();
  formData.append('image', params.imageFile);
  formData.append('audio', params.audioFile);

  const token = getStoredToken();

  try {
    const response = await fetch(
      `${API_BASE_URL}/api/avatar/generate-lip-sync`,
      {
        method: 'POST',
        headers: {
          ...(token && { 'Authorization': `Bearer ${token}` })
        },
        body: formData
      }
    );

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(
        errorData.error ||
        `Failed to generate lip-sync video (${response.status})`
      );
    }

    const contentType = response.headers.get('content-type');
    if (!contentType?.includes('video/mp4')) {
      // Might be error JSON wrapped as fallback
      const jsonResponse = await response.json();
      if (jsonResponse.fallback) {
        throw new Error(jsonResponse.message || 'Video generation unavailable');
      }
      throw new Error('Invalid response type');
    }

    return response.blob();
  } catch (error) {
    console.error('Lip-sync video generation error:', error);
    throw error;
  }
}

/**
 * Download a lip-synced video directly (triggers browser download)
 * @param imageFile - Avatar image file
 * @param audioFile - Audio file
 * @param filename - Output filename (default: talking_head.mp4)
 */
export async function downloadLipSyncVideo(
  imageFile: File,
  audioFile: File,
  filename: string = 'talking_head.mp4'
): Promise<void> {
  try {
    const blob = await generateLipSyncVideo({
      imageFile,
      audioFile
    });

    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  } catch (error) {
    console.error('Failed to download video:', error);
    throw error;
  }
}

/**
 * Check Wav2Lip service status and availability
 * @returns Service status information
 */
export async function checkLipSyncStatus(): Promise<LipSyncStatus> {
  const token = getStoredToken();

  try {
    const response = await fetch(
      `${API_BASE_URL}/api/avatar/lip-sync/status`,
      {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          ...(token && { 'Authorization': `Bearer ${token}` })
        }
      }
    );

    if (!response.ok) {
      return {
        success: false,
        service: 'wav2lip',
        available: false,
        error: `Status check failed (${response.status})`
      };
    }

    return response.json();
  } catch (error) {
    console.error('Failed to check lip-sync status:', error);
    return {
      success: false,
      service: 'wav2lip',
      available: false,
      error: error instanceof Error ? error.message : 'Unknown error'
    };
  }
}

/**
 * Create a video URL object from image and audio
 * Useful for displaying preview or progress
 * @param imageFile - Avatar image
 * @param audioFile - Audio file
 * @returns Promise resolving to video blob URL
 */
export async function createVideoFromAudioAndImage(
  imageFile: File,
  audioFile: File
): Promise<string> {
  try {
    const blob = await generateLipSyncVideo({
      imageFile,
      audioFile
    });
    return URL.createObjectURL(blob);
  } catch (error) {
    console.error('Failed to create video:', error);
    throw error;
  }
}

/**
 * Utility function to convert audio URL to File object
 * @param audioUrl - URL to audio resource
 * @param filename - Filename for the File object
 * @returns Promise resolving to File object
 */
export async function audioUrlToFile(
  audioUrl: string,
  filename: string = 'audio.wav'
): Promise<File> {
  const response = await fetch(audioUrl);
  const blob = await response.blob();
  return new File([blob], filename, { type: blob.type });
}

/**
 * Utility function to convert image URL to File object
 * @param imageUrl - URL to image resource
 * @param filename - Filename for the File object
 * @returns Promise resolving to File object
 */
export async function imageUrlToFile(
  imageUrl: string,
  filename: string = 'avatar.png'
): Promise<File> {
  const response = await fetch(imageUrl);
  const blob = await response.blob();
  return new File([blob], filename, { type: blob.type });
}
