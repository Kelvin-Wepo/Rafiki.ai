/**
 * TrustBadges Component
 * Security and trust indicators
 */

import { Lock, Shield, CheckCircle } from 'lucide-react';

interface TrustBadgesProps {
  variant?: 'horizontal' | 'vertical';
  showAll?: boolean;
}

export function TrustBadges({ variant = 'horizontal', showAll = true }: TrustBadgesProps) {
  const badges = [
    { icon: Lock, text: 'End-to-end encrypted' },
    { icon: Shield, text: 'Government verified' },
    { icon: CheckCircle, text: 'WCAG 2.1 AA' },
  ];

  const displayBadges = showAll ? badges : [badges[0]];

  if (variant === 'vertical') {
    return (
      <div className="space-y-2">
        {displayBadges.map(({ icon: Icon, text }, index) => (
          <div key={index} className="flex items-center gap-2 text-xs text-gray-500">
            <Icon className="w-3.5 h-3.5 text-[#006600]" />
            <span>{text}</span>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="flex flex-wrap items-center justify-center gap-4 pt-6 border-t border-gray-100">
      {displayBadges.map(({ icon: Icon, text }, index) => (
        <div key={index} className="flex items-center gap-1.5 text-xs text-gray-500">
          <Icon className="w-3.5 h-3.5 text-[#006600]" />
          <span>{text}</span>
        </div>
      ))}
    </div>
  );
}

export default TrustBadges;
