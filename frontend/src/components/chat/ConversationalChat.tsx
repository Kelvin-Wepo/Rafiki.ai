/**
 * ConversationalChat Component
 * Voice-enabled chat interface with speech recognition and TTS
 */

import { useState, useRef, useEffect } from 'react';
import { useVoiceConversation } from '../../hooks/useVoiceConversation';
import { Mic, MicOff, Send, Volume2, VolumeX, Globe, Loader2, MessageSquare } from 'lucide-react';

interface ConversationalChatProps {
  sessionId?: string | null;
  onSessionChange?: (sessionId: string) => void;
  className?: string;
}

export default function ConversationalChat({
  sessionId: externalSessionId,
  onSessionChange,
  className = ''
}: ConversationalChatProps) {
  const [textInput, setTextInput] = useState('');
  const [language, setLanguage] = useState<'en-KE' | 'sw-KE'>('en-KE');
  const [isMuted, setIsMuted] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const {
    state,
    messages,
    sessionId,
    isListening,
    transcript,
    audioLevel,
    startListening,
    stopListening,
    sendTextMessage,
    stopSpeaking,
    clearMessages,
    setLanguage: updateLanguage,
  } = useVoiceConversation({
    language,
    autoSpeak: !isMuted,
    onStateChange: (newState) => {
      console.log('Conversation state:', newState);
    },
    onMessage: (message) => {
      console.log('New message:', message);
    },
    onError: (error) => {
      console.error('Conversation error:', error);
    },
  });

  // Notify parent of session changes
  useEffect(() => {
    if (sessionId && onSessionChange) {
      onSessionChange(sessionId);
    }
  }, [sessionId, onSessionChange]);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, transcript]);

  // Handle language change
  const toggleLanguage = () => {
    const newLang = language === 'en-KE' ? 'sw-KE' : 'en-KE';
    setLanguage(newLang);
    updateLanguage(newLang);
  };

  // Handle mic button
  const handleMicClick = () => {
    if (isListening) {
      stopListening();
    } else {
      startListening();
    }
  };

  // Handle text submit
  const handleTextSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (textInput.trim()) {
      sendTextMessage(textInput.trim());
      setTextInput('');
    }
  };

  // Handle mute toggle
  const handleMuteToggle = () => {
    if (!isMuted && state === 'speaking') {
      stopSpeaking();
    }
    setIsMuted(!isMuted);
  };

  // Format timestamp
  const formatTime = (date: Date) => {
    return date.toLocaleTimeString(language === 'sw-KE' ? 'sw-KE' : 'en-KE', {
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className={`flex flex-col h-full bg-slate-900/50 backdrop-blur-xl rounded-2xl border border-slate-700/50 overflow-hidden ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 bg-slate-800/50 border-b border-slate-700/50">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-emerald-400 to-cyan-400 flex items-center justify-center">
            <MessageSquare className="w-5 h-5 text-slate-900" />
          </div>
          <div>
            <h2 className="text-white font-semibold">Rafiki Assistant</h2>
            <div className="flex items-center gap-2">
              <span className={`w-2 h-2 rounded-full ${
                state === 'idle' ? 'bg-green-400' :
                state === 'listening' ? 'bg-red-400 animate-pulse' :
                state === 'processing' ? 'bg-yellow-400 animate-pulse' :
                state === 'speaking' ? 'bg-blue-400 animate-pulse' :
                'bg-slate-400'
              }`} />
              <span className="text-xs text-slate-400">
                {state === 'idle' && 'Ready to help'}
                {state === 'listening' && 'Listening...'}
                {state === 'processing' && 'Thinking...'}
                {state === 'speaking' && 'Speaking...'}
                {state === 'error' && 'Error occurred'}
              </span>
            </div>
          </div>
        </div>

        {/* Controls */}
        <div className="flex items-center gap-2">
          {/* Language Toggle */}
          <button
            onClick={toggleLanguage}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-700/50 hover:bg-slate-600/50 text-slate-300 transition-colors"
            title="Toggle Language"
          >
            <Globe className="w-4 h-4" />
            <span className="text-xs font-medium">{language === 'en-KE' ? 'EN' : 'SW'}</span>
          </button>

          {/* Mute Toggle */}
          <button
            onClick={handleMuteToggle}
            className={`p-2 rounded-lg transition-colors ${
              isMuted 
                ? 'bg-red-500/20 text-red-400 hover:bg-red-500/30' 
                : 'bg-slate-700/50 text-slate-300 hover:bg-slate-600/50'
            }`}
            title={isMuted ? 'Unmute' : 'Mute'}
          >
            {isMuted ? <VolumeX className="w-4 h-4" /> : <Volume2 className="w-4 h-4" />}
          </button>
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* Welcome message if no messages */}
        {messages.length === 0 && !transcript && (
          <div className="text-center py-8">
            <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-gradient-to-br from-emerald-500/20 to-cyan-500/20 flex items-center justify-center">
              <MessageSquare className="w-8 h-8 text-emerald-400" />
            </div>
            <h3 className="text-white font-medium mb-2">
              {language === 'sw-KE' ? 'Habari! Mimi ni Rafiki' : 'Hello! I\'m Rafiki'}
            </h3>
            <p className="text-slate-400 text-sm max-w-md mx-auto">
              {language === 'sw-KE' 
                ? 'Ninaweza kukusaidia na huduma za serikali. Bonyeza kitufe cha maikrofoni au andika ujumbe wako.'
                : 'I can help you with government services. Click the microphone button or type your message below.'
              }
            </p>
          </div>
        )}

        {/* Message List */}
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                message.role === 'user'
                  ? 'bg-gradient-to-r from-emerald-500 to-cyan-500 text-white'
                  : 'bg-slate-800/80 text-slate-100 border border-slate-700/50'
              }`}
            >
              <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</p>
              <p className={`text-xs mt-1 ${
                message.role === 'user' ? 'text-white/60' : 'text-slate-500'
              }`}>
                {formatTime(message.timestamp)}
              </p>
            </div>
          </div>
        ))}

        {/* Live Transcript */}
        {transcript && (
          <div className="flex justify-end">
            <div className="max-w-[80%] rounded-2xl px-4 py-3 bg-gradient-to-r from-emerald-500/50 to-cyan-500/50 text-white/80 border border-emerald-500/30">
              <p className="text-sm leading-relaxed italic">{transcript}</p>
              <div className="flex items-center gap-2 mt-1">
                <span className="w-2 h-2 rounded-full bg-red-400 animate-pulse" />
                <span className="text-xs text-white/60">
                  {language === 'sw-KE' ? 'Inasikiliza...' : 'Listening...'}
                </span>
              </div>
            </div>
          </div>
        )}

        {/* Processing Indicator */}
        {state === 'processing' && (
          <div className="flex justify-start">
            <div className="bg-slate-800/80 rounded-2xl px-4 py-3 border border-slate-700/50">
              <div className="flex items-center gap-2">
                <Loader2 className="w-4 h-4 text-emerald-400 animate-spin" />
                <span className="text-sm text-slate-400">
                  {language === 'sw-KE' ? 'Rafiki anafikiria...' : 'Rafiki is thinking...'}
                </span>
              </div>
            </div>
          </div>
        )}

        {/* Speaking Indicator */}
        {state === 'speaking' && (
          <div className="flex justify-start">
            <div className="bg-slate-800/80 rounded-2xl px-4 py-3 border border-slate-700/50">
              <div className="flex items-center gap-2">
                <div className="flex gap-1">
                  {[...Array(3)].map((_, i) => (
                    <div
                      key={i}
                      className="w-1 h-3 bg-emerald-400 rounded-full animate-pulse"
                      style={{ animationDelay: `${i * 0.1}s` }}
                    />
                  ))}
                </div>
                <span className="text-sm text-slate-400">
                  {language === 'sw-KE' ? 'Rafiki anasema...' : 'Rafiki is speaking...'}
                </span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="px-4 py-3 bg-slate-800/50 border-t border-slate-700/50">
        {/* Audio Level Indicator */}
        {isListening && (
          <div className="mb-3">
            <div className="h-1 bg-slate-700 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-emerald-400 to-cyan-400 transition-all duration-75"
                style={{ width: `${Math.min(audioLevel * 2, 100)}%` }}
              />
            </div>
          </div>
        )}

        <div className="flex items-center gap-3">
          {/* Mic Button */}
          <button
            onClick={handleMicClick}
            disabled={state === 'processing' || state === 'speaking'}
            className={`
              relative flex-shrink-0 w-12 h-12 rounded-full flex items-center justify-center
              transition-all duration-300 transform
              ${isListening
                ? 'bg-red-500 text-white scale-110 shadow-lg shadow-red-500/30'
                : state === 'processing' || state === 'speaking'
                ? 'bg-slate-700 text-slate-500 cursor-not-allowed'
                : 'bg-gradient-to-r from-emerald-500 to-cyan-500 text-white hover:scale-105 hover:shadow-lg hover:shadow-emerald-500/30'
              }
            `}
          >
            {isListening ? (
              <MicOff className="w-5 h-5" />
            ) : (
              <Mic className="w-5 h-5" />
            )}
            
            {/* Pulse animation when listening */}
            {isListening && (
              <>
                <span className="absolute inset-0 rounded-full bg-red-500 animate-ping opacity-30" />
                <span className="absolute inset-0 rounded-full bg-red-500 animate-pulse opacity-20" />
              </>
            )}
          </button>

          {/* Text Input */}
          <form onSubmit={handleTextSubmit} className="flex-1 flex items-center gap-2">
            <input
              type="text"
              value={textInput}
              onChange={(e) => setTextInput(e.target.value)}
              placeholder={language === 'sw-KE' ? 'Andika ujumbe...' : 'Type a message...'}
              disabled={state === 'processing' || state === 'speaking' || isListening}
              className="
                flex-1 px-4 py-2.5 rounded-xl
                bg-slate-700/50 text-white placeholder-slate-400
                border border-slate-600/50 focus:border-emerald-500/50
                focus:outline-none focus:ring-2 focus:ring-emerald-500/20
                disabled:opacity-50 disabled:cursor-not-allowed
                transition-all
              "
            />
            <button
              type="submit"
              disabled={!textInput.trim() || state === 'processing' || state === 'speaking' || isListening}
              className="
                flex-shrink-0 p-2.5 rounded-xl
                bg-gradient-to-r from-emerald-500 to-cyan-500
                text-white
                disabled:opacity-50 disabled:cursor-not-allowed
                hover:scale-105 transition-all
              "
            >
              <Send className="w-5 h-5" />
            </button>
          </form>
        </div>

        {/* Hint Text */}
        <p className="text-xs text-slate-500 text-center mt-2">
          {language === 'sw-KE'
            ? 'Bonyeza maikrofoni kusema au andika ujumbe wako'
            : 'Press the microphone to speak or type your message'
          }
        </p>
      </div>
    </div>
  );
}
