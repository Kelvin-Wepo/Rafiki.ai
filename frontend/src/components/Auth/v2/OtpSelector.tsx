/**
 * OtpSelector Component
 * Three pill buttons: SMS, Voice Call, Smart Auto (Recommended)
 * Only one selectable at a time
 */

import { MessageSquare, PhoneCall, Zap } from 'lucide-react';

export type OtpMethod = 'sms' | 'voice' | 'auto';

interface OtpSelectorProps {
  value: OtpMethod;
  onChange: (method: OtpMethod) => void;
  disabled?: boolean;
}

const options: { id: OtpMethod; label: string; icon: typeof MessageSquare; recommended?: boolean }[] = [
  { id: 'sms', label: 'SMS', icon: MessageSquare },
  { id: 'voice', label: 'Voice Call', icon: PhoneCall },
  { id: 'auto', label: 'Smart Auto', icon: Zap, recommended: true },
];

export function OtpSelector({ value, onChange, disabled = false }: OtpSelectorProps) {
  return (
    <div className="space-y-3">
      {/* Label */}
      <p className="text-sm font-medium text-slate-700">
        How would you like to receive your OTP?
      </p>

      {/* Pill Buttons - Grid layout for equal sizing */}
      <div className="grid grid-cols-3 gap-3">
        {options.map(({ id, label, icon: Icon, recommended }) => {
          const isSelected = value === id;
          return (
            <button
              key={id}
              type="button"
              onClick={() => onChange(id)}
              disabled={disabled}
              aria-pressed={isSelected}
              aria-label={`Receive OTP via ${label}${recommended ? ' (Recommended)' : ''}`}
              className={`
                relative flex items-center justify-center gap-2
                h-14 px-3 rounded-xl text-sm font-medium
                transition-all duration-200
                focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-[#0F6B3E]
                disabled:opacity-50 disabled:cursor-not-allowed
                ${isSelected 
                  ? 'bg-[#0F6B3E] text-white ring-2 ring-green-300 shadow-md' 
                  : 'bg-white text-slate-700 border border-slate-200 hover:bg-slate-50 hover:border-slate-300'
                }
              `}
            >
              {/* Recommended Badge */}
              {recommended && (
                <span 
                  className={`absolute -top-2 left-1/2 -translate-x-1/2 text-[9px] font-bold px-2 py-0.5 rounded-full whitespace-nowrap
                    ${isSelected ? 'bg-white text-[#0F6B3E]' : 'bg-[#0F6B3E] text-white'}
                  `}
                >
                  Recommended
                </span>
              )}
              <Icon className="w-4 h-4 flex-shrink-0" />
              <span className="truncate">{label}</span>
            </button>
          );
        })}
      </div>

      {/* Helper Text */}
      <p className="text-xs" style={{ color: '#6B7280' }}>
        Voice verification improves accessibility.
      </p>
    </div>
  );
}

export default OtpSelector;
