/**
 * Particle Effects Component
 * Ambient particles for thinking/processing states
 */

import React, { useMemo, useEffect, useState } from 'react';
import type { AvatarState } from '../../types/avatar.types';
import { STATE_CONFIGS } from '../../types/avatar.types';

interface Particle {
  id: number;
  x: number;
  y: number;
  size: number;
  opacity: number;
  speed: number;
  angle: number;
  delay: number;
}

interface ParticleEffectsProps {
  state: AvatarState;
  intensity?: number;
  particleCount?: number;
}

// Particle configurations for different states
const PARTICLE_CONFIGS: Record<AvatarState, {
  enabled: boolean;
  color: string;
  pattern: 'orbital' | 'rising' | 'radial' | 'pulse' | 'none';
  speed: number;
  size: { min: number; max: number };
}> = {
  idle: {
    enabled: true,
    color: 'rgba(34, 139, 34, 0.6)',
    pattern: 'orbital',
    speed: 0.5,
    size: { min: 0.5, max: 1.5 }
  },
  listening: {
    enabled: true,
    color: 'rgba(65, 105, 225, 0.7)',
    pattern: 'pulse',
    speed: 1,
    size: { min: 0.8, max: 2 }
  },
  thinking: {
    enabled: true,
    color: 'rgba(255, 215, 0, 0.7)',
    pattern: 'orbital',
    speed: 2,
    size: { min: 1, max: 2.5 }
  },
  speaking: {
    enabled: true,
    color: 'rgba(200, 16, 46, 0.6)',
    pattern: 'radial',
    speed: 1.5,
    size: { min: 0.5, max: 1.5 }
  },
  error: {
    enabled: true,
    color: 'rgba(178, 34, 34, 0.8)',
    pattern: 'pulse',
    speed: 3,
    size: { min: 1, max: 3 }
  }
};

