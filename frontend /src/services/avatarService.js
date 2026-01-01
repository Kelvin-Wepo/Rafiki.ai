/**
 * Avatar Service
 * Handles communication with SadTalker backend for lip-synced videos
 * Falls back to animated avatar when video generation is unavailable
 */

import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

class AvatarService {
  constructor() {
    this.apiAvailable = null;
    this.avatars = [];
    this.currentAvatar = 'habari';
  }

  /**
   * Check if SadTalker service is available
   * @returns {Promise<{available: boolean, capabilities: object}>}
   */
  async checkStatus() {
    try {
      const response = await axios.get(`${API_BASE_URL}/avatar/status`);
      this.apiAvailable = response.data.api_available;
      return {
        available: response.data.api_available,
        capabilities: response.data.capabilities,
        avatarsCount: response.data.avatars_count,
      };
    } catch (error) {
      console.warn('Avatar service status check failed:', error);
      this.apiAvailable = false;
      return {
        available: false,
        capabilities: { animated_fallback: true },
        avatarsCount: 0,
      };
    }
  }

  /**
   * Get list of available avatars
   * @returns {Promise<Array>}
   */
  async getAvatars() {
    try {
      const response = await axios.get(`${API_BASE_URL}/avatar/list`);
      this.avatars = response.data.avatars;
      return this.avatars;
    } catch (error) {
      console.warn('Failed to get avatars:', error);
      // Return default avatar
      return [{
        id: 'habari',
        name: 'Habari (Default)',
        path: null,
      }];
    }
  }

  /**
   * Set the current avatar
   * @param {string} avatarId 
   */
  setCurrentAvatar(avatarId) {
    this.currentAvatar = avatarId;
  }

  /**
   * Generate a lip-synced video from audio
   * @param {Blob|File} audioBlob - Audio file to lip-sync
   * @param {Object} options - Generation options
   * @returns {Promise<{success: boolean, videoUrl?: string, fallback?: boolean}>}
   */
  async generateFromAudio(audioBlob, options = {}) {
    const {
      avatarId = this.currentAvatar,
      preprocess = 'crop',
      stillMode = false,
      expressionScale = 1.0,
    } = options;

    try {
      const formData = new FormData();
      formData.append('audio', audioBlob, 'audio.wav');
      formData.append('avatar_id', avatarId);
      formData.append('preprocess', preprocess);
      formData.append('still_mode', stillMode);
      formData.append('expression_scale', expressionScale);

      const response = await axios.post(`${API_BASE_URL}/avatar/generate`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        responseType: 'blob',
        timeout: 120000, // 2 minutes for video generation
      });

      // Check if we got a video or fallback response
      if (response.headers['content-type']?.includes('video')) {
        const videoUrl = URL.createObjectURL(response.data);
        return { success: true, videoUrl, fallback: false };
      } else {
        // Got JSON fallback response
        const text = await response.data.text();
        const data = JSON.parse(text);
        return { success: false, fallback: true, error: data.error };
      }
    } catch (error) {
      console.warn('Video generation failed, using fallback:', error);
      return { 
        success: false, 
        fallback: true, 
        error: error.message || 'Video generation failed'
      };
    }
  }

  /**
   * Generate a lip-synced video from text
   * @param {string} text - Text to speak
   * @param {string} language - Language (en/sw)
   * @param {string} avatarId - Avatar to use
   * @returns {Promise<{success: boolean, videoUrl?: string, fallback?: boolean}>}
   */
  async generateFromText(text, language = 'en', avatarId = null) {
    try {
      const response = await axios.post(`${API_BASE_URL}/avatar/text-to-video`, {
        text,
        avatar_id: avatarId || this.currentAvatar,
        language,
      }, {
        responseType: 'blob',
        timeout: 120000,
      });

      if (response.headers['content-type']?.includes('video')) {
        const videoUrl = URL.createObjectURL(response.data);
        return { success: true, videoUrl, fallback: false };
      } else {
        const text = await response.data.text();
        const data = JSON.parse(text);
        return { success: false, fallback: true, error: data.error };
      }
    } catch (error) {
      console.warn('Text-to-video failed, using fallback:', error);
      return { 
        success: false, 
        fallback: true, 
        error: error.message || 'Text-to-video failed'
      };
    }
  }

  /**
   * Cleanup video URL to free memory
   * @param {string} videoUrl 
   */
  revokeVideoUrl(videoUrl) {
    if (videoUrl && videoUrl.startsWith('blob:')) {
      URL.revokeObjectURL(videoUrl);
    }
  }

  /**
   * Check if service is available (cached)
   * @returns {boolean|null}
   */
  isAvailable() {
    return this.apiAvailable;
  }
}

// Export singleton instance
const avatarService = new AvatarService();
export default avatarService;
