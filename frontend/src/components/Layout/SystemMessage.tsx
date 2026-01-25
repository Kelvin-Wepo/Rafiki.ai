/**
 * SystemMessage Component
 * 
 * A polished, accessible dialog for system messages, errors, and guidance.
 * Matches the Rafiki design language: calm, professional, government-grade.
 * 
 * Features:
 * - Glassmorphism design with subtle blur
 * - Smooth fade-in animation (respects prefers-reduced-motion)
 * - Clear visual hierarchy between message and guidance
 * - Accessible with aria-live and proper contrast
 */

import { useEffect, useState } from 'react';
import { Info, AlertCircle, CheckCircle, XCircle, X } from 'lucide-react';

export type MessageType = 'info' | 'warning' | 'error' | 'success';

interface SystemMessageProps {
  /** Main message text */
  message: string;
  /** Optional secondary guidance text */
  guidance?: string;
  /** Message type determines icon and accent color */
  type?: MessageType;
  /** Whether the message can be dismissed */
  dismissible?: boolean;
  /** Callback when dismissed */
  onDismiss?: () => void;
  /** Additional CSS classes */
  className?: string;
}

const typeConfig = {
  info: {
    icon: Info,
    accentColor: 'from-cyan-500/20 to-blue-500/20',
    borderColor: 'border-cyan-500/20',
    iconColor: 'text-cyan-400',
    dotColor: 'bg-cyan-400',
  },
  warning: {
    icon: AlertCircle,
    accentColor: 'from-amber-500/20 to-orange-500/20',
    borderColor: 'border-amber-500/20',
    iconColor: 'text-amber-400',
    dotColor: 'bg-amber-400',
  },
  error: {
    icon: XCircle,
    accentColor: 'from-red-500/20 to-rose-500/20',
    borderColor: 'border-red-500/20',
    iconColor: 'text-red-400',
    dotColor: 'bg-red-400',
  },
  success: {
    icon: CheckCircle,
    accentColor: 'from-emerald-500/20 to-teal-500/20',
    borderColor: 'border-emerald-500/20',
    iconColor: 'text-emerald-400',
    dotColor: 'bg-emerald-400',
  },
};

export default function SystemMessage({
  message,
  guidance,
  type = 'info',
  dismissible = true,
  onDismiss,
  className = '',
}: SystemMessageProps) {
  const [isVisible, setIsVisible] = useState(false);
  const [isExiting, setIsExiting] = useState(false);

  const config = typeConfig[type];
  const Icon = config.icon;

  // Trigger entrance animation on mount
  useEffect(() => {
    // Small delay to ensure CSS transition works
    const timer = setTimeout(() => setIsVisible(true), 10);
    return () => clearTimeout(timer);
  }, []);

  const handleDismiss = () => {
    setIsExiting(true);
    // Wait for exit animation before calling onDismiss
    setTimeout(() => {
      onDismiss?.();
    }, 200);
  };

  return (
    <div
      role="status"
      aria-live="polite"
      aria-atomic="true"
      className={`
        w-full max-w-2xl mx-auto px-4
        ${className}
      `}
    >
      <div
        className={`
          relative overflow-hidden
          bg-slate-900/60 backdrop-blur-xl
          border ${config.borderColor}
          rounded-2xl
          shadow-lg shadow-black/20
          transition-all duration-300 ease-out
          motion-safe:transform
          ${isVisible && !isExiting 
            ? 'opacity-100 translate-y-0' 
            : 'opacity-0 translate-y-2'
          }
        `}
      >
        {/* Subtle gradient accent at top */}
        <div 
          className={`
            absolute top-0 left-0 right-0 h-[2px]
            bg-gradient-to-r ${config.accentColor}
          `}
        />

        {/* Glass highlight effect */}
        <div className="absolute inset-0 bg-gradient-to-b from-white/[0.03] to-transparent pointer-events-none" />

        {/* Content */}
        <div className="relative p-4 sm:p-5">
          <div className="flex items-start gap-3">
            {/* Status indicator */}
            <div className="flex-shrink-0 mt-0.5">
              <div className="relative">
                {/* Subtle glow behind icon */}
                <div 
                  className={`
                    absolute inset-0 rounded-full blur-md opacity-30
                    ${config.dotColor}
                  `}
                />
                <Icon 
                  className={`
                    relative w-5 h-5 ${config.iconColor}
                    transition-colors duration-200
                  `}
                  strokeWidth={1.5}
                />
              </div>
            </div>

            {/* Message content */}
            <div className="flex-1 min-w-0 space-y-1.5">
              {/* Primary message */}
              <p className="text-slate-200 text-sm sm:text-base font-medium leading-relaxed">
                {message}
              </p>

              {/* Secondary guidance */}
              {guidance && (
                <p className="text-slate-400 text-xs sm:text-sm leading-relaxed">
                  {guidance}
                </p>
              )}
            </div>

            {/* Dismiss button */}
            {dismissible && onDismiss && (
              <button
                onClick={handleDismiss}
                className={`
                  flex-shrink-0 p-1.5 -m-1.5
                  text-slate-500 hover:text-slate-300
                  rounded-lg
                  hover:bg-slate-700/50
                  transition-all duration-200
                  focus:outline-none focus:ring-2 focus:ring-slate-500/50
                `}
                aria-label="Dismiss message"
              >
                <X className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

/**
 * Inline variant for smaller, less prominent messages
 */
export function SystemMessageInline({
  message,
  type = 'info',
  className = '',
}: Pick<SystemMessageProps, 'message' | 'type' | 'className'>) {
  const config = typeConfig[type];
  const Icon = config.icon;

  return (
    <div
      role="status"
      aria-live="polite"
      className={`
        inline-flex items-center gap-2
        px-3 py-2
        bg-slate-800/40 backdrop-blur-sm
        border ${config.borderColor}
        rounded-xl
        text-sm text-slate-300
        ${className}
      `}
    >
      <Icon className={`w-4 h-4 ${config.iconColor}`} strokeWidth={1.5} />
      <span>{message}</span>
    </div>
  );
}
