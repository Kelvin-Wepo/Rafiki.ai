"use client"

import { X } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { Slider } from "@/components/ui/slider"
import { Checkbox } from "@/components/ui/checkbox"

interface AccessibilityPanelProps {
  textSize: "normal" | "large" | "xlarge"
  onTextSizeChange: (size: "normal" | "large" | "xlarge") => void
  speechRate: number
  onSpeechRateChange: (rate: number) => void
  highContrast?: boolean
  onHighContrastChange?: (enabled: boolean) => void
  screenReaderMode?: boolean
  onScreenReaderModeChange?: (enabled: boolean) => void
  reduceMotion?: boolean
  onReduceMotionChange?: (enabled: boolean) => void
  onClose: () => void
}

export function AccessibilityPanel({
  textSize,
  onTextSizeChange,
  speechRate,
  onSpeechRateChange,
  highContrast = false,
  onHighContrastChange,
  screenReaderMode = false,
  onScreenReaderModeChange,
  reduceMotion = false,
  onReduceMotionChange,
  onClose,
}: AccessibilityPanelProps) {
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Escape") {
      onClose()
    }
  }

  return (
    <div 
      className={`${highContrast ? 'bg-black text-white border-2 border-white' : 'bg-secondary border-b border-border'} p-4 md:p-6`} 
      role="region" 
      aria-label="Accessibility settings"
      onKeyDown={handleKeyDown}
    >
      <div className="flex items-center justify-between mb-4">
        <h2 className={`text-lg font-semibold ${highContrast ? 'text-white' : ''}`}>
          Accessibility Settings
        </h2>
        <Button
          variant="ghost"
          size="sm"
          onClick={onClose}
          className={`min-w-[44px] min-h-[44px] ${highContrast ? 'bg-white text-black hover:bg-gray-200' : ''}`}
          aria-label="Close accessibility settings"
          title="Press Escape to close"
        >
          <X className="w-5 h-5" aria-hidden="true" />
        </Button>
      </div>

      <div className="space-y-6">
        {/* Text Size */}
        <div className="space-y-3">
          <Label className={`text-base font-medium ${highContrast ? 'text-white' : ''}`}>
            Text Size
          </Label>
          <div className="flex gap-2 flex-wrap" role="radiogroup" aria-label="Text size options">
            {(["normal", "large", "xlarge"] as const).map((size) => (
              <Button
                key={size}
                variant={textSize === size ? "default" : "outline"}
                onClick={() => onTextSizeChange(size)}
                className={`min-h-[44px] capitalize ${highContrast && textSize === size ? 'bg-white text-black' : ''} ${highContrast && textSize !== size ? 'bg-black text-white border-white' : ''}`}
                role="radio"
                aria-checked={textSize === size}
                aria-label={`Set text size to ${size}`}
              >
                {size === "xlarge" ? "Extra Large" : size}
              </Button>
            ))}
          </div>
        </div>

        {/* Speech Rate */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <Label htmlFor="speech-rate" className={`text-base font-medium ${highContrast ? 'text-white' : ''}`}>
              Speech Rate
            </Label>
            <span 
              className={`text-sm ${highContrast ? 'text-white' : 'text-muted-foreground'}`} 
              aria-live="polite"
              aria-label={`Current speech rate: ${speechRate} times normal speed`}
            >
              {speechRate}x
            </span>
          </div>
          <Slider
            id="speech-rate"
            min={0.5}
            max={2}
            step={0.25}
            value={[speechRate]}
            onValueChange={([value]) => onSpeechRateChange(value)}
            className="w-full"
            aria-valuemin={0.5}
            aria-valuemax={2}
            aria-valuenow={speechRate}
            aria-valuetext={`${speechRate} times normal speed`}
            aria-label="Adjust speech rate from 0.5x to 2x speed"
          />
          <div className="flex justify-between text-xs text-muted-foreground">
            <span>Slower (0.5x)</span>
            <span>Faster (2x)</span>
          </div>
        </div>

        {/* High Contrast Mode */}
        <div className="space-y-3">
          <div className="flex items-center gap-3 min-h-[44px]">
            <Checkbox
              id="high-contrast"
              checked={highContrast}
              onCheckedChange={(checked) => onHighContrastChange?.(checked === true)}
              aria-label="Enable high contrast mode for better visibility"
            />
            <Label 
              htmlFor="high-contrast" 
              className={`text-base font-medium cursor-pointer ${highContrast ? 'text-white' : ''}`}
            >
              High Contrast Mode
            </Label>
          </div>
          <p className={`text-sm ${highContrast ? 'text-gray-300' : 'text-muted-foreground'}`}>
            Increases contrast for easier reading
          </p>
        </div>

        {/* Screen Reader Mode */}
        <div className="space-y-3">
          <div className="flex items-center gap-3 min-h-[44px]">
            <Checkbox
              id="screen-reader"
              checked={screenReaderMode}
              onCheckedChange={(checked) => onScreenReaderModeChange?.(checked === true)}
              aria-label="Enable screen reader optimization"
            />
            <Label 
              htmlFor="screen-reader" 
              className={`text-base font-medium cursor-pointer ${highContrast ? 'text-white' : ''}`}
            >
              Screen Reader Optimization
            </Label>
          </div>
          <p className={`text-sm ${highContrast ? 'text-gray-300' : 'text-muted-foreground'}`}>
            Optimizes interface for screen readers and verbal feedback
          </p>
        </div>

        {/* Reduce Motion */}
        <div className="space-y-3">
          <div className="flex items-center gap-3 min-h-[44px]">
            <Checkbox
              id="reduce-motion"
              checked={reduceMotion}
              onCheckedChange={(checked) => onReduceMotionChange?.(checked === true)}
              aria-label="Reduce motion and animations"
            />
            <Label 
              htmlFor="reduce-motion" 
              className={`text-base font-medium cursor-pointer ${highContrast ? 'text-white' : ''}`}
            >
              Reduce Motion
            </Label>
          </div>
          <p className={`text-sm ${highContrast ? 'text-gray-300' : 'text-muted-foreground'}`}>
            Minimizes animations and transitions
          </p>
        </div>

        {/* Keyboard Shortcuts Help */}
        <div className={`${highContrast ? 'bg-gray-900 border-white' : 'bg-muted'} border rounded-lg p-4`}>
          <h3 className={`font-semibold mb-3 ${highContrast ? 'text-white' : ''}`}>Keyboard Shortcuts</h3>
          <ul className="space-y-2 text-sm">
            <li><kbd className={`px-2 py-1 rounded ${highContrast ? 'bg-white text-black' : 'bg-background'}`}>Space</kbd> - Start/Stop voice</li>
            <li><kbd className={`px-2 py-1 rounded ${highContrast ? 'bg-white text-black' : 'bg-background'}`}>Tab</kbd> - Navigate controls</li>
            <li><kbd className={`px-2 py-1 rounded ${highContrast ? 'bg-white text-black' : 'bg-background'}`}>Enter</kbd> - Submit message</li>
            <li><kbd className={`px-2 py-1 rounded ${highContrast ? 'bg-white text-black' : 'bg-background'}`}>Esc</kbd> - Close panel</li>
          </ul>
        </div>
      </div>
    </div>
  )
}
          <div className="flex justify-between text-xs text-muted-foreground">
            <span>Slower</span>
            <span>Faster</span>
          </div>
        </div>

        {/* Keyboard Shortcuts Info */}
        <div className="bg-card rounded-lg p-4 border border-border">
          <h3 className="font-medium mb-2">Keyboard Shortcuts</h3>
          <ul className="text-sm text-muted-foreground space-y-1">
            <li>
              <kbd className="px-2 py-0.5 bg-muted rounded text-xs font-mono">Space</kbd> — Toggle voice input
            </li>
            <li>
              <kbd className="px-2 py-0.5 bg-muted rounded text-xs font-mono">Escape</kbd> — Stop voice input
            </li>
            <li>
              <kbd className="px-2 py-0.5 bg-muted rounded text-xs font-mono">Tab</kbd> — Navigate between elements
            </li>
          </ul>
        </div>
      </div>
    </div>
  )
}
