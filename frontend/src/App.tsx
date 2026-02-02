/**
 * Rafiki AI - Modern Voice Assistant Demo
 * Beautiful, accessible interface showcasing avatar capabilities
 */

import { useState, useCallback, useRef, useEffect } from 'react';
import { RafikiTalkingAvatar } from './components/avatar';
import { useAudioAnalyzer, useSpeechSynthesis, useSadTalker, type Emotion } from './hooks';
import type { AvatarState, AudioAnalysis } from './types';
import './App.css';

// Demo messages in multiple languages
const DEMO_MESSAGES = {
  en: [
    "Hello! I'm Rafiki, your government AI assistant. How can I help you today?",
    "I can help you with public services, document applications, and general inquiries.",
    "Let me look that up for you. One moment please.",
    "Thank you for using our services. Is there anything else I can assist you with?",
    "I apologize, but I couldn't process that request. Please try again."
  ],
  sw: [
    "Habari! Mimi ni Rafiki, msaidizi wako wa serikali wa AI. Ninaweza kukusaidia vipi leo?",
    "Ninaweza kukusaidia na huduma za umma, maombi ya hati, na maswali ya jumla.",
    "Hebu nikutafutie hiyo. Tafadhali subiri kidogo.",
    "Asante kwa kutumia huduma zetu. Je, kuna kitu kingine ninachoweza kukusaidia?",
    "Samahani, sikuweza kushughulikia ombi hilo. Tafadhali jaribu tena."
  ]
};

