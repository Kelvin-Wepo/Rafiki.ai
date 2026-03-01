/**
 * PrimaryButton Component
 * Main action button with loading state
 */

import { ArrowRight, Loader2 } from 'lucide-react';
import type { ButtonHTMLAttributes, ReactNode } from 'react';

interface PrimaryButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  children: ReactNode;
  isLoading?: boolean;
  loadingText?: string;
  showArrow?: boolean;
  variant?: 'primary' | 'secondary' | 'outline';
  size?: 'sm' | 'md' | 'lg';
}

export function PrimaryButton({
  children,
  isLoading = false,
  loadingText = 'Please wait...',
  showArrow = true,
  variant = 'primary',
  size = 'lg',
  disabled,
  className = '',
  ...props
}: PrimaryButtonProps) {
  const baseStyles = `
    inline-flex items-center justify-center gap-2
    font-semibold rounded-xl
    transition-all duration-200
    focus:outline-none focus:ring-2 focus:ring-offset-2
    disabled:opacity-50 disabled:cursor-not-allowed
  `;

  const sizeStyles = {
    sm: 'px-4 py-2 text-sm',
    md: 'px-5 py-2.5 text-base',
    lg: 'w-full px-6 py-3.5 text-base',
  };

  const variantStyles = {
    primary: `
      bg-gradient-to-r from-[#006600] to-[#008800]
      text-white
      hover:from-[#005500] hover:to-[#007700]
      focus:ring-[#006600]/50
      shadow-lg shadow-[#006600]/25
      hover:shadow-xl hover:shadow-[#006600]/30
      active:scale-[0.98]
    `,
    secondary: `
      bg-gray-100
      text-gray-700
      hover:bg-gray-200
      focus:ring-gray-500/50
    `,
    outline: `
      bg-transparent
      border-2 border-[#006600]
      text-[#006600]
      hover:bg-[#006600]/5
      focus:ring-[#006600]/50
    `,
  };

  return (
    <button
      disabled={disabled || isLoading}
      className={`${baseStyles} ${sizeStyles[size]} ${variantStyles[variant]} ${className}`}
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
          {showArrow && <ArrowRight className="w-5 h-5" />}
        </>
      )}
    </button>
  );
}

export default PrimaryButton;