const ParticleEffects: React.FC<ParticleEffectsProps> = ({
  state,
  intensity = 1,
  particleCount = 12
}) => {
  const [time, setTime] = useState(0);
  const config = PARTICLE_CONFIGS[state];
  const glowColor = STATE_CONFIGS[state].glow.color;

  // Generate particles
  const particles = useMemo((): Particle[] => {
    return Array.from({ length: particleCount }, (_, i) => ({
      id: i,
      x: 50 + (Math.random() - 0.5) * 60,
      y: 50 + (Math.random() - 0.5) * 60,
      size: config.size.min + Math.random() * (config.size.max - config.size.min),
      opacity: 0.3 + Math.random() * 0.5,
      speed: 0.5 + Math.random() * 1.5,
      angle: (i / particleCount) * Math.PI * 2,
      delay: Math.random() * 2
    }));
  }, [particleCount, config.size.min, config.size.max]);

  // Animation loop
  useEffect(() => {
    if (!config.enabled) return;

    let animationFrame: number;
    let startTime = performance.now();

    const animate = (currentTime: number) => {
      const elapsed = (currentTime - startTime) / 1000;
      setTime(elapsed);
      animationFrame = requestAnimationFrame(animate);
    };

    animationFrame = requestAnimationFrame(animate);

    return () => {
      cancelAnimationFrame(animationFrame);
    };
  }, [config.enabled]);

  if (!config.enabled) return null;

  // Calculate particle positions based on pattern
  const getParticlePosition = (particle: Particle) => {
    const t = (time + particle.delay) * config.speed * particle.speed;
    const baseX = particle.x;
    const baseY = particle.y;

    switch (config.pattern) {
      case 'orbital': {
        const radius = 35 + particle.size * 5;
        const angle = particle.angle + t * 0.5;
        return {
          x: 50 + Math.cos(angle) * radius * (0.8 + Math.sin(t * 2) * 0.2),
          y: 50 + Math.sin(angle) * radius * (0.6 + Math.cos(t * 2) * 0.2),
          opacity: particle.opacity * (0.5 + Math.sin(t * 3) * 0.5) * intensity
        };
      }
      case 'rising': {
        const y = ((baseY + t * 20) % 100);
        return {
          x: baseX + Math.sin(t * 2 + particle.angle) * 5,
          y: 100 - y,
          opacity: particle.opacity * (1 - y / 100) * intensity
        };
      }
      case 'radial': {
        const distance = 20 + Math.sin(t * 2 + particle.angle) * 15;
        const angle = particle.angle + t * 0.3;
        return {
          x: 50 + Math.cos(angle) * distance,
          y: 50 + Math.sin(angle) * distance,
          opacity: particle.opacity * (0.6 + Math.sin(t * 4) * 0.4) * intensity
        };
      }
      case 'pulse': {
        const pulsePhase = (t * 2 + particle.delay) % (Math.PI * 2);
        const scale = 0.5 + Math.sin(pulsePhase) * 0.5;
        const distance = 30 * scale;
        return {
          x: 50 + Math.cos(particle.angle) * distance,
          y: 50 + Math.sin(particle.angle) * distance,
          opacity: particle.opacity * scale * intensity
        };
      }
      default:
        return { x: baseX, y: baseY, opacity: 0 };
    }
  };

  return (
    <g className="rafiki-particles" style={{ pointerEvents: 'none' }}>
      <defs>
        {/* Particle glow filter */}
        <filter id="particle-glow" x="-100%" y="-100%" width="300%" height="300%">
          <feGaussianBlur stdDeviation="1" result="blur" />
          <feComposite in="SourceGraphic" in2="blur" operator="over" />
        </filter>

        {/* Radial gradient for particles */}
        <radialGradient id="particle-gradient" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor={config.color} />
          <stop offset="100%" stopColor={config.color} stopOpacity="0" />
        </radialGradient>
      </defs>

      {/* Background glow ring */}
      <circle
        cx="50"
        cy="50"
        r="42"
        fill="none"
        stroke={glowColor}
        strokeWidth="0.5"
        opacity={0.3 * intensity}
        style={{ filter: 'blur(2px)' }}
      />

      {/* Particles */}
      {particles.map((particle) => {
        const pos = getParticlePosition(particle);
        return (
          <circle
            key={particle.id}
            cx={pos.x}
            cy={pos.y}
            r={particle.size * intensity}
            fill={config.color}
            opacity={pos.opacity}
            filter="url(#particle-glow)"
          />
        );
      })}

      {/* Center glow */}
      <circle
        cx="50"
        cy="50"
        r="5"
        fill="url(#particle-gradient)"
        opacity={0.3 * intensity * (0.5 + Math.sin(time * 2) * 0.5)}
      />

      {/* Orbital ring for thinking state */}
      {state === 'thinking' && (
        <ellipse
          cx="50"
          cy="50"
          rx="40"
          ry="25"
          fill="none"
          stroke={config.color}
          strokeWidth="0.5"
          strokeDasharray="3 5"
          opacity={0.4 * intensity}
          style={{
            transform: `rotate(${time * 20}deg)`,
            transformOrigin: '50px 50px'
          }}
        />
      )}

      {/* Pulse rings for listening state */}
      {state === 'listening' && (
        <>
          {[0, 1, 2].map((i) => {
            const pulseTime = (time * 0.5 + i * 0.33) % 1;
            const radius = 10 + pulseTime * 40;
            const opacity = (1 - pulseTime) * 0.5 * intensity;
            return (
              <circle
                key={`pulse-${i}`}
                cx="50"
                cy="50"
                r={radius}
                fill="none"
                stroke={config.color}
                strokeWidth="1"
                opacity={opacity}
              />
            );
          })}
        </>
      )}

      {/* Error state warning indicators */}
      {state === 'error' && (
        <g opacity={0.5 + Math.sin(time * 6) * 0.5}>
          <circle
            cx="50"
            cy="50"
            r="45"
            fill="none"
            stroke={config.color}
            strokeWidth="2"
            strokeDasharray="10 5"
            opacity={intensity}
          />
        </g>
      )}
    </g>
  );
};

export default ParticleEffects;
