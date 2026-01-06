/**
 * Rafiki Avatar Enhanced Demo Application
 * Government AI Voice Assistant Frontend
 * 
 * This demo showcases all enhanced avatar features:
 * - State transitions (Idle, Listening, Thinking, Speaking, Error)
 * - SadTalker integration for realistic lip-synced video
 * - Real-time audio analysis for lip-sync with phoneme detection (fallback)
 * - Natural blinking, breathing, and micro-movements
 * - Eye tracking following cursor
 * - Emotional expressions
 * - Particle effects and voice waveform visualization
 * - Text-to-speech with synchronized lip movement
 * - Accessible design with keyboard navigation
 * 
 * Now using the actual rafiki.png image with SadTalker lip-sync!
 */

import { useState, useCallback, useRef, useEffect } from 'react';
import { RafikiTalkingAvatar } from './components/avatar';
import { useAudioAnalyzer, useSpeechSynthesis, useSadTalker, type Emotion } from './hooks';
import type { AvatarState, AudioAnalysis } from './types';
import './App.css';

// Demo conversation messages
const DEMO_MESSAGES = [
  "Hello! I'm Rafiki, your government AI assistant. How can I help you today?",
  "I can help you with public services, document applications, and general inquiries.",
  "Let me look that up for you. One moment please.",
  "Thank you for using our services. Is there anything else I can assist you with?",
  "I apologize, but I couldn't process that request. Please try again."
];

