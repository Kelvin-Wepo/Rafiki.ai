import { useState, useCallback, useRef, useEffect } from 'react';

/**
 * Custom hook for text-to-speech with accessibility support
 * Uses the Web Speech API for browser-based speech synthesis
 */
const useTextToSpeech = (options = {}) => {
  const {
    voice = null,
    rate = 1.0,
    pitch = 1.0,
    volume = 1.0,
    language = 'en-KE',
    onStart = () => {},
    onEnd = () => {},
    onPause = () => {},
    onResume = () => {},
    onError = () => {}
  } = options;

  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [isSupported, setIsSupported] = useState(false);
  const [voices, setVoices] = useState([]);
  const [currentVoice, setCurrentVoice] = useState(voice);
  const [error, setError] = useState(null);
  
  const utteranceRef = useRef(null);
  const speechQueueRef = useRef([]);

  // Check for browser support and load voices
  useEffect(() => {
    const synth = window.speechSynthesis;
    setIsSupported(!!synth);

    if (synth) {
      const loadVoices = () => {
        const availableVoices = synth.getVoices();
        setVoices(availableVoices);
        
        // Try to find a voice for the specified language
        if (!currentVoice && availableVoices.length > 0) {
          const langVoice = availableVoices.find(v => v.lang.startsWith(language.split('-')[0]));
          const defaultVoice = availableVoices.find(v => v.default);
          setCurrentVoice(langVoice || defaultVoice || availableVoices[0]);
        }
      };

      loadVoices();
      
      // Chrome loads voices asynchronously
      if (synth.onvoiceschanged !== undefined) {
        synth.onvoiceschanged = loadVoices;
      }
    }

    return () => {
      if (synth) {
        synth.cancel();
      }
    };
  }, [language, currentVoice]);

  const speak = useCallback((text, immediate = false) => {
    const synth = window.speechSynthesis;
    
    if (!synth || !text) return;

    // If immediate, cancel any current speech
    if (immediate) {
      synth.cancel();
      speechQueueRef.current = [];
    }

    const utterance = new SpeechSynthesisUtterance(text);
    
    if (currentVoice) {
      utterance.voice = currentVoice;
    }
    
    utterance.rate = rate;
    utterance.pitch = pitch;
    utterance.volume = volume;
    utterance.lang = language;

    utterance.onstart = () => {
      setIsSpeaking(true);
      setIsPaused(false);
      setError(null);
      onStart();
    };

    utterance.onend = () => {
      setIsSpeaking(false);
      setIsPaused(false);
      onEnd();
      
      // Process next item in queue
      if (speechQueueRef.current.length > 0) {
        const nextText = speechQueueRef.current.shift();
        speak(nextText);
      }
    };

    utterance.onpause = () => {
      setIsPaused(true);
      onPause();
    };

    utterance.onresume = () => {
      setIsPaused(false);
      onResume();
    };

    utterance.onerror = (event) => {
      let errorMessage = 'Speech synthesis error';
      
      switch (event.error) {
        case 'canceled':
          errorMessage = 'Speech was canceled';
          break;
        case 'interrupted':
          errorMessage = 'Speech was interrupted';
          break;
        case 'audio-busy':
          errorMessage = 'Audio is busy';
          break;
        case 'network':
          errorMessage = 'Network error during speech';
          break;
        case 'synthesis-unavailable':
          errorMessage = 'Speech synthesis unavailable';
          break;
        case 'synthesis-failed':
          errorMessage = 'Speech synthesis failed';
          break;
        case 'language-unavailable':
          errorMessage = 'Language not available';
          break;
        case 'voice-unavailable':
          errorMessage = 'Voice not available';
          break;
        case 'text-too-long':
          errorMessage = 'Text is too long to speak';
          break;
        case 'invalid-argument':
          errorMessage = 'Invalid speech argument';
          break;
        default:
          errorMessage = `Speech error: ${event.error}`;
      }

      setError(errorMessage);
      setIsSpeaking(false);
      setIsPaused(false);
      onError(errorMessage, event.error);
    };

    utteranceRef.current = utterance;
    synth.speak(utterance);
  }, [currentVoice, rate, pitch, volume, language, onStart, onEnd, onPause, onResume, onError]);

  const queueSpeak = useCallback((text) => {
    if (isSpeaking) {
      speechQueueRef.current.push(text);
    } else {
      speak(text);
    }
  }, [isSpeaking, speak]);

  const stop = useCallback(() => {
    const synth = window.speechSynthesis;
    if (synth) {
      synth.cancel();
      speechQueueRef.current = [];
      setIsSpeaking(false);
      setIsPaused(false);
    }
  }, []);

  const pause = useCallback(() => {
    const synth = window.speechSynthesis;
    if (synth && isSpeaking) {
      synth.pause();
    }
  }, [isSpeaking]);

  const resume = useCallback(() => {
    const synth = window.speechSynthesis;
    if (synth && isPaused) {
      synth.resume();
    }
  }, [isPaused]);

  const setVoiceByName = useCallback((name) => {
    const selectedVoice = voices.find(v => v.name === name);
    if (selectedVoice) {
      setCurrentVoice(selectedVoice);
    }
  }, [voices]);

  const setVoiceByLanguage = useCallback((lang) => {
    const selectedVoice = voices.find(v => v.lang.startsWith(lang));
    if (selectedVoice) {
      setCurrentVoice(selectedVoice);
    }
  }, [voices]);

  return {
    speak,
    queueSpeak,
    stop,
    pause,
    resume,
    isSpeaking,
    isPaused,
    isSupported,
    voices,
    currentVoice,
    setVoiceByName,
    setVoiceByLanguage,
    error
  };
};

export default useTextToSpeech;
