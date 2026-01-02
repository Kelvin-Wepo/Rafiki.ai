"use client"

import { Settings } from "lucide-react"
import { Button } from "@/components/ui/button"

interface HeaderProps {
  onAccessibilityClick: () => void
}

export function Header({ onAccessibilityClick }: HeaderProps) {
  return (
    <header className="bg-primary text-primary-foreground px-4 py-4 md:px-6" role="banner">
      <div className="flex items-center justify-between gap-4">
        {/* Government Logo */}
        <div className="flex items-center gap-3">
          <div
            className="w-12 h-12 bg-primary-foreground/10 rounded-lg flex items-center justify-center"
            aria-hidden="true"
          >
            <svg viewBox="0 0 48 48" className="w-8 h-8" fill="currentColor" aria-hidden="true">
              <path d="M24 4L4 14v4h40v-4L24 4zm0 4.5L38 14H10l14-5.5zM8 20v18h6V20H8zm13 0v18h6V20h-6zm13 0v18h6V20h-6zM4 42v4h40v-4H4z" />
            </svg>
          </div>
          <div>
            <h1 className="text-xl md:text-2xl font-bold leading-tight">Government Services</h1>
            <p className="text-sm text-primary-foreground/80 hidden sm:block">Voice-Enabled Assistant</p>
          </div>
        </div>

        {/* Accessibility Controls Button */}
        <Button
          variant="ghost"
          size="lg"
          onClick={onAccessibilityClick}
          className="text-primary-foreground hover:bg-primary-foreground/10 min-w-[44px] min-h-[44px]"
          aria-label="Open accessibility settings"
        >
          <Settings className="w-6 h-6" aria-hidden="true" />
          <span className="sr-only md:not-sr-only md:ml-2">Accessibility</span>
        </Button>
      </div>
    </header>
  )
}
