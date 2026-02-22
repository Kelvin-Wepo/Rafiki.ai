/**
 * MainLayout Component - Revamped
 * Modern design with collapsible sidebar and improved styling
 */

import { useState, useCallback, useEffect, useRef } from 'react';
import Sidebar from './Sidebar';
import TopBar from './TopBar';
import AssistantPanel from './AssistantPanel';
import InteractionArea from './InteractionArea';
import ChatInput from './ChatInput';
import SystemMessage from './SystemMessage';
import { ConversationHistory, TranscriptDownload } from '../Dashboard';
import type { VoiceState, QuickAction } from '../../lib/types';
import type { User, Conversation } from '../../services/authService';
import { sessionApi, voiceApi, ttsApi, type AssistantResponse } from '../../lib/api';

interface MainLayoutProps {
  user: User | null;
  onLogout: () => void;
}

// Helper to convert blob to base64
const blobToBase64 = (blob: Blob): Promise<string> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onloadend = () => {
      const base64 = reader.result as string;
      const base64Data = base64.split(',')[1];
      resolve(base64Data);
    };
    reader.onerror = reject;
    reader.readAsDataURL(blob);
  });
};

export default function MainLayout({ user, onLogout }: MainLayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [voiceState, setVoiceState] = useState<VoiceState>('idle');
  const [isRecording, setIsRecording] = useState(false);
  const [audioLevel, setAudioLevel] = useState(0);
  const [currentView, setCurrentView] = useState<'chat' | 'history' | 'transcripts'>('chat');
  const [selectedConversation, setSelectedConversation] = useState<Conversation | null>(null);
  
  // Session and conversation state
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [lastResponse, setLastResponse] = useState<AssistantResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  
  // Audio refs
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const animationFrameRef = useRef<number | null>(null);
  const audioPlayerRef = useRef<HTMLAudioElement | null>(null);

  // Initialize session on mount (non-blocking)
  useEffect(() => {
    let isMounted = true;
    
    const initSession = async () => {
      try {
        const session = await sessionApi.create();
        if (isMounted) {
          setSessionId(session.session_id);
          console.log('Session created:', session.session_id);
        }
      } catch (err) {
        console.error('Failed to create session:', err);
        // Don't block UI - session will be created on first message
      }
    };
    
    // Initialize session asynchronously without awaiting
    initSession();
    
    return () => {
      isMounted = false;
    };
  }, []);

  // Close sidebar on escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && sidebarOpen) {
        setSidebarOpen(false);
      }
    };
    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [sidebarOpen]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
      if (audioContextRef.current) {
        audioContextRef.current.close();
      }
    };
  }, []);

  // Play TTS audio response with audio level analysis for lip-sync
  const playTTSResponse = useCallback(async (text: string) => {
    try {
      setVoiceState('talking');
      
      const ttsResponse = await ttsApi.textToSpeech({ text });
      
      if (ttsResponse.success && ttsResponse.audio_data) {
        const audioBlob = new Blob(
          [Uint8Array.from(atob(ttsResponse.audio_data), c => c.charCodeAt(0))],
          { type: ttsResponse.content_type || 'audio/mpeg' }
        );
        const audioUrl = URL.createObjectURL(audioBlob);
        
        if (audioPlayerRef.current) {
          audioPlayerRef.current.pause();
        }
        audioPlayerRef.current = new Audio(audioUrl);
        
        // Set up audio analysis for lip-sync during TTS playback
        try {
          const ttsAudioContext = new AudioContext();
          const ttsAnalyser = ttsAudioContext.createAnalyser();
          ttsAnalyser.fftSize = 256;
          
          const source = ttsAudioContext.createMediaElementSource(audioPlayerRef.current);
          source.connect(ttsAnalyser);
          ttsAnalyser.connect(ttsAudioContext.destination);
          
          const updateTTSLevel = () => {
            if (ttsAnalyser && audioPlayerRef.current && !audioPlayerRef.current.paused) {
              const dataArray = new Uint8Array(ttsAnalyser.frequencyBinCount);
              ttsAnalyser.getByteFrequencyData(dataArray);
              const average = dataArray.reduce((a, b) => a + b) / dataArray.length;
              setAudioLevel(average * 1.5); // Amplify for better lip movement
              requestAnimationFrame(updateTTSLevel);
            } else {
              setAudioLevel(0);
            }
          };
          
          audioPlayerRef.current.onplay = () => {
            updateTTSLevel();
          };
          
          audioPlayerRef.current.onended = () => {
            setVoiceState('idle');
            setAudioLevel(0);
            ttsAudioContext.close();
            URL.revokeObjectURL(audioUrl);
          };
          
          audioPlayerRef.current.onerror = () => {
            setVoiceState('idle');
            setAudioLevel(0);
            ttsAudioContext.close();
            URL.revokeObjectURL(audioUrl);
          };
        } catch (audioErr) {
          console.warn('Could not set up audio analysis:', audioErr);
          // Fallback without audio analysis
          audioPlayerRef.current.onended = () => {
            setVoiceState('idle');
            URL.revokeObjectURL(audioUrl);
          };
          audioPlayerRef.current.onerror = () => {
            setVoiceState('idle');
            URL.revokeObjectURL(audioUrl);
          };
        }
        
        await audioPlayerRef.current.play();
      } else {
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.onend = () => setVoiceState('idle');
        speechSynthesis.speak(utterance);
      }
    } catch (err) {
      console.error('TTS error:', err);
      setVoiceState('idle');
    }
  }, []);

  // Process assistant response
  const processResponse = useCallback(async (response: AssistantResponse) => {
    setLastResponse(response);
    
    if (response.text) {
      await playTTSResponse(response.text);
    } else {
      setVoiceState('idle');
    }
  }, [playTTSResponse]);

  // Handle new chat
  const handleNewChat = useCallback(async () => {
    setVoiceState('idle');
    setIsRecording(false);
    setAudioLevel(0);
    setLastResponse(null);
    setError(null);
    
    try {
      const session = await sessionApi.create();
      setSessionId(session.session_id);
      console.log('New session created:', session.session_id);
    } catch (err) {
      console.error('Failed to create new session:', err);
    }
  }, []);

  // Handle mic click - toggle recording
  const handleMicClick = useCallback(async () => {
    if (isRecording) {
      if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
        mediaRecorderRef.current.stop();
      }
      setIsRecording(false);
    } else {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        
        audioContextRef.current = new AudioContext();
        analyserRef.current = audioContextRef.current.createAnalyser();
        const source = audioContextRef.current.createMediaStreamSource(stream);
        source.connect(analyserRef.current);
        analyserRef.current.fftSize = 256;
        
        const updateLevel = () => {
          if (analyserRef.current) {
            const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount);
            analyserRef.current.getByteFrequencyData(dataArray);
            const average = dataArray.reduce((a, b) => a + b) / dataArray.length;
            setAudioLevel(average);
          }
          animationFrameRef.current = requestAnimationFrame(updateLevel);
        };
        updateLevel();
        
        // Try to use opus codec for better compression, fallback to webm
        const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus') 
          ? 'audio/webm;codecs=opus' 
          : 'audio/webm';
        
        mediaRecorderRef.current = new MediaRecorder(stream, { mimeType });
        audioChunksRef.current = [];
        
        mediaRecorderRef.current.ondataavailable = (e) => {
          if (e.data.size > 0) {
            audioChunksRef.current.push(e.data);
          }
        };
        
        mediaRecorderRef.current.onstop = async () => {
          if (animationFrameRef.current) {
            cancelAnimationFrame(animationFrameRef.current);
          }
          stream.getTracks().forEach(track => track.stop());
          setAudioLevel(0);
          
          const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
          console.log('Recording complete:', audioBlob.size, 'bytes');
          
          // Check minimum recording size (at least 5KB for meaningful audio)
          if (audioBlob.size < 5000) {
            console.warn('Recording too short:', audioBlob.size, 'bytes');
            setError('Recording too short. Please hold the mic button and speak for at least 1-2 seconds.');
            setVoiceState('idle');
            return;
          }
          
          // Process audio
          setVoiceState('processing');
          try {
            const base64Audio = await blobToBase64(audioBlob);
            
            // Create session if needed
            let currentSessionId = sessionId;
            if (!currentSessionId) {
              const session = await sessionApi.create();
              currentSessionId = session.session_id;
              setSessionId(currentSessionId);
            }
            
            const response = await voiceApi.sendAudio(base64Audio, currentSessionId);
            
            if (response) {
              await processResponse(response);
            } else {
              setVoiceState('idle');
            }
          } catch (err) {
            console.error('Voice processing error:', err);
            setError('Failed to process voice. Please try again.');
            setVoiceState('idle');
          }
        };
        
        // Start recording with timeslice to capture data every 100ms
        mediaRecorderRef.current.start(100);
        setIsRecording(true);
        setVoiceState('listening');
      } catch (err) {
        console.error('Error accessing microphone:', err);
        setError('Could not access microphone. Please check permissions.');
      }
    }
  }, [isRecording, sessionId, processResponse]);

  // Handle quick action
  const handleQuickAction = useCallback(async (action: QuickAction) => {
    setVoiceState('processing');
    setError(null);
    
    try {
      // Create session if needed
      let currentSessionId = sessionId;
      if (!currentSessionId) {
        const session = await sessionApi.create();
        currentSessionId = session.session_id;
        setSessionId(currentSessionId);
      }
      
      const response = await voiceApi.sendMessage(action.query, currentSessionId);
      
      if (response) {
        await processResponse(response);
      } else {
        setVoiceState('idle');
      }
    } catch (err) {
      console.error('Quick action error:', err);
      setError('Failed to process request. Please try again.');
      setVoiceState('idle');
    }
  }, [sessionId, processResponse]);

  // Handle text message send
  const handleSendMessage = useCallback(async (message: string) => {
    setVoiceState('processing');
    setError(null);
    
    try {
      // Create session if needed
      let currentSessionId = sessionId;
      if (!currentSessionId) {
        const session = await sessionApi.create();
        currentSessionId = session.session_id;
        setSessionId(currentSessionId);
      }
      
      const response = await voiceApi.sendMessage(message, currentSessionId);
      
      if (response) {
        await processResponse(response);
      } else {
        setVoiceState('idle');
      }
    } catch (err) {
      console.error('Send message error:', err);
      setError('Failed to send message. Please try again.');
      setVoiceState('idle');
    }
  }, [sessionId, processResponse]);

  return (
    <div className="flex h-screen overflow-hidden bg-[var(--ke-gray-50)]">
      {/* Sidebar - Old style for voice mode (uses dark theme) */}
      <Sidebar
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        user={user}
        onNewChat={handleNewChat}
        onLogout={onLogout}
        currentView={currentView}
        onViewChange={setCurrentView}
        isCollapsed={sidebarCollapsed}
        onToggleCollapse={() => setSidebarCollapsed(!sidebarCollapsed)}
      />

      {/* Main Content Area */}
      <main className="relative flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Top Bar - Mobile/Tablet only */}
        <TopBar
          onMenuClick={() => setSidebarOpen(true)}
          onNewChat={handleNewChat}
        />

        {/* Error Message */}
        {error && (
          <div className="pt-4">
            <SystemMessage
              message={error}
              guidance="Please try again or type your message below."
              type="error"
              onDismiss={() => setError(null)}
            />
          </div>
        )}

        {/* Content - Conditionally render based on currentView */}
        {currentView === 'chat' ? (
          <>
            {/* Chat View */}
            <div className="flex-1 flex flex-col overflow-y-auto">
              {/* Assistant Panel */}
              <AssistantPanel
                voiceState={voiceState}
                audioLevel={audioLevel}
              />

              {/* Last Response Display */}
              {lastResponse && (
                <div className="pb-4">
                  <SystemMessage
                    message={lastResponse.text}
                    type="info"
                    dismissible={false}
                  />
                  {lastResponse.suggested_actions && lastResponse.suggested_actions.length > 0 && (
                    <div className="px-4 mt-3 w-full max-w-2xl mx-auto">
                      <div className="flex flex-wrap gap-2 justify-center">
                        {lastResponse.suggested_actions.map((action: string, index: number) => (
                          <button
                            key={index}
                            onClick={() => handleSendMessage(action)}
                            className="
                              px-4 py-2 
                              bg-slate-800/60 hover:bg-slate-700/60 
                              text-slate-300 hover:text-white
                              text-xs font-medium 
                              rounded-xl
                              border border-slate-700/50 hover:border-emerald-500/30
                              transition-all duration-200
                              hover:scale-[1.02]
                              focus:outline-none focus:ring-2 focus:ring-emerald-500/30
                              backdrop-blur-sm
                            "
                          >
                            {action}
                          </button>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Interaction Area */}
              <InteractionArea
                voiceState={voiceState}
                onMicClick={handleMicClick}
                onQuickAction={handleQuickAction}
                isRecording={isRecording}
              />
            </div>

            {/* Chat Input - Pinned to bottom */}
            <ChatInput
              onSendMessage={handleSendMessage}
              onMicClick={handleMicClick}
              voiceState={voiceState}
              isRecording={isRecording}
            />
          </>
        ) : currentView === 'history' ? (
          /* History View */
          <div className="flex-1 flex flex-col overflow-y-auto">
            <ConversationHistory
              onSelectConversation={(conversation) => {
                setSelectedConversation(conversation);
                setCurrentView('chat');
              }}
              selectedId={selectedConversation?.id}
              onNewConversation={handleNewChat}
            />
          </div>
        ) : (
          /* Transcripts View */
          <div className="flex-1 flex flex-col overflow-y-auto">
            <div className="p-6 max-w-4xl mx-auto w-full">
              <h2 className="text-2xl font-bold text-white mb-2">Download Transcripts</h2>
              <p className="text-slate-400 mb-6">Export your conversation transcripts in TXT or JSON format.</p>
              <TranscriptDownload preSelectedConversation={selectedConversation} />
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
