/**
 * InteractionArea Component - Revamped
 * Main microphone button and quick action chips with improved styling
 */

import { Mic, MicOff, Sparkles } from 'lucide-react';
import type { VoiceState, QuickAction } from '../../lib/types';
import { DEFAULT_QUICK_ACTIONS } from '../../lib/types';

interface InteractionAreaProps {
  voiceState: VoiceState;
  onMicClick: () => void;
  onQuickAction: (action: QuickAction) => void;
  isRecording: boolean;
  quickActions?: QuickAction[];
}

export default function InteractionArea({
  voiceState,
  onMicClick,
  onQuickAction,
  isRecording,
  quickActions = DEFAULT_QUICK_ACTIONS,
}: InteractionAreaProps) {
  const isMicActive = isRecording || voiceState === 'listening';
  const isDisabled = voiceState === 'processing' || voiceState === 'talking';

  const getMicGradient = () => {
    if (isMicActive) return 'from-red-500 via-orange-500 to-amber-500';
    return 'from-emerald-500 via-cyan-500 to-blue-500';
  };

  const getMicGlow = () => {
    if (isMicActive) return '0 0 50px rgba(239, 68, 68, 0.5), 0 0 100px rgba(249, 115, 22, 0.3)';
    return '0 0 40px rgba(16, 185, 129, 0.4), 0 0 80px rgba(6, 182, 212, 0.2)';
  };

  return (
    <div className="flex flex-col items-center gap-8 px-4 pb-6">
      {/* Microphone Button */}
      <div className="relative">
        {/* Outer pulse rings */}
        {isMicActive && (
          <>
            <div 
              className="absolute inset-0 rounded-full bg-red-500/20 animate-ping"
              style={{ animationDuration: '1.5s' }}
            />
            <div 
              className="absolute -inset-4 rounded-full border-2 border-red-500/30 animate-ping"
              style={{ animationDuration: '2s' }}
            />
          </>
        )}

        <button
          onClick={onMicClick}
          disabled={isDisabled}
          className={`
            relative w-20 h-20 sm:w-24 sm:h-24 rounded-full
            flex items-center justify-center
            transition-all duration-300
            focus:outline-none focus-visible:ring-4 focus-visible:ring-emerald-400/50
            disabled:opacity-50 disabled:cursor-not-allowed
            bg-gradient-to-br ${getMicGradient()}
            ${!isDisabled && !isMicActive ? 'hover:scale-110 active:scale-95' : ''}
          `}
          style={{
            boxShadow: getMicGlow(),
          }}
          aria-label={isMicActive ? 'Stop recording' : 'Start recording'}
          aria-pressed={isMicActive}
        >
          {/* Glass overlay */}
          <div className="absolute inset-1 rounded-full bg-gradient-to-br from-white/20 to-transparent" />
          
          {/* Icon container */}
          <div className={`
            relative z-10 p-3 rounded-full
            ${isMicActive ? 'bg-white/10 animate-pulse' : ''}
          `}>
            {isMicActive ? (
              <MicOff className="w-8 h-8 sm:w-10 sm:h-10 text-white drop-shadow-lg" />
            ) : (
              <Mic className="w-8 h-8 sm:w-10 sm:h-10 text-white drop-shadow-lg" />
            )}
          </div>

          {/* Spinning border when recording */}
          {isMicActive && (
            <div 
              className="absolute inset-0 rounded-full border-4 border-white/30 border-t-white/80 animate-spin"
              style={{ animationDuration: '1s' }}
            />
          )}
        </button>

        {/* Helper text below button */}
        <p className="text-center mt-4 text-sm text-slate-400">
          {isMicActive ? 'Tap to stop' : 'Tap to speak'}
        </p>
      </div>

      {/* Quick Action Chips */}
      <div className="w-full max-w-lg">
        <div className="flex items-center justify-center gap-2 mb-4">
          <Sparkles className="w-4 h-4 text-emerald-400" />
          <p className="text-slate-400 text-xs font-medium uppercase tracking-wider">Quick Actions</p>
        </div>
        <div className="flex flex-wrap justify-center gap-2 sm:gap-3">
          {quickActions.map((action) => (
            <button
              key={action.id}
              onClick={() => onQuickAction(action)}
              disabled={isDisabled}
              className="
                group relative px-4 sm:px-5 py-2.5 sm:py-3 rounded-xl
                bg-slate-800/50 backdrop-blur-sm
                border border-slate-700/50
                text-slate-300 text-sm font-medium
                hover:bg-slate-700/50 hover:text-white 
                hover:border-emerald-500/50 hover:shadow-lg hover:shadow-emerald-500/10
                disabled:opacity-50 disabled:cursor-not-allowed
                transition-all duration-200
                min-h-[48px]
              "
            >
              {/* Hover gradient */}
              <div className="absolute inset-0 rounded-xl bg-gradient-to-r from-emerald-500/10 to-cyan-500/10 opacity-0 group-hover:opacity-100 transition-opacity" />
              <span className="relative">{action.label}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
