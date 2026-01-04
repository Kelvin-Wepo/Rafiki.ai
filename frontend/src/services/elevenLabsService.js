/**
 * ElevenLabs Conversational AI Service
 * Full integration with ElevenLabs for voice conversations and TTS
 * Uses backend for signed URLs (secure) with fallback to direct connection
 */

import { Conversation } from '@elevenlabs/client';

// Configuration
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
const ELEVENLABS_AGENT_ID = process.env.REACT_APP_ELEVENLABS_AGENT_ID || 'agent_7901kbqbewwcf1avres326fjahdb';

class ElevenLabsService {
  constructor() {
    this.conversation = null;
    this.isConnected = false;
    this.agentId = ELEVENLABS_AGENT_ID;
    
    // Callbacks
    this.onConnect = null;
    this.onDisconnect = null;
    this.onMessage = null;
    this.onError = null;
    this.onModeChange = null;
    this.onStatusChange = null;
    this.onUserTranscript = null;
    this.onAgentResponse = null;
    
    // State
    this.currentLanguage = 'en';
    this.lastUserMessage = '';
    this.lastAgentResponse = '';
    this.volume = 1.0;
  }

  /**
   * Set the language for the conversation
   */
  setLanguage(language) {
    this.currentLanguage = language;
  }

  /**
   * Set volume level (0-1)
   */
  setVolumeLevel(volume) {
    this.volume = Math.max(0, Math.min(1, volume));
    if (this.conversation) {
      this.conversation.setVolume({ volume: this.volume });
    }
  }

  /**
   * Get signed URL from backend (secure method)
   */
  async getSignedUrl() {
    try {
      const response = await fetch(`${API_BASE_URL}/elevenlabs/signed-url?agent_id=${this.agentId}`);
      const data = await response.json();
      
      if (data.success && data.signed_url) {
        console.log('Got signed URL from backend');
        return data.signed_url;
      }
      return null;
    } catch (error) {
      console.warn('Could not get signed URL from backend:', error.message);
      return null;
    }
  }

  /**
   * Request microphone permission
   */
  async requestMicrophonePermission() {
    try {
      await navigator.mediaDevices.getUserMedia({ audio: true });
      return true;
    } catch (error) {
      console.error('Microphone permission denied:', error);
      return false;
    }
  }

  /**
   * Start a conversation with the ElevenLabs agent
   */
  async startConversation(options = {}) {
    try {
      // Request microphone permission first
      const hasPermission = await this.requestMicrophonePermission();
      if (!hasPermission) {
        throw new Error('Microphone permission is required for voice conversation');
      }

      // End any existing conversation
      if (this.conversation) {
        await this.endConversation();
      }

      console.log('Starting ElevenLabs conversation with agent:', this.agentId);

      // Try to get signed URL from backend first (more secure)
      const signedUrl = await this.getSignedUrl();
      
      // Configure session options
      const sessionConfig = {
        onConnect: () => {
          console.log('ElevenLabs: Connected');
          this.isConnected = true;
          if (this.onConnect) this.onConnect();
          if (this.onStatusChange) this.onStatusChange('connected');
        },
        
        onDisconnect: () => {
          console.log('ElevenLabs: Disconnected');
          this.isConnected = false;
          if (this.onDisconnect) this.onDisconnect();
          if (this.onStatusChange) this.onStatusChange('disconnected');
        },
        
        onMessage: (message) => {
          console.log('ElevenLabs message:', message);
          
          // Capture agent responses
          if (message.source === 'ai' && message.message) {
            this.lastAgentResponse = message.message;
            if (this.onAgentResponse) {
              this.onAgentResponse(message.message);
            }
          }
          
          // Capture user transcripts
          if (message.source === 'user' && message.message) {
            this.lastUserMessage = message.message;
            if (this.onUserTranscript) {
              this.onUserTranscript(message.message);
            }
          }
          
          if (this.onMessage) this.onMessage(message);
        },
        
        onError: (error) => {
          console.error('ElevenLabs error:', error);
          if (this.onError) this.onError(error);
          if (this.onStatusChange) this.onStatusChange('error');
        },
        
        onModeChange: (mode) => {
          console.log('ElevenLabs mode:', mode.mode);
          if (this.onModeChange) this.onModeChange(mode.mode);
          if (this.onStatusChange) this.onStatusChange(mode.mode);
        },
      };

      // Start session with signed URL if available, otherwise use agent ID
      if (signedUrl) {
        this.conversation = await Conversation.startSession({
          signedUrl,
          ...sessionConfig
        });
      } else {
        // Fallback: direct connection (agent must be public)
        this.conversation = await Conversation.startSession({
          agentId: this.agentId,
          ...sessionConfig
        });
      }

      // Set initial volume
      if (this.volume !== 1.0) {
        this.conversation.setVolume({ volume: this.volume });
      }

      return true;
    } catch (error) {
      console.error('Failed to start ElevenLabs conversation:', error);
      if (this.onError) this.onError(error.message);
      return false;
    }
  }

