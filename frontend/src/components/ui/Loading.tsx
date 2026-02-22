/**
 * Loading Components - Kenya National Design System
 * Spinner, Skeleton, and loading states
 */

import { type HTMLAttributes } from 'react';

// Spinner Component
export interface SpinnerProps extends HTMLAttributes<HTMLDivElement> {
  size?: 'sm' | 'md' | 'lg' | 'xl';
  color?: 'primary' | 'white' | 'gray';
}

const spinnerSizes = {
  sm: 'w-4 h-4 border-2',
  md: 'w-6 h-6 border-2',
  lg: 'w-8 h-8 border-3',
  xl: 'w-12 h-12 border-4',
};

const spinnerColors = {
  primary: 'border-[var(--ke-green)] border-t-transparent',
  white: 'border-white border-t-transparent',
  gray: 'border-[var(--ke-gray-300)] border-t-[var(--ke-gray-600)]',
};

export function Spinner({ size = 'md', color = 'primary', className = '', ...props }: SpinnerProps) {
  return (
    <div
      role="status"
      aria-label="Loading"
      className={`
        inline-block rounded-full animate-spin
        ${spinnerSizes[size]}
        ${spinnerColors[color]}
        ${className}
      `.replace(/\s+/g, ' ').trim()}
      {...props}
    >
      <span className="sr-only">Loading...</span>
    </div>
  );
}

// Skeleton Component
export interface SkeletonProps extends HTMLAttributes<HTMLDivElement> {
  variant?: 'text' | 'circular' | 'rectangular' | 'rounded';
  width?: string | number;
  height?: string | number;
  lines?: number;
}

export function Skeleton({
  variant = 'text',
  width,
  height,
  lines = 1,
  className = '',
  ...props
}: SkeletonProps) {
  const baseStyles = 'bg-[var(--ke-gray-200)] animate-pulse';

  const variants = {
    text: 'h-4 rounded',
    circular: 'rounded-full',
    rectangular: '',
    rounded: 'rounded-lg',
  };

  const style = {
    width: width ?? (variant === 'text' ? '100%' : undefined),
    height: height ?? (variant === 'circular' ? width : undefined),
  };

  if (lines > 1 && variant === 'text') {
    return (
      <div className={`space-y-2 ${className}`} {...props}>
        {Array.from({ length: lines }).map((_, i) => (
          <div
            key={i}
            className={`${baseStyles} ${variants.text}`}
            style={{
              ...style,
              width: i === lines - 1 ? '75%' : '100%',
            }}
          />
        ))}
      </div>
    );
  }

  return (
    <div
      className={`${baseStyles} ${variants[variant]} ${className}`}
      style={style}
      {...props}
    />
  );
}

// Loading Overlay
export interface LoadingOverlayProps {
  isLoading: boolean;
  message?: string;
  fullScreen?: boolean;
}

export function LoadingOverlay({ isLoading, message = 'Loading...', fullScreen = false }: LoadingOverlayProps) {
  if (!isLoading) return null;

  return (
    <div
      className={`
        flex flex-col items-center justify-center gap-4
        bg-white/80 backdrop-blur-sm
        ${fullScreen ? 'fixed inset-0 z-[var(--z-modal)]' : 'absolute inset-0 rounded-xl'}
      `}
      role="status"
      aria-live="polite"
    >
      <Spinner size="lg" />
      <p className="text-[var(--ke-gray-600)] font-medium">{message}</p>
    </div>
  );
}

// Page Loading State
export function PageLoader() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-[var(--ke-gray-50)]">
      <div className="text-center">
        <Spinner size="xl" />
        <p className="mt-4 text-[var(--ke-gray-600)]">Loading Rafiki...</p>
      </div>
    </div>
  );
}

// Card Skeleton
export function CardSkeleton() {
  return (
    <div className="bg-white rounded-xl border border-[var(--ke-gray-200)] p-6">
      <div className="flex items-center gap-4 mb-4">
        <Skeleton variant="circular" width={48} height={48} />
        <div className="flex-1">
          <Skeleton width="60%" height={20} className="mb-2" />
          <Skeleton width="40%" height={16} />
        </div>
      </div>
      <Skeleton lines={3} />
    </div>
  );
}

export default Spinner;
