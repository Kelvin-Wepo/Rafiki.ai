/**
 * Voice Waveform Visualization Component
 * Audio input visualization around avatar
 */

import React, { useMemo, useEffect, useState } from 'react';
import type { AvatarState, AudioAnalysis } from '../../types/avatar.types';
import { STATE_CONFIGS } from '../../types/avatar.types';

interface VoiceWaveformProps {
  state: AvatarState;
  audioData?: AudioAnalysis;
  barCount?: number;
  radius?: number;
}

const VoiceWaveform: React.FC<VoiceWaveformProps> = ({
  state,
  audioData,
  barCount = 32,
  radius = 48
}) => {
  const [waveformData, setWaveformData] = useState<number[]>(() => 
    Array(barCount).fill(0.1)
  );

  const glowConfig = STATE_CONFIGS[state].glow;
  const isActive = state === 'listening' || (state === 'speaking' && audioData?.isSpeaking);

  // Generate bar positions around the circle
  const bars = useMemo(() => {
    return Array.from({ length: barCount }, (_, i) => {
      const angle = (i / barCount) * Math.PI * 2 - Math.PI / 2;
      return {
        index: i,
        angle,
        x: 50 + Math.cos(angle) * radius,
        y: 50 + Math.sin(angle) * radius
      };
    });
  }, [barCount, radius]);

  // Update waveform data based on audio
  useEffect(() => {
    if (!isActive) {
      // Smooth decay to idle state
      setWaveformData(prev => 
        prev.map(v => Math.max(0.1, v * 0.9))
      );
      return;
    }

    if (audioData) {
      const { amplitude, frequency } = audioData;
      
      setWaveformData(prev => {
        const newData = [...prev];
        
        // Create waveform pattern based on audio
        for (let i = 0; i < barCount; i++) {
          const baseValue = amplitude * 0.8;
          // Add frequency-based variation
          const freqMod = Math.sin((i / barCount) * Math.PI * 4 + frequency * 0.01) * 0.3;
          // Add random variation for naturalness
          const randomMod = (Math.random() - 0.5) * 0.2 * amplitude;
          
          const targetValue = Math.max(0.1, Math.min(1, baseValue + freqMod + randomMod));
          
          // Smooth transition
          newData[i] = prev[i] + (targetValue - prev[i]) * 0.3;
        }
        
        return newData;
      });
    }
  }, [audioData, isActive, barCount]);

  // Idle animation
  useEffect(() => {
    if (isActive) return;

    const interval = setInterval(() => {
      setWaveformData(prev => {
        const time = Date.now() / 1000;
        return prev.map((_, i) => {
          const wave = Math.sin(time * 2 + i * 0.3) * 0.05;
          return 0.1 + wave + 0.02;
        });
      });
    }, 50);

    return () => clearInterval(interval);
  }, [isActive]);

  // Color based on state
  const getBarColor = (_index: number, value: number) => {
    if (state === 'listening') {
      return `rgba(65, 105, 225, ${0.3 + value * 0.7})`;
    }
    if (state === 'speaking') {
      return `rgba(200, 16, 46, ${0.3 + value * 0.7})`;
    }
    if (state === 'thinking') {
      return `rgba(255, 215, 0, ${0.3 + value * 0.5})`;
    }
    if (state === 'error') {
      return `rgba(178, 34, 34, ${0.4 + value * 0.6})`;
    }
    return `rgba(34, 139, 34, ${0.2 + value * 0.3})`;
  };

  return (
    <g className="rafiki-waveform" style={{ pointerEvents: 'none' }}>
      <defs>
        {/* Glow filter for bars */}
        <filter id="bar-glow" x="-50%" y="-50%" width="200%" height="200%">
          <feGaussianBlur stdDeviation="0.5" result="blur" />
          <feComposite in="SourceGraphic" in2="blur" operator="over" />
        </filter>

        {/* Gradient for bars */}
        <linearGradient id="bar-gradient" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stopColor={glowConfig.color} stopOpacity="1" />
          <stop offset="100%" stopColor={glowConfig.color} stopOpacity="0.3" />
        </linearGradient>
      </defs>

      {/* Background ring */}
      <circle
        cx="50"
        cy="50"
        r={radius}
        fill="none"
        stroke="rgba(255, 255, 255, 0.05)"
        strokeWidth="0.5"
      />

      {/* Waveform bars */}
      {bars.map((bar, index) => {
        const value = waveformData[index];
        const barHeight = 2 + value * 8;
        const barWidth = 1.5;
        
        // Calculate end point of bar (pointing outward)
        const endX = bar.x + Math.cos(bar.angle) * barHeight;
        const endY = bar.y + Math.sin(bar.angle) * barHeight;

        return (
          <g key={bar.index}>
            {/* Bar shadow */}
            <line
              x1={bar.x}
              y1={bar.y}
              x2={endX}
              y2={endY}
              stroke="rgba(0, 0, 0, 0.3)"
              strokeWidth={barWidth + 0.5}
              strokeLinecap="round"
              style={{ filter: 'blur(1px)' }}
            />
            
            {/* Main bar */}
            <line
              x1={bar.x}
              y1={bar.y}
              x2={endX}
              y2={endY}
              stroke={getBarColor(index, value)}
              strokeWidth={barWidth}
              strokeLinecap="round"
              filter={isActive && value > 0.3 ? 'url(#bar-glow)' : undefined}
              style={{
                transition: 'stroke 0.1s ease-out'
              }}
            />

            {/* Highlight dot at peak */}
            {value > 0.5 && isActive && (
              <circle
                cx={endX}
                cy={endY}
                r={0.8}
                fill={getBarColor(index, 1)}
                opacity={value}
              />
            )}
          </g>
        );
      })}

      {/* Center connector ring */}
      <circle
        cx="50"
        cy="50"
        r={radius - 1}
        fill="none"
        stroke={glowConfig.color}
        strokeWidth="0.3"
        opacity={isActive ? 0.5 : 0.2}
        style={{
          transition: 'opacity 0.3s ease-out'
        }}
      />

      {/* Active state outer glow */}
      {isActive && (
        <circle
          cx="50"
          cy="50"
          r={radius + 5}
          fill="none"
          stroke={glowConfig.color}
          strokeWidth="0.5"
          opacity={0.3}
          style={{ filter: 'blur(2px)' }}
        >
          <animate
            attributeName="opacity"
            values="0.2;0.4;0.2"
            dur="1s"
            repeatCount="indefinite"
          />
        </circle>
      )}

      {/* Speaking indicator */}
      {state === 'speaking' && audioData?.isSpeaking && (
        <g>
          {[0, 1, 2].map((i) => (
            <circle
              key={`speak-ring-${i}`}
              cx="50"
              cy="50"
              r={radius + 2 + i * 3}
              fill="none"
              stroke={glowConfig.color}
              strokeWidth="0.3"
              opacity={0.3 - i * 0.1}
            >
              <animate
                attributeName="r"
                values={`${radius + 2 + i * 3};${radius + 8 + i * 3};${radius + 2 + i * 3}`}
                dur={`${1 + i * 0.2}s`}
                repeatCount="indefinite"
              />
              <animate
                attributeName="opacity"
                values={`${0.3 - i * 0.1};${0.1};${0.3 - i * 0.1}`}
                dur={`${1 + i * 0.2}s`}
                repeatCount="indefinite"
              />
            </circle>
          ))}
        </g>
      )}
    </g>
  );
};

export default VoiceWaveform;
