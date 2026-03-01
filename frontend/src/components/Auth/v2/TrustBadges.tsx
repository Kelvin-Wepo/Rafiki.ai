/**
 * TrustBadges Component - IMPROVED
 * Accessibility and trust indicators row
 * WCAG 2.1 AA, Voice Enabled, Bilingual (EN/SW)
 * Better spacing and visual hierarchy
 */

import { CheckCircle, Mic, Globe } from 'lucide-react';

export function TrustBadges() {
  const badges = [
    { icon: CheckCircle, label: 'WCAG 2.1 AA' },
    { icon: Mic, label: 'Voice Enabled' },
    { icon: Globe, label: 'Bilingual (EN/SW)' },
  ];

  return (
    <div className="flex flex-wrap items-center justify-center gap-4 pt-4">
      {badges.map(({ icon: Icon, label }, index) => (
        <div 
          key={index} 
          className="flex items-center gap-1.5 text-xs text-slate-500"
        >
          <Icon className="w-3.5 h-3.5 text-[#0F6B3E]" />
          <span>{label}</span>
        </div>
      ))}
    </div>
  );
}

export default TrustBadges;