function App() {
  const [currentState, setCurrentState] = useState<AvatarState>('idle');
  const [currentEmotion, setCurrentEmotion] = useState<Emotion>('neutral');
  const [isRecording, setIsRecording] = useState(false);
  const [showEffects, setShowEffects] = useState({ particles: true, waveform: true });
  const [language, setLanguage] = useState<'en' | 'sw'>('en');
  const [demoText, setDemoText] = useState(DEMO_MESSAGES.en[0]);
  const [useSadTalkerMode, setUseSadTalkerMode] = useState(true);
  const [hasAutoGreeted, setHasAutoGreeted] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const audioRef = useRef<HTMLAudioElement>(null);
  
  const { audioData, startAnalyzing, stopAnalyzing } = useAudioAnalyzer();
  const { speak, stop: stopSpeaking, isSpeaking, audioData: speechAudioData } = useSpeechSynthesis();
  
  // Update demo text when language changes
  useEffect(() => {
    setDemoText(DEMO_MESSAGES[language][0]);
  }, [language]);
  
  // SadTalker integration
  const {
    isGenerating: isSadTalkerGenerating,
    currentJob: sadTalkerJob,
    currentVideoUrl,
    currentAudioUrl,
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

  // Handle microphone input
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
    
    setTimeout(async () => {
      if (useSadTalkerMode && isBackendAvailable) {
        setCurrentState('speaking');
        setCurrentEmotion('confident');
        await generateFromText(demoText, language);
      } else {
        handleFallbackSpeak();
      }
    }, 2000);
  }, [stopAnalyzing, useSadTalkerMode, isBackendAvailable, generateFromText, demoText, language, handleFallbackSpeak]);

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
      try {
        setCurrentState('speaking');
        setCurrentEmotion('confident');
        const videoUrl = await generateFromText(demoText, language);
        if (!videoUrl) {
          handleFallbackSpeak();
        }
      } catch (error) {
        console.error('SadTalker failed:', error);
        handleFallbackSpeak();
      }
    } else {
      handleFallbackSpeak();
    }
  }, [
    stopSpeaking, isSpeaking, demoText, language,
    useSadTalkerMode, isBackendAvailable, generateFromText, cancelSadTalker, isSadTalkerGenerating,
    handleFallbackSpeak
  ]);

  // Handle video end
  const handleVideoEnd = useCallback(() => {
    setCurrentState('idle');
    setCurrentEmotion('happy');
    setTimeout(() => setCurrentEmotion('neutral'), 1500);
  }, []);

  // Get effective audio data
  const effectiveAudioData: AudioAnalysis | undefined = 
    currentState === 'speaking' && isSpeaking && !currentVideoUrl
      ? speechAudioData 
      : (currentState === 'listening' ? audioData : undefined);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setCurrentState('idle');
        setIsExpanded(false);
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
  }, [isRecording, handleStartListening, handleStopListening]);

  // Auto-greeting on page load
  useEffect(() => {
    if (!hasAutoGreeted && isBackendAvailable !== null) {
      setHasAutoGreeted(true);
      
      const timer = setTimeout(() => {
        if (useSadTalkerMode && isBackendAvailable) {
          setCurrentState('thinking');
          setCurrentEmotion('thoughtful');
          setTimeout(async () => {
            setCurrentState('speaking');
            setCurrentEmotion('confident');
            await generateFromText(DEMO_MESSAGES[language][0]);
          }, 1000);
        } else {
          setCurrentState('speaking');
          setCurrentEmotion('confident');
          speak(DEMO_MESSAGES[language][0]);
        }
      }, 2000);

      return () => clearTimeout(timer);
    }
  }, [hasAutoGreeted, isBackendAvailable, useSadTalkerMode, generateFromText, speak, language]);

  return (
    <div className="app">
      {/* Animated Background */}
      <div className="app-background">
        <div className="gradient-orb gradient-orb--1" />
        <div className="gradient-orb gradient-orb--2" />
        <div className="gradient-orb gradient-orb--3" />
      </div>

      {/* Header */}
      <header className="app-header">
        <div className="header-content">
          <div className="header-main">
            <div className="logo-container">
              <div className="logo-icon">🇰🇪</div>
              <div>
                <h1 className="app-title">Rafiki AI</h1>
                <p className="app-subtitle">Government Voice Assistant</p>
              </div>
            </div>
            <div className={`backend-status ${isBackendAvailable ? 'backend-status--online' : 'backend-status--offline'}`}>
              <span className="status-dot" />
              <span>{isBackendAvailable ? 'Ready' : 'Offline'}</span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="app-main">
        {/* Avatar Section */}
        <div className="avatar-section">
          <div className="avatar-container">
            <RafikiTalkingAvatar
              state={currentState}
              audioData={effectiveAudioData}
              size={420}
              accessible={true}
              showParticles={showEffects.particles}
              showWaveform={showEffects.waveform}
              emotion={currentEmotion}
              followCursor={true}
              videoUrl={currentVideoUrl}
              audioUrl={currentAudioUrl}
              onVideoEnd={handleVideoEnd}
            />
            
            {/* State Badge */}
            <div className={`state-badge state-badge--${currentState}`}>
              <span className="state-dot" />
              <span className="state-label">
                {currentState.charAt(0).toUpperCase() + currentState.slice(1)}
                {isSadTalkerGenerating && ' (Generating...)'}
              </span>
            </div>

            {/* Progress Bar */}
            {isSadTalkerGenerating && sadTalkerJob && (
              <div className="progress-container">
                <div className="progress-bar">
                  <div 
                    className="progress-fill" 
                    style={{ width: `${sadTalkerJob.progress * 100}%` }}
                  />
                </div>
                <span className="progress-text">
                  {Math.round(sadTalkerJob.progress * 100)}% Complete
                </span>
              </div>
            )}
          </div>

          {/* Voice Control */}
          <div className="voice-control">
            <button
              className={`voice-button ${isRecording ? 'voice-button--recording' : ''}`}
              onClick={isRecording ? handleStopListening : handleStartListening}
              aria-label={isRecording ? 'Stop listening' : 'Start speaking'}
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
              <span>{isRecording ? 'Stop' : 'Speak'}</span>
            </button>

            {isRecording && (
              <div className="audio-level-indicator">
                <div 
                  className="audio-level-bar" 
                  style={{ transform: `scaleX(${Math.max(0.1, audioData.amplitude)})` }}
                />
              </div>
            )}
          </div>
        </div>

        {/* Controls Section */}
        <div className={`controls-section ${isExpanded ? 'controls-section--expanded' : ''}`}>
          <button 
            className="expand-toggle"
            onClick={() => setIsExpanded(!isExpanded)}
            aria-label={isExpanded ? 'Collapse controls' : 'Expand controls'}
          >
            <span>{isExpanded ? '▼' : '▲'}</span>
            <span>Controls</span>
          </button>

          <div className="controls-content">
            {/* TTS Section */}
            <div className="control-card">
              <h3 className="card-title">Text-to-Speech</h3>
              
              <div className="mode-toggle">
                <label className="toggle-switch">
                  <input
                    type="checkbox"
                    checked={useSadTalkerMode}
                    onChange={(e) => setUseSadTalkerMode(e.target.checked)}
                    disabled={!isBackendAvailable}
                  />
                  <span className="toggle-slider" />
                  <span className="toggle-label">SadTalker Lip-Sync</span>
                </label>
                {!isBackendAvailable && (
                  <span className="mode-hint">Backend unavailable</span>
                )}
              </div>

              <div className="input-group">
                <label className="input-label">Language</label>
                <select 
                  className="select-input"
                  value={language}
                  onChange={(e) => setLanguage(e.target.value as 'en' | 'sw')}
                >
                  <option value="en">🇬🇧 English</option>
                  <option value="sw">🇰🇪 Kiswahili</option>
                </select>
              </div>

              <div className="input-group">
                <label className="input-label">Message</label>
                <select 
                  className="select-input"
                  value={demoText}
                  onChange={(e) => setDemoText(e.target.value)}
                >
                  {DEMO_MESSAGES[language].map((msg, i) => (
                    <option key={i} value={msg}>{msg.substring(0, 60)}...</option>
                  ))}
                </select>
              </div>

              <button 
                className={`action-button action-button--primary ${(isSpeaking || isSadTalkerGenerating) ? 'action-button--active' : ''}`}
                onClick={handleSpeak}
                disabled={isSadTalkerGenerating}
              >
                {isSadTalkerGenerating ? (
                  <>
                    <span className="spinner" />
                    Generating...
                  </>
                ) : isSpeaking ? (
                  <>
                    <span>⏹</span>
                    Stop
                  </>
                ) : (
                  <>
                    <span>▶</span>
                    Speak
                  </>
                )}
              </button>

              <textarea
                className="text-input"
                value={demoText}
                onChange={(e) => setDemoText(e.target.value)}
                placeholder="Enter text for Rafiki to speak..."
                rows={3}
              />
            </div>

            {/* Demo Controls */}
            <div className="control-card">
              <h3 className="card-title">Avatar Controls</h3>
              
              <div className="control-group">
                <label className="control-label">State</label>
                <div className="button-group">
                  {(['idle', 'listening', 'thinking', 'speaking', 'error'] as AvatarState[]).map((state) => (
                    <button
                      key={state}
                      className={`control-button ${currentState === state ? 'control-button--active' : ''}`}
                      onClick={() => setCurrentState(state)}
                    >
                      {state}
                    </button>
                  ))}
                </div>
              </div>

              <div className="control-group">
                <label className="control-label">Emotion</label>
                <div className="button-group button-group--wrap">
                  {(['neutral', 'happy', 'confident', 'thoughtful', 'attentive'] as Emotion[]).map((emotion) => (
                    <button
                      key={emotion}
                      className={`control-button control-button--small ${currentEmotion === emotion ? 'control-button--active' : ''}`}
                      onClick={() => setCurrentEmotion(emotion)}
                    >
                      {emotion}
                    </button>
                  ))}
                </div>
              </div>

              <div className="control-group">
                <label className="control-label">Effects</label>
                <div className="checkbox-group">
                  <label className="checkbox-label">
                    <input
                      type="checkbox"
                      checked={showEffects.particles}
                      onChange={(e) => setShowEffects(prev => ({ ...prev, particles: e.target.checked }))}
                    />
                    <span>Particles</span>
                  </label>
                  <label className="checkbox-label">
                    <input
                      type="checkbox"
                      checked={showEffects.waveform}
                      onChange={(e) => setShowEffects(prev => ({ ...prev, waveform: e.target.checked }))}
                    />
                    <span>Waveform</span>
                  </label>
                </div>
              </div>
            </div>

            {/* Help Section */}
            <div className="help-card">
              <h4 className="help-title">💡 Tips</h4>
              <ul className="help-list">
                <li>Press <kbd>Space</kbd> to start/stop recording</li>
                <li>Press <kbd>Esc</kbd> to reset</li>
                <li>Move your mouse to see eye tracking</li>
                <li>SadTalker generates realistic lip-sync videos</li>
              </ul>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="app-footer">
        <p>Rafiki AI • Accessible • Trustworthy • Inclusive</p>
        <p className="footer-tech">Built with React • SadTalker • Web Audio API</p>
      </footer>

      {/* Hidden audio element */}
      <audio ref={audioRef} style={{ display: 'none' }} />
    </div>
  );
}

export default App;
