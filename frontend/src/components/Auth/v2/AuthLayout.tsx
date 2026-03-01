/**
 * AuthLayout Component - IMPROVED
 * Split-screen layout: Left (40%) form card, Right (60%) hero image
 * Responsive: Mobile shows hero on top, form in bottom sheet
 * 
 * Fixes: Consistent 32px padding, improved spacing, better mobile UX
 */

import type { ReactNode } from 'react';
import { HeroSection } from './HeroSection';

interface AuthLayoutProps {
  children: ReactNode;
}

export function AuthLayout({ children }: AuthLayoutProps) {
  return (
    <div className="min-h-screen grid grid-cols-1 lg:grid-cols-[520px_1fr] bg-[#F7F9F8]">
      {/* Mobile Hero - Shows on top for mobile only */}
      <div className="lg:hidden relative h-[38vh] min-h-[240px]">
        <HeroSection isMobile />
      </div>

      {/* LEFT SIDE - Form Panel */}
      <div className="min-h-screen flex flex-col relative z-10 lg:px-10">
        {/* Form Card Container - Vertically centered */}
        <div className="flex-1 flex items-center justify-center px-4 sm:px-6 py-8 lg:py-12">
          <div 
            className="w-full max-w-[520px] bg-white rounded-2xl p-8 -mt-12 lg:mt-0 shadow-lg"
          >
            {children}
          </div>
        </div>

        {/* Footer Trust Strip */}
        <div className="py-4 px-6 bg-slate-50">
          <p className="text-center text-xs text-slate-500 mb-2">
            Protected by end-to-end encryption. Built for Kenya.
          </p>
          {/* Kenya flag accent line */}
          <div className="flex justify-center">
            <div className="flex h-1 w-20 rounded-full overflow-hidden">
              <div className="flex-1 bg-black"></div>
              <div className="flex-1 bg-[#BB0000]"></div>
              <div className="flex-1 bg-[#006600]"></div>
            </div>
          </div>
        </div>
      </div>

      {/* RIGHT SIDE - Hero Image */}
      <div className="hidden lg:block relative">
        <HeroSection />
      </div>
    </div>
  );
}

export default AuthLayout;
