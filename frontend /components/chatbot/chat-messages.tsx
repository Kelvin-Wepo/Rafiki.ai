"use client"

import { useEffect, useRef } from "react"
import type { Message } from "./chatbot-container"

interface ChatMessagesProps {
  messages: Message[]
  screenReaderMode?: boolean
}

export function ChatMessages({ messages, screenReaderMode = false }: ChatMessagesProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: screenReaderMode ? "auto" : "smooth" })
  }, [messages, screenReaderMode])

  return (
    <div
      id="chat-messages"
      className="flex-1 overflow-y-auto p-4 md:p-6 space-y-4"
      role="log"
      aria-label="Conversation history. New messages appear at the bottom."
      aria-live="polite"
      aria-atomic="false"
    >
      {messages.map((message, index) => (
        <div 
          key={message.id} 
          className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
          aria-label={`Message ${index + 1} of ${messages.length}`}
        >
          <div
            className={`max-w-[85%] md:max-w-[75%] rounded-2xl px-4 py-3 ${
              message.role === "user"
                ? "bg-chat-user-bg text-foreground rounded-br-md focus:outline-none focus:ring-2 focus:ring-primary"
                : "bg-chat-bot-bg border border-border text-foreground rounded-bl-md shadow-sm focus:outline-none focus:ring-2 focus:ring-primary"
            }`}
            role="article"
            tabIndex={0}
            aria-label={`${message.role === "user" ? "You" : "Rafiki"} said: ${message.content}`}
          >
            <p className="leading-relaxed break-words">{message.content}</p>
            {!screenReaderMode && (
              <time 
                className="block text-xs text-muted-foreground mt-2" 
                dateTime={message.timestamp.toISOString()}
                aria-label={`sent at ${message.timestamp.toLocaleTimeString()}`}
              >
                {message.timestamp.toLocaleTimeString([], {
                  hour: "2-digit",
                  minute: "2-digit",
                })}
              </time>
            )}
          </div>
        </div>
      ))}
      <div ref={messagesEndRef} aria-hidden="true" />
      
      {/* Screen reader announcement for new messages */}
      {screenReaderMode && messages.length > 0 && (
        <div className="sr-only" role="status" aria-live="assertive" aria-atomic="true">
          {messages[messages.length - 1].role === "bot" && 
            `New message from Rafiki: ${messages[messages.length - 1].content}`}
        </div>
      )}
    </div>
  )
}
