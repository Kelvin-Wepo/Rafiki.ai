/**
 * Alert Component - Kenya National Design System
 * Accessible alert/notification component
 */

import { type ReactNode, type HTMLAttributes } from 'react';
import { AlertCircle, CheckCircle, Info, AlertTriangle, X } from 'lucide-react';

export interface AlertProps extends HTMLAttributes<HTMLDivElement> {
  variant?: 'info' | 'success' | 'warning' | 'error';
  title?: string;
  children: ReactNode;
  onDismiss?: () => void;
  icon?: ReactNode;
}

const icons = {
  info: Info,
  success: CheckCircle,
  warning: AlertTriangle,
  error: AlertCircle,
};

const styles = {
  info: {
    container: 'bg-[var(--ke-info-bg)] border-[var(--ke-info-border)] text-[var(--ke-info)]',
    icon: 'text-[var(--ke-info)]',
  },
  success: {
    container: 'bg-[var(--ke-green-bg)] border-[var(--ke-green-border)] text-[var(--ke-green)]',
    icon: 'text-[var(--ke-green)]',
  },
  warning: {
    container: 'bg-[var(--ke-warning-bg)] border-[var(--ke-warning-border)] text-[var(--ke-warning)]',
    icon: 'text-[var(--ke-warning)]',
  },
  error: {
    container: 'bg-[var(--ke-red-bg)] border-[var(--ke-red-border)] text-[var(--ke-red)]',
    icon: 'text-[var(--ke-red)]',
  },
};

export function Alert({
  variant = 'info',
  title,
  children,
  onDismiss,
  icon,
  className = '',
  role = 'alert',
  ...props
}: AlertProps) {
  const IconComponent = icons[variant];
  const variantStyles = styles[variant];

  return (
    <div
      role={role}
      className={`
        relative flex gap-3 p-4 rounded-lg border
        ${variantStyles.container}
        ${className}
      `.replace(/\s+/g, ' ').trim()}
      {...props}
    >
      <div className={`flex-shrink-0 ${variantStyles.icon}`}>
        {icon || <IconComponent className="w-5 h-5" aria-hidden="true" />}
      </div>

      <div className="flex-1 min-w-0">
        {title && (
          <h4 className="font-semibold text-[var(--ke-gray-900)] mb-1">{title}</h4>
        )}
        <div className="text-sm text-[var(--ke-gray-700)]">{children}</div>
      </div>

      {onDismiss && (
        <button
          type="button"
          onClick={onDismiss}
          className="flex-shrink-0 p-1 rounded-md hover:bg-black/5 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--ke-gray-400)]"
          aria-label="Dismiss alert"
        >
          <X className="w-4 h-4" aria-hidden="true" />
        </button>
      )}
    </div>
  );
}

export default Alert;
