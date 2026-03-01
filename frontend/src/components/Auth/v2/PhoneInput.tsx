/**
 * PhoneInput Component
 * Phone number input with Kenya flag and +254 prefix
 * Validates Kenyan phone formats
 */

import { Phone, CheckCircle } from 'lucide-react';

interface PhoneInputProps {
  value: string;
  onChange: (value: string) => void;
  error?: string | null;
  disabled?: boolean;
}

export function PhoneInput({ value, onChange, error, disabled = false }: PhoneInputProps) {
  return (
    <div className="space-y-2">
      {/* Label */}
      <label 
        htmlFor="phone-input" 
        className="flex items-center gap-2 text-sm font-semibold"
        style={{ color: '#1E1E1E' }}
      >
        <Phone className="w-4 h-4" style={{ color: '#0F6B3E' }} />
        Phone Number
      </label>

      {/* Input Group */}
      <div 
        className={`
          flex items-stretch rounded-xl border-2 overflow-hidden transition-all
          ${error ? 'border-red-500' : 'border-gray-200 focus-within:border-[#0F6B3E]'}
          ${disabled ? 'opacity-60 cursor-not-allowed' : ''}
        `}
        style={{ backgroundColor: '#FAFBFA' }}
      >
        {/* Country Code */}
        <div 
          className="flex items-center gap-2 px-4 py-3 border-r border-gray-200"
          style={{ backgroundColor: '#F0F2F1' }}
        >
          <span className="text-xl" role="img" aria-label="Kenya flag">🇰🇪</span>
          <span className="font-medium text-gray-700">+254</span>
        </div>

        {/* Input Field */}
        <input
          id="phone-input"
          type="tel"
          inputMode="numeric"
          value={value}
          onChange={(e) => onChange(e.target.value.replace(/\D/g, ''))}
          placeholder="712 345 678"
          disabled={disabled}
          autoComplete="tel-national"
          aria-describedby={error ? 'phone-error' : 'phone-hint'}
          className="
            flex-1 px-4 py-3 text-base font-medium
            placeholder:text-gray-400 
            focus:outline-none
            disabled:cursor-not-allowed
          "
          style={{ 
            backgroundColor: 'transparent',
            color: '#1E1E1E'
          }}
        />
      </div>

      {/* Error Message */}
      {error && (
        <p id="phone-error" className="text-sm text-red-600 flex items-center gap-1">
          {error}
        </p>
      )}

      {/* Success Hint */}
      {!error && (
        <p id="phone-hint" className="text-xs flex items-center gap-1.5" style={{ color: '#6B7280' }}>
          <CheckCircle className="w-3.5 h-3.5" style={{ color: '#0F6B3E' }} />
          We support SMS and Voice OTP
        </p>
      )}
    </div>
  );
}

export default PhoneInput;
