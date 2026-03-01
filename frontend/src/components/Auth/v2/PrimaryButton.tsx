/**
 * PrimaryButton Component - IMPROVED
 * Full width CTA button with loading state
 * Height: 56px (increased), Rounded: 16px, Green background
 * Better hover effects and visual prominence
 */

import { ArrowRight, Loader2 } from 'lucide-react';
import type { ButtonHTMLAttributes } from 'react';

interface PrimaryButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  isLoading?: boolean;
  loadingText?: string;
}

export function PrimaryButton({
  children,
  isLoading = false,
  loadingText = 'Verifying…',
  disabled,
  ...props
}: PrimaryButtonProps) {
  return (
    <button
      disabled={disabled || isLoading}
      className="
        w-full h-[56px] flex items-center justify-center gap-3
        rounded-2xl font-bold text-base text-white
        transition-all duration-300 ease-out
        focus:outline-none focus:ring-4 focus:ring-[#0F6B3E]/30
        disabled:opacity-50 disabled:cursor-not-allowed
        hover:scale-[1.02] hover:-translate-y-0.5 active:scale-[0.98] active:translate-y-0
        group
      "
      style={{
        backgroundColor: disabled || isLoading ? '#6B9980' : '#0F6B3E',
        boxShadow: disabled || isLoading 
          ? '0 2px 8px rgba(15, 107, 62, 0.2)' 
          : '0 6px 20px rgba(15, 107, 62, 0.4), 0 2px 6px rgba(15, 107, 62, 0.2)'
      }}
      onMouseEnter={(e) => {
        if (!disabled && !isLoading) {
          e.currentTarget.style.backgroundColor = '#0A5A32';
          e.currentTarget.style.boxShadow = '0 8px 24px rgba(15, 107, 62, 0.5), 0 4px 8px rgba(15, 107, 62, 0.25)';
        }
      }}
      onMouseLeave={(e) => {
        if (!disabled && !isLoading) {
          e.currentTarget.style.backgroundColor = '#0F6B3E';
          e.currentTarget.style.boxShadow = '0 6px 20px rgba(15, 107, 62, 0.4), 0 2px 6px rgba(15, 107, 62, 0.2)';
        }
      }}
      {...props}
    >
      {isLoading ? (
        <>
          <Loader2 className="w-5 h-5 animate-spin" />
          <span>{loadingText}</span>
        </>
      ) : (
        <>
          <span>{children}</span>
          <ArrowRight className="w-5 h-5 transition-transform duration-200 group-hover:translate-x-1" />
        </>
      )}
    </button>
  );
}

export default PrimaryButton;
