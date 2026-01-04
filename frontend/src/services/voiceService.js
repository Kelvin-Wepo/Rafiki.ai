/**
 * Voice Service
 * Handles speech recognition and text-to-speech in the browser
 */

class VoiceService {
  constructor() {
    this.recognition = null;
    this.synthesis = window.speechSynthesis;
    this.isListening = false;
    this.onResult = null;
    this.onError = null;
    this.onStart = null;
    this.onEnd = null;

    this.initializeRecognition();
  }

  initializeRecognition() {
    // Check for browser support
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    
    if (!SpeechRecognition) {
      console.warn('Speech recognition not supported in this browser');
      return;
    }

    this.recognition = new SpeechRecognition();
    this.recognition.continuous = false;
    this.recognition.interimResults = true;
    this.recognition.lang = 'en-KE'; // Kenyan English

    this.recognition.onstart = () => {
      this.isListening = true;
      if (this.onStart) this.onStart();
    };

    this.recognition.onend = () => {
      this.isListening = false;
      if (this.onEnd) this.onEnd();
    };

    this.recognition.onresult = (event) => {
      let finalTranscript = '';
      let interimTranscript = '';

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          finalTranscript += transcript;
        } else {
          interimTranscript += transcript;
        }
      }

      if (this.onResult) {
        this.onResult({
          final: finalTranscript,
          interim: interimTranscript,
          isFinal: finalTranscript.length > 0,
        });
      }
    };

    this.recognition.onerror = (event) => {
      this.isListening = false;
      console.error('Speech recognition error:', event.error);
      
      if (this.onError) {
        let message = 'An error occurred with speech recognition';
        switch (event.error) {
          case 'no-speech':
            message = 'No speech was detected. Please try again.';
            break;
          case 'audio-capture':
            message = 'No microphone was found. Please ensure a microphone is connected.';
            break;
          case 'not-allowed':
            message = 'Microphone access was denied. Please allow microphone access to use voice input.';
            break;
          case 'network':
            message = 'A network error occurred. Please check your connection.';
            break;
          default:
            message = `Speech recognition error: ${event.error}`;
        }
        this.onError(message);
      }
    };
  }

  isSupported() {
    return this.recognition !== null;
  }

  isSynthesisSupported() {
    return 'speechSynthesis' in window;
  }

  setLanguage(lang) {
    // Set recognition language: sw-KE for Kiswahili, en-KE for English
    if (this.recognition) {
      this.recognition.lang = lang || 'en-KE';
    }
  }

  startListening(lang = null) {
    if (!this.recognition) {
      if (this.onError) {
        this.onError('Speech recognition is not supported in this browser');
      }
      return false;
    }

    // Update language if provided
    if (lang) {
      this.recognition.lang = lang;
    }

    if (this.isListening) {
      return true;
    }

    try {
      this.recognition.start();
      return true;
    } catch (error) {
      console.error('Failed to start recognition:', error);
      if (this.onError) {
        this.onError('Failed to start voice recognition');
      }
      return false;
    }
  }

  stopListening() {
    if (this.recognition && this.isListening) {
      this.recognition.stop();
    }
  }

  speak(text, options = {}) {
    if (!this.synthesis) {
      console.warn('Speech synthesis not supported');
      return Promise.resolve();
    }

    return new Promise((resolve, reject) => {
      // Cancel any ongoing speech
      this.synthesis.cancel();

      const utterance = new SpeechSynthesisUtterance(text);
      
      // Use slower rate: 0.8 = 20% slower than normal
      utterance.rate = options.rate || 0.8;
      utterance.pitch = options.pitch || 1;
      utterance.volume = options.volume || 1;
      utterance.lang = options.lang || 'en-KE';

      // Try to select a natural-sounding voice
      const voices = this.synthesis.getVoices();
      if (options.voiceIndex !== undefined && voices[options.voiceIndex]) {
        utterance.voice = voices[options.voiceIndex];
      } else {
        // Find a natural/neural voice if available
        const langPrefix = options.lang?.startsWith('sw') ? 'sw' : 'en';
        const preferredVoice = voices.find(voice => 
          voice.lang.startsWith(langPrefix) && 
          (voice.name.includes('Neural') || voice.name.includes('Natural') || voice.name.includes('Google'))
        ) || voices.find(voice => voice.lang.startsWith(langPrefix));
        
        if (preferredVoice) {
          utterance.voice = preferredVoice;
        }
      }

      utterance.onend = () => resolve();
      utterance.onerror = (error) => reject(error);

      this.synthesis.speak(utterance);
    });
  }

  stopSpeaking() {
    if (this.synthesis) {
      this.synthesis.cancel();
    }
  }

  getVoices() {
    if (!this.synthesis) return [];
    return this.synthesis.getVoices();
  }

  setLanguage(lang) {
    if (this.recognition) {
      this.recognition.lang = lang;
    }
  }

  // Request microphone permission
  async requestMicrophonePermission() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      // Stop the stream immediately, we just needed permission
      stream.getTracks().forEach(track => track.stop());
      return true;
    } catch (error) {
      console.error('Microphone permission denied:', error);
      return false;
    }
  }

  // Convert audio blob to base64
  async audioToBase64(blob) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onloadend = () => {
        const base64 = reader.result.split(',')[1];
        resolve(base64);
      };
      reader.onerror = reject;
      reader.readAsDataURL(blob);
    });
  }
}

// Export singleton instance
const voiceService = new VoiceService();
export default voiceService;
