/**
 * VoiceBanner Component
 * Green-tinted info row with mic icon
 */

import { Mic } from 'lucide-react';

export function VoiceBanner() {
  return (
    <div 
      className="flex items-center gap-3 p-4 rounded-xl"
      style={{ backgroundColor: 'rgba(15, 107, 62, 0.08)' }}
    >
      <div 
        className="w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0"
        style={{ backgroundColor: 'rgba(15, 107, 62, 0.15)' }}
      >
        <Mic className="w-5 h-5" style={{ color: '#0F6B3E' }} />
      </div>
      <p className="text-sm" style={{ color: '#0A4F2A' }}>
        Register using your phone number to start voice access.
      </p>
    </div>
  );
}

export default VoiceBanner;
