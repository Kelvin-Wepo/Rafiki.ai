/**
 * AuthCard Component
 * Card wrapper with optional shake animation for errors
 */

import React, { useEffect, useState } from 'react';

interface AuthCardProps {
  children: React.ReactNode;
  shake?: boolean;
  onShakeEnd?: () => void;
  className?: string;
}

export function AuthCard({
  children,
  shake = false,
  onShakeEnd,
  className = '',
}: AuthCardProps) {
  const [isShaking, setIsShaking] = useState(false);

  useEffect(() => {
    if (shake) {
      setIsShaking(true);
      const timer = setTimeout(() => {
        setIsShaking(false);
        onShakeEnd?.();
      }, 500);
      return () => clearTimeout(timer);
    }
  }, [shake, onShakeEnd]);

  return (
    <div 
      className={`auth-card ${isShaking ? 'shake' : ''} ${className}`}
      role="region"
      aria-live="polite"
    >
      {children}
    </div>
  );
}

export default AuthCard;