function App() {
  const [currentState, setCurrentState] = useState<AvatarState>('idle');
  const [currentEmotion, setCurrentEmotion] = useState<Emotion>('neutral');
  const [isRecording, setIsRecording] = useState(false);
  const [showEffects, setShowEffects] = useState({ particles: true, waveform: true });
  const [demoText, setDemoText] = useState(DEMO_MESSAGES[0]);
  const [useSadTalkerMode, setUseSadTalkerMode] = useState(true);
  const audioRef = useRef<HTMLAudioElement>(null);
  
  const { audioData, startAnalyzing, stopAnalyzing } = useAudioAnalyzer();
  const { speak, stop: stopSpeaking, isSpeaking, audioData: speechAudioData, voices, selectedVoice, setVoice } = useSpeechSynthesis();
  
  // SadTalker integration
  const {
    isGenerating: isSadTalkerGenerating,
    currentJob: sadTalkerJob,
    currentVideoUrl,
    isBackendAvailable,
    generateFromText,
    cancel: cancelSadTalker
  } = useSadTalker({
    backendUrl: 'http://localhost:8000',
    onProgress: (progress: number, message: string) => {
      console.log(`SadTalker: ${message} (${Math.round(progress * 100)}%)`);
    },
    onComplete: (videoUrl: string) => {
      console.log('SadTalker video ready:', videoUrl);
    },
    onError: (error: string) => {
      console.error('SadTalker error:', error);
    }
  });

  // Fallback to browser TTS when SadTalker is unavailable
  const handleFallbackSpeak = useCallback(async () => {
    setCurrentState('speaking');
    setCurrentEmotion('confident');
    
    try {
      await speak(demoText);
      setCurrentState('idle');
      setCurrentEmotion('happy');
      setTimeout(() => setCurrentEmotion('neutral'), 1500);
    } catch (error) {
      console.error('Speech failed:', error);
      setCurrentState('error');
      setCurrentEmotion('apologetic');
    }
  }, [speak, demoText]);

  // Handle microphone input for listening state
  const handleStartListening = useCallback(async () => {
    try {
      await startAnalyzing();
      setCurrentState('listening');
      setCurrentEmotion('attentive');
      setIsRecording(true);
    } catch (error) {
      console.error('Failed to start microphone:', error);
      setCurrentState('error');
      setCurrentEmotion('apologetic');
    }
  }, [startAnalyzing]);

  const handleStopListening = useCallback(() => {
    stopAnalyzing();
    setIsRecording(false);
    setCurrentState('thinking');
    setCurrentEmotion('thoughtful');
    
    // Simulate processing and then speaking
    setTimeout(async () => {
      if (useSadTalkerMode && isBackendAvailable) {
        // Generate lip-synced video with SadTalker
        setCurrentState('speaking');
        setCurrentEmotion('confident');
        await generateFromText(demoText);
      } else {
        // Use browser TTS
        handleFallbackSpeak();
      }
    }, 2000);
  }, [stopAnalyzing, useSadTalkerMode, isBackendAvailable, generateFromText, demoText, handleFallbackSpeak]);

  // Handle TTS/SadTalker button click
  const handleSpeak = useCallback(async () => {
    if (isSpeaking || isSadTalkerGenerating) {
      stopSpeaking();
      cancelSadTalker();
      setCurrentState('idle');
      setCurrentEmotion('neutral');
      return;
    }

    setCurrentState('thinking');
    setCurrentEmotion('thoughtful');
    
    if (useSadTalkerMode && isBackendAvailable) {
      // Generate lip-synced video with SadTalker
      try {
        setCurrentState('speaking');
        setCurrentEmotion('confident');
        const videoUrl = await generateFromText(demoText);
        if (!videoUrl) {
          // Fallback if generation failed
          handleFallbackSpeak();
        }
      } catch (error) {
        console.error('SadTalker failed:', error);
        handleFallbackSpeak();
      }
    } else {
      // Use browser TTS
      handleFallbackSpeak();
    }
  }, [
    stopSpeaking, isSpeaking, demoText,
    useSadTalkerMode, isBackendAvailable, generateFromText, cancelSadTalker, isSadTalkerGenerating,
    handleFallbackSpeak
  ]);

  // Handle video end
  const handleVideoEnd = useCallback(() => {
    setCurrentState('idle');
    setCurrentEmotion('happy');
    setTimeout(() => setCurrentEmotion('neutral'), 1500);
  }, []);

  // State control buttons for demo
  const handleStateChange = useCallback((state: AvatarState) => {
    if (isRecording) {
      stopAnalyzing();
      setIsRecording(false);
    }
    if (isSpeaking) {
      stopSpeaking();
    }
    if (isSadTalkerGenerating) {
      cancelSadTalker();
    }
    setCurrentState(state);
  }, [isRecording, stopAnalyzing, isSpeaking, stopSpeaking, isSadTalkerGenerating, cancelSadTalker]);

  // Emotion control
  const handleEmotionChange = useCallback((emotion: Emotion) => {
    setCurrentEmotion(emotion);
  }, []);

  // Get effective audio data (real or from speech synthesis)
  const effectiveAudioData: AudioAnalysis | undefined = 
    currentState === 'speaking' && isSpeaking && !currentVideoUrl
      ? speechAudioData 
      : (currentState === 'listening' ? audioData : undefined);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        handleStateChange('idle');
      } else if (e.key === ' ' && e.target === document.body) {
        e.preventDefault();
        if (isRecording) {
          handleStopListening();
        } else {
          handleStartListening();
        }
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [isRecording, handleStartListening, handleStopListening, handleStateChange]);

  return (
    <div className="app">
      {/* Header */}
      <header className="app-header">
        <div className="header-content">
          <h1 className="app-title">Rafiki</h1>
          <p className="app-subtitle">Government AI Voice Assistant • SadTalker Edition</p>
          {/* Backend status indicator */}
          <div className={`backend-status ${isBackendAvailable ? 'backend-status--online' : 'backend-status--offline'}`}>
            <span className="status-dot" />
            <span>{isBackendAvailable ? 'SadTalker Ready' : 'SadTalker Offline (Using Fallback)'}</span>
          </div>
        </div>
      </header>

      {/* Main Avatar Display */}
      <main className="app-main">
        <div className="avatar-container">
          <RafikiTalkingAvatar
            state={currentState}
            audioData={effectiveAudioData}
            size={400}
            accessible={true}
            showParticles={showEffects.particles}
            showWaveform={showEffects.waveform}
            emotion={currentEmotion}
            followCursor={true}
            videoUrl={currentVideoUrl}
            isVideoPlaying={!!currentVideoUrl && currentState === 'speaking'}
            onVideoEnd={handleVideoEnd}
          />
          
          {/* State indicator */}
          <div className={`state-indicator state-indicator--${currentState}`}>
            <span className="state-dot" />
            <span className="state-label">
              {currentState.charAt(0).toUpperCase() + currentState.slice(1)}
              {isSadTalkerGenerating && ' (Generating...)'}
            </span>
            {currentEmotion !== 'neutral' && (
              <span className="emotion-label">• {currentEmotion}</span>
            )}
          </div>

          {/* Generation progress */}
          {isSadTalkerGenerating && sadTalkerJob && (
            <div className="generation-progress">
              <div className="progress-bar">
                <div 
                  className="progress-fill" 
                  style={{ width: `${sadTalkerJob.progress * 100}%` }}
                />
              </div>
              <span className="progress-text">
                Generating lip-sync video: {Math.round(sadTalkerJob.progress * 100)}%
              </span>
            </div>
          )}
        </div>

        {/* Interaction Controls */}
        <div className="controls-section">
          {/* Voice interaction button */}
          <button
            className={`voice-button ${isRecording ? 'voice-button--recording' : ''}`}
            onClick={isRecording ? handleStopListening : handleStartListening}
            aria-label={isRecording ? 'Stop listening' : 'Start speaking to Rafiki'}
          >
            <svg viewBox="0 0 24 24" className="voice-icon">
              {isRecording ? (
                <rect x="6" y="6" width="12" height="12" rx="2" fill="currentColor" />
              ) : (
                <path
                  d="M12 1a4 4 0 0 0-4 4v7a4 4 0 0 0 8 0V5a4 4 0 0 0-4-4zm0 16a6 6 0 0 1-6-6H4a8 8 0 0 0 7 7.93V22h2v-3.07A8 8 0 0 0 20 11h-2a6 6 0 0 1-6 6z"
                  fill="currentColor"
                />
              )}
            </svg>
            <span>{isRecording ? 'Tap to stop' : 'Tap to speak'}</span>
          </button>

          {/* Audio level indicator (when recording) */}
          {isRecording && (
            <div className="audio-level">
              <div 
                className="audio-level-bar" 
                style={{ transform: `scaleX(${audioData.amplitude})` }}
              />
            </div>
          )}
        </div>

        {/* TTS/SadTalker Demo Section */}
        <div className="tts-section">
          <h2 className="section-title">Text-to-Speech Demo</h2>
          
          {/* Mode toggle */}
          <div className="mode-toggle">
            <label className="toggle-label mode-toggle-label">
              <input
                type="checkbox"
                checked={useSadTalkerMode}
                onChange={(e) => setUseSadTalkerMode(e.target.checked)}
                disabled={!isBackendAvailable}
              />
              <span>Use SadTalker (Realistic Lip-Sync)</span>
            </label>
            {!isBackendAvailable && (
              <span className="mode-hint">Start backend server to enable</span>
            )}
          </div>

          <div className="tts-controls">
            <select 
              className="tts-message-select"
              value={demoText}
              onChange={(e) => setDemoText(e.target.value)}
            >
              {DEMO_MESSAGES.map((msg, i) => (
                <option key={i} value={msg}>{msg.substring(0, 50)}...</option>
              ))}
            </select>
            
            {!useSadTalkerMode && voices.length > 0 && (
              <select 
                className="tts-voice-select"
                value={selectedVoice?.name || ''}
                onChange={(e) => {
                  const voice = voices.find(v => v.name === e.target.value);
                  if (voice) setVoice(voice);
                }}
              >
                {voices.map((voice) => (
                  <option key={voice.name} value={voice.name}>
                    {voice.name} ({voice.lang})
                  </option>
                ))}
              </select>
            )}
            
            <button 
              className={`tts-button ${(isSpeaking || isSadTalkerGenerating) ? 'tts-button--speaking' : ''}`}
              onClick={handleSpeak}
              disabled={isSadTalkerGenerating}
            >
              {isSadTalkerGenerating ? '⏳ Generating...' : (isSpeaking ? '⏹ Stop' : '▶ Speak')}
            </button>
          </div>
          <textarea
            className="tts-input"
            value={demoText}
            onChange={(e) => setDemoText(e.target.value)}
            placeholder="Enter text for Rafiki to speak..."
            rows={3}
          />
        </div>

        {/* Demo Controls */}
        <div className="demo-controls">
          <h2 className="demo-title">Demo Controls</h2>
          
          {/* State buttons */}
          <div className="control-group">
            <h3 className="control-label">Avatar State</h3>
            <div className="state-buttons">
              {(['idle', 'listening', 'thinking', 'speaking', 'error'] as AvatarState[]).map((state) => (
                <button
                  key={state}
                  className={`state-button state-button--${state} ${currentState === state ? 'state-button--active' : ''}`}
                  onClick={() => handleStateChange(state)}
                >
                  {state.charAt(0).toUpperCase() + state.slice(1)}
                </button>
              ))}
            </div>
          </div>

          {/* Emotion buttons */}
          <div className="control-group">
            <h3 className="control-label">Emotion</h3>
            <div className="emotion-buttons">
              {(['neutral', 'happy', 'concerned', 'empathetic', 'curious', 'confident', 'thoughtful', 'attentive', 'apologetic'] as Emotion[]).map((emotion) => (
                <button
                  key={emotion}
                  className={`emotion-button ${currentEmotion === emotion ? 'emotion-button--active' : ''}`}
                  onClick={() => handleEmotionChange(emotion)}
                >
                  {emotion.charAt(0).toUpperCase() + emotion.slice(1)}
                </button>
              ))}
            </div>
          </div>

          {/* Effect toggles */}
          <div className="control-group">
            <h3 className="control-label">Visual Effects</h3>
            <div className="effect-toggles">
              <label className="toggle-label">
                <input
                  type="checkbox"
                  checked={showEffects.particles}
                  onChange={(e) => setShowEffects(prev => ({ ...prev, particles: e.target.checked }))}
                />
                <span>Particles</span>
              </label>
              <label className="toggle-label">
                <input
                  type="checkbox"
                  checked={showEffects.waveform}
                  onChange={(e) => setShowEffects(prev => ({ ...prev, waveform: e.target.checked }))}
                />
                <span>Waveform</span>
              </label>
            </div>
          </div>
          
          <div className="demo-info">
            <p>Move your mouse to see eye tracking. Try different emotions and states!</p>
            <p className="demo-hint">
              Press <kbd>Space</kbd> to start/stop recording, <kbd>Esc</kbd> to reset.
            </p>
            <p className="demo-hint sadtalker-hint">
              <strong>SadTalker Mode:</strong> Generates realistic lip-synced video from the rafiki.png image.
              Requires the backend server running at localhost:8000.
            </p>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="app-footer">
        <p>Rafiki Government AI Assistant • Accessible • Trustworthy • Inclusive</p>
        <p className="footer-note">
          Built with React • SadTalker • Web Audio API • Speech Synthesis
        </p>
      </footer>

      {/* Hidden audio element for speech playback */}
      <audio ref={audioRef} style={{ display: 'none' }} />
    </div>
  );
}

export default App;
