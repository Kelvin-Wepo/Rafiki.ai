/**
 * ErrorMessage Component
 * Error display with icon
 */

import { AlertCircle } from 'lucide-react';

interface ErrorMessageProps {
  message: string;
}

export function ErrorMessage({ message }: ErrorMessageProps) {
  if (!message) return null;

  return (
    <div 
      className="flex items-start gap-2 p-3 bg-red-50 border border-red-200 rounded-xl text-red-700 text-sm"
      role="alert"
      aria-live="polite"
    >
      <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
      <span>{message}</span>
    </div>
  );
}

export default ErrorMessage;
