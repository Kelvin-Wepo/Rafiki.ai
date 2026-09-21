/**
 * Wav2Lip frontend service helper.
 * Handles backend calls for lip-sync video generation and status checks.
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface LipSyncStatus {
  available: boolean;
  device?: string;
  cached_videos?: number;
  error?: string;
}

export async function checkLipSyncStatus(): Promise<LipSyncStatus> {
  const response = await fetch(`${API_BASE_URL}/avatar/lip-sync/status`);
  if (!response.ok) {
    return { available: false, error: 'Unable to reach Wav2Lip service' };
  }
  return response.json();
}

export async function generateLipSyncVideo(params: {
  imageFile: File;
  audioFile: File;
}): Promise<Blob> {
  const formData = new FormData();
  formData.append('image', params.imageFile);
  formData.append('audio', params.audioFile);

  const response = await fetch(`${API_BASE_URL}/avatar/generate-lip-sync`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || 'Failed to generate lip sync video');
  }

  return response.blob();
}
