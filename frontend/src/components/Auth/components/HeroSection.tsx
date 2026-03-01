/**
 * HeroSection Component
 * Left panel hero content with branding and value proposition
 */

import { Shield, Mic, Globe } from 'lucide-react';

export function HeroSection() {
  return (
    <div className="flex flex-col h-full text-white">
      {/* Logo */}
      <div className="flex items-center gap-3 mb-12">
        <div className="w-12 h-12 bg-white/20 backdrop-blur-sm rounded-xl flex items-center justify-center">
          <Shield className="w-7 h-7 text-white" />
        </div>
        <span className="text-2xl font-bold tracking-tight">Rafiki.ai</span>
      </div>

      {/* Main Headline */}
      <div className="flex-1 flex flex-col justify-center">
        <h1 className="text-4xl lg:text-5xl font-bold leading-tight mb-6">
          Huduma za Serikali
          <br />
          <span className="text-white/90">Kwa Sauti Yako</span>
        </h1>
        
        <p className="text-xl text-white/80 mb-10 leading-relaxed">
          Access Kenya government services through voice — in English, Kiswahili, or both.
        </p>

        {/* Feature Pills */}
        <div className="flex flex-wrap gap-3 mb-12">
          <div className="flex items-center gap-2 bg-white/15 backdrop-blur-sm px-4 py-2 rounded-full text-sm font-medium">
            <Mic className="w-4 h-4" />
            <span>Voice-First</span>
          </div>
          <div className="flex items-center gap-2 bg-white/15 backdrop-blur-sm px-4 py-2 rounded-full text-sm font-medium">
            <Globe className="w-4 h-4" />
            <span>Bilingual</span>
          </div>
          <div className="flex items-center gap-2 bg-white/15 backdrop-blur-sm px-4 py-2 rounded-full text-sm font-medium">
            <Shield className="w-4 h-4" />
            <span>Secure</span>
          </div>
        </div>

        {/* Stats/Social Proof */}
        <div className="grid grid-cols-3 gap-6 border-t border-white/20 pt-8">
          <div>
            <div className="text-3xl font-bold">7+</div>
            <div className="text-sm text-white/70">Government Services</div>
          </div>
          <div>
            <div className="text-3xl font-bold">2</div>
            <div className="text-sm text-white/70">Languages</div>
          </div>
          <div>
            <div className="text-3xl font-bold">24/7</div>
            <div className="text-sm text-white/70">Available</div>
          </div>
        </div>
      </div>

      {/* Footer Quote */}
      <div className="mt-auto pt-8 border-t border-white/10">
        <p className="text-white/60 text-sm italic">
          "Sema. Sikiliza. Pata Msaada."
        </p>
        <p className="text-white/40 text-xs mt-1">
          Speak. Listen. Get Help.
        </p>
      </div>
    </div>
  );
}

export default HeroSection;
