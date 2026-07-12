/**
 * AuthInput Component
 * Styled input with floating label, icon support, and validation states
 */

import React, { useState, useId } from 'react';
import { Eye, EyeOff, AlertCircle } from 'lucide-react';

interface AuthInputProps {
  label: string;
  placeholder: string;
  type?: string;
  icon?: React.ReactNode;
  value: string;
  onChange: (val: string) => void;
  error?: string;
  rightElement?: React.ReactNode;
  showPasswordToggle?: boolean;
  autoComplete?: string;
  required?: boolean;
  /** Render the label above the input (redesign style) instead of floating */
  staticLabel?: boolean;
  'aria-describedby'?: string;
  /** Ref to the underlying input, e.g. for moving focus to the first invalid field */
  inputRef?: React.Ref<HTMLInputElement>;
}

export function AuthInput({
  label,
  placeholder,
  type = 'text',
  icon,
  value,
  onChange,
  error,
  rightElement,
  showPasswordToggle = false,
  autoComplete,
  required = false,
  staticLabel = false,
  'aria-describedby': ariaDescribedBy,
  inputRef,
}: AuthInputProps) {
  const [showPassword, setShowPassword] = useState(false);
  const inputId = useId();
  const errorId = useId();

  const inputType = showPasswordToggle 
    ? (showPassword ? 'text' : 'password')
    : type;

  const hasError = Boolean(error);

  return (
    <div className="w-full">
      {staticLabel && (
        <label htmlFor={inputId} className="auth-field-label">
          {label}
        </label>
      )}
      <div className={`auth-input-wrapper ${staticLabel ? 'static-label' : ''}`}>
        <input
          ref={inputRef}
          id={inputId}
          type={inputType}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          autoComplete={autoComplete}
          required={required}
          aria-invalid={hasError}
          aria-describedby={hasError ? errorId : ariaDescribedBy}
          className={`auth-input ${hasError ? 'has-error' : ''}`}
        />
        
        {icon && (
          <span className="auth-input-icon" aria-hidden="true">
            {icon}
          </span>
        )}
        
        {!staticLabel && (
          <label htmlFor={inputId} className="auth-label">
            {label}
          </label>
        )}

        {showPasswordToggle && (
          <button
            type="button"
            className="auth-input-toggle"
            onClick={() => setShowPassword(!showPassword)}
            aria-label={showPassword ? 'Hide password' : 'Show password'}
          >
            {showPassword ? (
              <EyeOff size={20} aria-hidden="true" />
            ) : (
              <Eye size={20} aria-hidden="true" />
            )}
          </button>
        )}

        {rightElement && !showPasswordToggle && (
          <div className="auth-input-toggle">
            {rightElement}
          </div>
        )}
      </div>

      {hasError && (
        <div id={errorId} className="auth-error" role="alert">
          <AlertCircle size={14} aria-hidden="true" />
          <span>{error}</span>
        </div>
      )}
    </div>
  );
}

export default AuthInput;
