/**
 * PhoneInput Component
 * Kenyan phone number input with country code prefix
 */

import { Phone } from 'lucide-react';

interface PhoneInputProps {
  value: string;
  onChange: (value: string) => void;
  error?: boolean;
  disabled?: boolean;
  placeholder?: string;
}

export function PhoneInput({ 
  value, 
  onChange, 
  error = false, 
  disabled = false,
  placeholder = "712 345 678"
}: PhoneInputProps) {
  return (
    <div className="space-y-2">
      <label htmlFor="phone" className="flex items-center gap-2 text-sm font-semibold text-gray-700">
        <Phone className="w-4 h-4 text-[#006600]" />
        Phone Number
      </label>
      
      <div className="flex">
        {/* Country Code Prefix */}
        <div className="flex items-center gap-2 px-4 py-3 bg-gray-50 border border-r-0 border-gray-300 rounded-l-xl text-gray-600 font-medium">
          <span className="text-lg" role="img" aria-label="Kenya flag">🇰🇪</span>
          <span>+254</span>
        </div>
        
        {/* Phone Input */}
        <input
          type="tel"
          id="phone"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          disabled={disabled}
          autoComplete="tel"
          className={`
            flex-1 px-4 py-3 
            border border-gray-300 rounded-r-xl
            text-gray-900 text-base font-medium
            placeholder:text-gray-400
            focus:outline-none focus:ring-2 focus:ring-[#006600]/20 focus:border-[#006600]
            disabled:bg-gray-100 disabled:cursor-not-allowed
            transition-all duration-200
            ${error ? 'border-red-500 focus:ring-red-500/20 focus:border-red-500' : ''}
          `}
          aria-describedby={error ? 'phone-error' : undefined}
        />
      </div>
    </div>
  );
}

export default PhoneInput;
