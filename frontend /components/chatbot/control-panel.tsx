"use client"

import { useState, useEffect, type FormEvent } from "react"
import { Mic, Square, Send } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import type { AudioState } from "./chatbot-container"

interface ControlPanelProps {
  audioState: AudioState
  onVoiceToggle: () => void
  onTextSubmit: (text: string) => void
  reduceMotion?: boolean
}

export function ControlPanel({ audioState, onVoiceToggle, onTextSubmit, reduceMotion = false }: ControlPanelProps) {
  const [inputText, setInputText] = useState("")

  // Handle keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Space bar to toggle voice
      if (e.code === "Space" && e.target === document.body) {
        e.preventDefault()
        onVoiceToggle()
      }
    }

    window.addEventListener("keydown", handleKeyDown)
    return () => window.removeEventListener("keydown", handleKeyDown)
  }, [onVoiceToggle])

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    if (inputText.trim()) {
      onTextSubmit(inputText)
      setInputText("")
    }
  }

  const isActive = audioState !== "idle"
  const isListening = audioState === "listening"
  const isSpeaking = audioState === "speaking"

  const getStatusText = () => {
    switch (audioState) {
      case "listening":
        return "Listening..."
      case "speaking":
        return "Speaking..."
      case "connecting":
        return "Connecting..."
      default:
        return "Ready to listen"
    }
  }

  const getButtonLabel = () => {
    if (isActive) return "Stop conversation (or press Space)"
    return "Start speaking (or press Space)"
  }

  const animationClass = reduceMotion ? "" : "transition-all duration-300"

  return (
    <div
      className="border-t border-border bg-card p-4 md:p-6 space-y-4"
      role="region"
      aria-label="Voice and text controls"
    >
      {/* Voice Button - Large and Prominent */}
      <div className="flex flex-col items-center gap-3">
        <Button
          onClick={onVoiceToggle}
          className={`w-20 h-20 md:w-24 md:h-24 rounded-full ${animationClass} shadow-lg ${
            isListening
              ? "bg-status-listening hover:bg-status-listening/90 " + (reduceMotion ? "" : "animate-pulse")
              : isSpeaking
                ? "bg-status-speaking hover:bg-status-speaking/90"
                : "bg-status-idle hover:bg-status-idle/90"
          } text-primary-foreground focus:outline-none focus:ring-4 focus:ring-offset-2`}
          aria-label={getButtonLabel()}
          aria-pressed={isActive}
          title="Press Space to start/stop voice input"
        >
          {isActive ? (
            <Square className="w-8 h-8 md:w-10 md:h-10" aria-hidden="true" />
          ) : (
            <Mic className="w-8 h-8 md:w-10 md:h-10" aria-hidden="true" />
          )}
        </Button>

        {/* Status Indicator */}
        <div className="flex items-center gap-2" role="status" aria-live="polite" aria-atomic="true">
          <span
            className={`w-3 h-3 rounded-full ${
              isListening
                ? "bg-status-listening " + (reduceMotion ? "" : "animate-pulse")
                : isSpeaking
                  ? "bg-status-speaking " + (reduceMotion ? "" : "animate-pulse")
                  : "bg-muted-foreground"
            }`}
            aria-hidden="true"
          />
          <span className="text-sm font-medium text-muted-foreground">{getStatusText()}</span>
        </div>
      </div>

      {/* Text Input - Fallback for users who prefer typing */}
      <form onSubmit={handleSubmit} className="flex gap-2">
        <label htmlFor="message-input" className="sr-only">
          Type your message
        </label>
        <Input
          id="message-input"
          type="text"
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          placeholder="Or type your message here..."
          className="flex-1 min-h-[48px] text-base focus:outline-none focus:ring-2 focus:ring-primary"
          disabled={isActive}
          aria-describedby="input-help"
          aria-label="Message input field"
        />
        <Button
          type="submit"
          disabled={!inputText.trim() || isActive}
          className="min-w-[48px] min-h-[48px] bg-primary hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary"
          aria-label="Send message (or press Enter)"
          title="Send message"
        >
          <Send className="w-5 h-5" aria-hidden="true" />
        </Button>
      </form>
      <p id="input-help" className="sr-only">
        Press Enter or click Send to submit your message. You can press Space anywhere to start/stop voice input.
      </p>
    </div>
  )
}
