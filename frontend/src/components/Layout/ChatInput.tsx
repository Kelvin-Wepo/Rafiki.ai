/**
 * ChatInput Component - Revamped
 * Text input with mic and send buttons - improved styling
 */

import { useState, useRef, useEffect, type KeyboardEvent } from 'react';
import { Mic, Send, Loader2, Sparkles } from 'lucide-react';
import type { VoiceState } from '../../lib/types';

interface ChatInputProps {
  onSendMessage: (message: string) => void;
  onMicClick: () => void;
  voiceState: VoiceState;
  isRecording: boolean;
  placeholder?: string;
}

export default function ChatInput({
  onSendMessage,
  onMicClick,
  voiceState,
  isRecording,
  placeholder = 'Type your message...',
}: ChatInputProps) {
  const [message, setMessage] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);
  const isDisabled = voiceState === 'processing' || voiceState === 'talking';
  const isSending = voiceState === 'processing';

  const handleSubmit = () => {
    if (message.trim() && !isDisabled) {
      onSendMessage(message.trim());
      setMessage('');
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  useEffect(() => {
    if (voiceState === 'idle' && inputRef.current) {
      inputRef.current.focus();
    }
  }, [voiceState]);

  return (
    <div className="sticky bottom-0 left-0 right-0 bg-gradient-to-t from-slate-950 via-slate-950/95 to-transparent pt-6 pb-4 px-4">
      <div className="max-w-2xl mx-auto">
        <div
          className="
            relative flex items-center gap-2
            bg-slate-800/60 backdrop-blur-xl
            border border-slate-700/50
            rounded-2xl p-2
            shadow-2xl shadow-black/20
            focus-within:border-emerald-500/50 
            focus-within:shadow-emerald-500/10
            transition-all duration-300
          "
        >
          {/* Gradient accent on top */}
          <div className="absolute -top-px left-4 right-4 h-px bg-gradient-to-r from-transparent via-emerald-500/50 to-transparent opacity-0 group-focus-within:opacity-100 transition-opacity" />

          {/* Mic Button */}
          <button
            onClick={onMicClick}
            disabled={isDisabled}
            className={`
              p-3 rounded-xl transition-all duration-200
              min-w-[48px] min-h-[48px] flex items-center justify-center
              ${
                isRecording
                  ? 'bg-gradient-to-br from-red-500 to-orange-500 text-white shadow-lg shadow-red-500/30'
                  : 'bg-slate-700/50 text-slate-400 hover:bg-slate-600/50 hover:text-white'
              }
              disabled:opacity-50 disabled:cursor-not-allowed
            `}
            aria-label={isRecording ? 'Stop recording' : 'Start voice input'}
          >
            <Mic className={`w-5 h-5 ${isRecording ? 'animate-pulse' : ''}`} />
          </button>

          {/* Text Input */}
          <input
            ref={inputRef}
            type="text"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isDisabled}
            placeholder={placeholder}
            className="
              flex-1 bg-transparent text-white
              placeholder:text-slate-500
              focus:outline-none
              text-base py-2 px-2
              disabled:opacity-50
            "
            aria-label="Message input"
          />

          {/* Send Button */}
          <button
            onClick={handleSubmit}
            disabled={!message.trim() || isDisabled}
            className="
              p-3 rounded-xl
              bg-gradient-to-r from-emerald-500 to-cyan-500
              text-white font-medium
              hover:from-emerald-400 hover:to-cyan-400
              hover:shadow-lg hover:shadow-emerald-500/20
              disabled:opacity-30 disabled:cursor-not-allowed disabled:hover:shadow-none
              transition-all duration-200
              min-w-[48px] min-h-[48px] flex items-center justify-center
            "
            aria-label="Send message"
          >
            {isSending ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Send className="w-5 h-5" />
            )}
          </button>
        </div>

        {/* Helper text */}
        <div className="flex items-center justify-center gap-2 mt-3 text-slate-500 text-xs">
          <Sparkles className="w-3 h-3" />
          <span>Press Enter to send • Voice is primary</span>
        </div>
      </div>
    </div>
  );
}
