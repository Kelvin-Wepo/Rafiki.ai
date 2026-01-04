"use client"

import { useState, useEffect, useRef } from "react"

type AvatarState = "idle" | "listening" | "speaking" | "thinking"

interface TalkingAvatarProps {
  isListening?: boolean
  isSpeaking?: boolean
  isThinking?: boolean
  size?: "small" | "medium" | "large"
}

export function TalkingAvatar({
  isListening = false,
  isSpeaking = false,
  isThinking = false,
  size = "large",
}: TalkingAvatarProps) {
  const [currentState, setCurrentState] = useState<AvatarState>("idle")
  const [mouthOpen, setMouthOpen] = useState(false)
  const animationRef = useRef<NodeJS.Timeout | null>(null)

  // Determine avatar state
  useEffect(() => {
    if (isSpeaking) {
      setCurrentState("speaking")
    } else if (isListening) {
      setCurrentState("listening")
    } else if (isThinking) {
      setCurrentState("thinking")
    } else {
      setCurrentState("idle")
    }
  }, [isListening, isSpeaking, isThinking])

  // Lip sync animation when speaking
  useEffect(() => {
    if (currentState === "speaking") {
      const animateMouth = () => {
        setMouthOpen((prev) => !prev)
        const nextInterval = Math.random() * 120 + 80
        animationRef.current = setTimeout(animateMouth, nextInterval)
      }
      animateMouth()
    } else {
      setMouthOpen(false)
      if (animationRef.current) {
        clearTimeout(animationRef.current)
      }
    }

    return () => {
      if (animationRef.current) {
        clearTimeout(animationRef.current)
      }
    }
  }, [currentState])

  const sizeClasses = {
    small: "w-16 h-16",
    medium: "w-24 h-24",
    large: "w-32 h-32",
  }

  const getStatusText = () => {
    switch (currentState) {
      case "speaking":
        return "Assistant is speaking"
      case "listening":
        return "Listening to you"
      case "thinking":
        return "Processing..."
      default:
        return "Ready to help"
    }
  }

  const ringColor = {
    speaking: "stroke-status-speaking",
    listening: "stroke-status-listening",
    thinking: "stroke-amber-500",
    idle: "stroke-transparent",
  }

  return (
    <div className="flex flex-col items-center gap-2">
      <div className={`relative ${sizeClasses[size]}`}>
        <svg viewBox="0 0 200 200" className="w-full h-full" role="img" aria-label="Virtual assistant avatar">
          <defs>
            <linearGradient id="bgGradient" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#10B981" />
              <stop offset="100%" stopColor="#059669" />
            </linearGradient>
            <linearGradient id="skinTone" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#8B5A3C" />
              <stop offset="100%" stopColor="#6B4423" />
            </linearGradient>
          </defs>

          {/* Background */}
          <circle cx="100" cy="100" r="95" fill="url(#bgGradient)" />

          {/* Hair */}
          <ellipse cx="100" cy="75" rx="65" ry="55" fill="#1a1a1a" />
          <ellipse cx="100" cy="85" rx="60" ry="50" fill="#1a1a1a" />
          <path d="M45 70 Q40 90 35 120" stroke="#2a2a2a" strokeWidth="4" fill="none" />
          <path d="M55 65 Q48 85 42 115" stroke="#2a2a2a" strokeWidth="4" fill="none" />
          <path d="M145 65 Q152 85 158 115" stroke="#2a2a2a" strokeWidth="4" fill="none" />
          <path d="M155 70 Q160 90 165 120" stroke="#2a2a2a" strokeWidth="4" fill="none" />

          {/* Face */}
          <ellipse cx="100" cy="105" rx="50" ry="55" fill="url(#skinTone)" />

          {/* Ears & Earrings */}
          <ellipse cx="52" cy="105" rx="8" ry="12" fill="#8B5A3C" />
          <ellipse cx="148" cy="105" rx="8" ry="12" fill="#8B5A3C" />
          <circle cx="52" cy="115" r="4" fill="#FFD700" />
          <circle cx="148" cy="115" r="4" fill="#FFD700" />

          {/* Eyebrows */}
          <path d="M70 82 Q80 78 90 82" stroke="#1a1a1a" strokeWidth="2.5" fill="none" />
          <path d="M110 82 Q120 78 130 82" stroke="#1a1a1a" strokeWidth="2.5" fill="none" />

          {/* Eyes */}
          <ellipse cx="80" cy="95" rx="12" ry="8" fill="white" />
          <ellipse cx="120" cy="95" rx="12" ry="8" fill="white" />
          <circle cx="80" cy="95" r="5" fill="#3D2314" />
          <circle cx="120" cy="95" r="5" fill="#3D2314" />
          <circle cx="80" cy="95" r="2.5" fill="#1a1a1a" />
          <circle cx="120" cy="95" r="2.5" fill="#1a1a1a" />
          <circle cx="82" cy="93" r="1.5" fill="white" />
          <circle cx="122" cy="93" r="1.5" fill="white" />

          {/* Nose */}
          <path d="M100 100 Q95 115 92 118 Q100 122 108 118 Q105 115 100 100" fill="#7A4A2A" opacity="0.6" />

          {/* Mouth - animated */}
          <g>
            {mouthOpen ? (
              <>
                <ellipse cx="100" cy="135" rx="15" ry="10" fill="#8B0000" />
                <ellipse cx="100" cy="132" rx="12" ry="4" fill="white" opacity="0.9" />
                <path d="M88 138 Q100 142 112 138" fill="#CC6666" />
              </>
            ) : (
              <>
                <path d="M85 132 Q100 142 115 132" stroke="#5C3317" strokeWidth="3" fill="none" />
                <path d="M88 132 Q100 138 112 132" fill="#CC6666" opacity="0.5" />
              </>
            )}
          </g>

          {/* Cheek highlights */}
          <ellipse cx="65" cy="115" rx="8" ry="5" fill="#D4A574" opacity="0.3" />
          <ellipse cx="135" cy="115" rx="8" ry="5" fill="#D4A574" opacity="0.3" />

          {/* Neck */}
          <path d="M80 155 L80 180 L120 180 L120 155" fill="url(#skinTone)" />

          {/* Clothing */}
          <path d="M60 175 Q100 165 140 175 L150 200 L50 200 Z" fill="#E53E3E" />
          <path d="M75 175 Q100 170 125 175 L120 200 L80 200 Z" fill="#DD6B20" />

          {/* Necklace */}
          <path d="M75 160 Q100 170 125 160" stroke="#FFD700" strokeWidth="2" fill="none" />
          <circle cx="100" cy="168" r="4" fill="#FFD700" />

          {/* Status ring */}
          <circle
            cx="100"
            cy="100"
            r="95"
            fill="none"
            className={`${ringColor[currentState]} transition-all duration-300 ${
              currentState !== "idle" ? "animate-pulse" : ""
            }`}
            strokeWidth="4"
          />
        </svg>

        {/* Pulse rings for active states */}
        {(currentState === "speaking" || currentState === "listening") && (
          <div className="absolute inset-0 pointer-events-none">
            <span
              className={`absolute inset-0 rounded-full border-2 animate-ping opacity-30 ${
                currentState === "speaking" ? "border-status-speaking" : "border-status-listening"
              }`}
            />
          </div>
        )}
      </div>

      {/* Status text - visually hidden but available for screen readers */}
      <p className="text-xs text-muted-foreground text-center" aria-live="polite">
        {getStatusText()}
      </p>
    </div>
  )
}
