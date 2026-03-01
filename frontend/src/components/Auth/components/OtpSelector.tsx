/**
 * OtpSelector Component
 * Toggle buttons for OTP delivery method selection
 */

import { MessageSquare, PhoneCall, Zap } from 'lucide-react';

export type OTPMethod = 'sms' | 'voice' | 'both';

interface OtpSelectorProps {
  value: OTPMethod;
  onChange: (method: OTPMethod) => void;
  disabled?: boolean;
}

const methods: { id: OTPMethod; label: string; icon: typeof MessageSquare; description: string }[] = [
  { 
    id: 'sms', 
    label: 'SMS', 
    icon: MessageSquare,
    description: 'Receive code via text message'
  },
  { 
    id: 'voice', 
    label: 'Voice Call', 
    icon: PhoneCall,
    description: 'Receive code via phone call'
  },
  { 
    id: 'both', 
    label: 'Both', 
    icon: Zap,
    description: 'Receive via SMS and call'
  },
];

export function OtpSelector({ value, onChange, disabled = false }: OtpSelectorProps) {
  return (
    <div className="space-y-3">
      <label className="flex items-center gap-2 text-sm font-semibold text-gray-700">
        <Zap className="w-4 h-4 text-[#006600]" />
        Receive OTP via
      </label>
      
      <div className="grid grid-cols-3 gap-2">
        {methods.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            type="button"
            onClick={() => onChange(id)}
            disabled={disabled}
            className={`
              flex flex-col items-center justify-center gap-1.5 
              px-3 py-3 rounded-xl 
              border-2 transition-all duration-200
              font-medium text-sm
              disabled:opacity-50 disabled:cursor-not-allowed
              ${value === id 
                ? 'bg-[#006600] border-[#006600] text-white shadow-lg shadow-[#006600]/25' 
                : 'bg-white border-gray-200 text-gray-600 hover:border-[#006600]/50 hover:bg-[#006600]/5'
              }
            `}
            aria-pressed={value === id}
            aria-label={`Receive OTP via ${label}`}
          >
            <Icon className="w-5 h-5" />
            <span>{label}</span>
          </button>
        ))}
      </div>
      
      {/* Hint text */}
      <p className="text-xs text-gray-500 flex items-center gap-1.5">
        {value === 'sms' && (
          <>
            <span>📱</span>
            <span>You will receive a text message with your code</span>
          </>
        )}
        {value === 'voice' && (
          <>
            <span>📞</span>
            <span>You will receive a phone call with your code</span>
          </>
        )}
        {value === 'both' && (
          <>
            <span>📱📞</span>
            <span>You will receive both SMS and a phone call</span>
          </>
        )}
      </p>
    </div>
  );
}

export default OtpSelector;