  /**
   * End the current conversation
   */
  async endConversation() {
    if (this.conversation) {
      try {
        await this.conversation.endSession();
        this.conversation = null;
        this.isConnected = false;
        console.log('ElevenLabs: Conversation ended');
      } catch (error) {
        console.error('Error ending conversation:', error);
      }
    }
  }

  /**
   * Get text-to-speech audio from backend
   */
  async textToSpeech(text, voiceId = null) {
    try {
      const response = await fetch(`${API_BASE_URL}/elevenlabs/tts`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text,
          voice_id: voiceId
        })
      });
      
      const data = await response.json();
      
      if (data.success && data.audio_data) {
        return {
          success: true,
          audioData: data.audio_data,
          contentType: data.content_type
        };
      }
      
      return { success: false, error: data.error || 'TTS failed' };
    } catch (error) {
      console.error('TTS error:', error);
      return { success: false, error: error.message };
    }
  }

  /**
   * Play audio from base64 data
   */
  async playAudio(base64Audio, contentType = 'audio/mp3') {
    return new Promise((resolve, reject) => {
      try {
        const audio = new Audio(`data:${contentType};base64,${base64Audio}`);
        audio.volume = this.volume;
        
        audio.onended = () => resolve();
        audio.onerror = (e) => reject(e);
        
        audio.play();
      } catch (error) {
        reject(error);
      }
    });
  }

  /**
   * Speak text using ElevenLabs TTS
   */
  async speak(text) {
    try {
      const result = await this.textToSpeech(text);
      
      if (result.success) {
        await this.playAudio(result.audioData, result.contentType);
        return true;
      }
      
      // Fallback to browser TTS
      if ('speechSynthesis' in window) {
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = this.currentLanguage === 'sw' ? 'sw-KE' : 'en-KE';
        window.speechSynthesis.speak(utterance);
        return true;
      }
      
      console.error('Speak failed:', result.error);
      return false;
    } catch (error) {
      console.error('Speak error:', error);
      return false;
    }
  }

  /**
   * Get available voices from backend
   */
  async getVoices() {
    try {
      const response = await fetch(`${API_BASE_URL}/elevenlabs/voices`);
      const data = await response.json();
      
      if (data.success) {
        return data.voices;
      }
      return [];
    } catch (error) {
      console.error('Error getting voices:', error);
      return [];
    }
  }

  /**
   * Set the volume for the agent's voice (legacy method)
   * @param {number} volume - Volume level between 0 and 1
   */
  setVolume(volume) {
    this.setVolumeLevel(volume);
  }

  /**
   * Check if conversation is active
   */
  isActive() {
    return this.isConnected && this.conversation !== null;
  }

  /**
   * Get current status
   */
  getStatus() {
    if (!this.conversation) return 'disconnected';
    return this.isConnected ? 'connected' : 'connecting';
  }

  /**
   * Get conversation ID
   */
  getConversationId() {
    return this.conversation?.getId() || null;
  }
}

// Export singleton instance
const elevenLabsService = new ElevenLabsService();
export default elevenLabsService;
