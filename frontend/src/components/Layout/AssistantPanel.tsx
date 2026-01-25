/**
 * AssistantPanel Component - Revamped
 * Central panel showing Rafiki avatar with improved animations and styling
 */

import { useMemo, useEffect, useState } from 'react';
import type { VoiceState } from '../../lib/types';
import { VOICE_STATE_CONFIG } from '../../lib/types';
import avatarImage from '../../assets/rafiki_avatar.png';

interface AssistantPanelProps {
  voiceState: VoiceState;
  audioLevel?: number;
}

export default function AssistantPanel({ voiceState, audioLevel = 0 }: AssistantPanelProps) {
  const stateConfig = VOICE_STATE_CONFIG[voiceState];
  const [animatedLevel, setAnimatedLevel] = useState(0);

  // Smooth audio level animation
  useEffect(() => {
    const target = audioLevel;
    const animate = () => {
      setAnimatedLevel(prev => prev + (target - prev) * 0.3);
    };
    const interval = setInterval(animate, 50);
    return () => clearInterval(interval);
  }, [audioLevel]);

  // Generate waveform bars with varied heights
  const waveformBars = useMemo(() => {
    return Array.from({ length: 24 }, (_, i) => ({
      id: i,
      delay: i * 0.05,
      baseHeight: 3 + Math.sin(i * 0.5) * 2,
    }));
  }, []);

  const getStateGradient = () => {
    switch (voiceState) {
      case 'listening': return 'from-blue-500 to-cyan-500';
      case 'talking': return 'from-orange-500 to-amber-500';
      case 'processing': return 'from-purple-500 to-pink-500';
      default: return 'from-emerald-500 to-cyan-500';
    }
  };

  const getGlowColor = () => {
    switch (voiceState) {
      case 'listening': return 'rgba(59, 130, 246, 0.5)';
      case 'talking': return 'rgba(249, 115, 22, 0.5)';
      case 'processing': return 'rgba(168, 85, 247, 0.5)';
      default: return 'rgba(16, 185, 129, 0.3)';
    }
  };

  return (
    <div className="flex flex-col items-center justify-center flex-1 px-4 py-6 sm:py-10">
      {/* Title Section */}
      <div className="text-center mb-6 sm:mb-10">
        <h2 className="text-4xl sm:text-5xl font-black mb-2">
          <span className="bg-gradient-to-r from-emerald-400 via-cyan-400 to-blue-400 bg-clip-text text-transparent">
            Rafiki
          </span>
        </h2>
        <p className="text-slate-400 text-sm sm:text-base font-medium">
          Your Government AI Assistant
        </p>
      </div>

      {/* Avatar Container */}
      <div className="relative mb-6 sm:mb-10">
        {/* Animated rings */}
        {(voiceState === 'listening' || voiceState === 'talking') && (
          <>
            <div 
              className={`absolute inset-0 rounded-full bg-gradient-to-r ${getStateGradient()} opacity-20 animate-ping`}
              style={{ animationDuration: '2s', transform: 'scale(1.2)' }}
            />
            <div 
              className={`absolute inset-0 rounded-full bg-gradient-to-r ${getStateGradient()} opacity-10 animate-ping`}
              style={{ animationDuration: '2.5s', animationDelay: '0.5s', transform: 'scale(1.4)' }}
            />
          </>
        )}

        {/* Rotating gradient border */}
        <div 
          className={`
            absolute -inset-1 rounded-full 
            bg-gradient-to-r ${getStateGradient()}
            ${voiceState !== 'idle' ? 'animate-spin' : ''}
            opacity-60
          `}
          style={{ 
            animationDuration: voiceState === 'processing' ? '2s' : '8s',
            filter: 'blur(8px)'
          }}
        />

        {/* Avatar wrapper */}
        <div
          className="relative rounded-full overflow-hidden"
          style={{
            width: 'clamp(160px, 35vw, 280px)',
            height: 'clamp(160px, 35vw, 280px)',
            boxShadow: `0 0 60px ${getGlowColor()}, inset 0 0 30px rgba(0,0,0,0.3)`,
          }}
        >
          {/* Gradient border */}
          <div className={`absolute inset-0 rounded-full bg-gradient-to-br ${getStateGradient()} p-1`}>
            <div className="w-full h-full rounded-full overflow-hidden bg-slate-900">
              <img
                src={avatarImage}
                alt="Rafiki AI Assistant"
                className="w-full h-full object-cover"
              />
            </div>
          </div>

          {/* Processing overlay */}
          {voiceState === 'processing' && (
            <div className="absolute inset-0 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center rounded-full">
              <div className="relative">
                <div className="w-16 h-16 border-4 border-purple-500/30 rounded-full" />
                <div className="absolute inset-0 w-16 h-16 border-4 border-purple-500 border-t-transparent rounded-full animate-spin" />
              </div>
            </div>
          )}

          {/* Listening indicator */}
          {voiceState === 'listening' && (
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="absolute inset-0 bg-blue-500/10 animate-pulse rounded-full" />
            </div>
          )}
        </div>
      </div>

      {/* Status Pill */}
      <div
        className={`
          inline-flex items-center gap-2.5 px-5 py-2.5 rounded-full
          bg-slate-800/60 backdrop-blur-sm
          border border-slate-700/50
          shadow-lg transition-all duration-300
        `}
        role="status"
        aria-live="polite"
      >
        <span className="relative flex h-3 w-3">
          <span 
            className={`
              absolute inline-flex h-full w-full rounded-full opacity-75
              ${stateConfig.color.replace('text-', 'bg-')}
              ${voiceState !== 'idle' ? 'animate-ping' : ''}
            `}
          />
          <span 
            className={`
              relative inline-flex rounded-full h-3 w-3
              ${stateConfig.color.replace('text-', 'bg-')}
            `}
          />
        </span>
        <span className={`text-sm font-semibold ${stateConfig.color}`}>
          {stateConfig.label}
        </span>
      </div>

      {/* Audio Waveform */}
      <div
        className="flex items-end justify-center gap-[3px] mt-6 h-12 px-4"
        aria-hidden="true"
      >
        {waveformBars.map((bar) => {
          const dynamicHeight = voiceState === 'talking' || voiceState === 'listening'
            ? bar.baseHeight + (animatedLevel / 100) * 30 + Math.sin(Date.now() / 150 + bar.delay * 15) * 10
            : bar.baseHeight;
          
          return (
            <div
              key={bar.id}
              className={`
                w-1 rounded-full transition-all duration-100
                bg-gradient-to-t ${getStateGradient()}
              `}
              style={{
                height: `${Math.max(3, dynamicHeight)}px`,
                opacity: voiceState === 'idle' ? 0.2 : 0.8,
              }}
            />
          );
        })}
      </div>

      {/* Helper Text */}
      <p className="text-slate-500 text-sm mt-4 text-center max-w-xs">
        {stateConfig.description}
      </p>
    </div>
  );
}
