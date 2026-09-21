/**
 * RegisterPage Component - CREATIVE REDESIGN
 * Bold, modern, government-grade design for Kenya
 * Split-screen with animated elements and accessibility focus
 */

import { useState, type FormEvent } from 'react';
import { Shield, Phone, MessageSquare, PhoneCall, Zap, CheckCircle, Mic, Globe, ArrowRight, Loader2 } from 'lucide-react';
import { useAuth } from '../../../contexts/AuthContext';
import type { OTPDeliveryMethod } from '../../../services/authService';

type OtpMethod = 'sms' | 'voice' | 'auto';

export function RegisterPage() {
  const { login, isLoading, error, clearError } = useAuth();
  const [phoneNumber, setPhoneNumber] = useState('');
  const [otpMethod, setOtpMethod] = useState<OtpMethod>('auto');
  const [validationError, setValidationError] = useState<string | null>(null);
  const [isFocused, setIsFocused] = useState(false);

  const validatePhone = (phone: string): boolean => {
    const cleaned = phone.replace(/\s/g, '');
    return /^0?\d{9}$/.test(cleaned);
  };

  const formatPhone = (phone: string): string => {
    const cleaned = phone.replace(/\s/g, '');
    if (cleaned.startsWith('0')) return `+254${cleaned.slice(1)}`;
    return `+254${cleaned}`;
  };

  const mapOtpMethod = (method: OtpMethod): OTPDeliveryMethod => {
    switch (method) {
      case 'sms': return 'sms';
      case 'voice': return 'voice';
      case 'auto': return 'both';
    }
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setValidationError(null);
    clearError();

    if (!phoneNumber.trim()) {
      setValidationError('Please enter your phone number');
      return;
    }

    if (!validatePhone(phoneNumber)) {
      setValidationError('Enter a valid Kenyan number (e.g., 0712345678)');
      return;
    }

    try {
      await login(formatPhone(phoneNumber), mapOtpMethod(otpMethod));
    } catch {
      // Error handled by context
    }
  };

  const displayError = validationError || error;

  const otpOptions = [
    { id: 'sms' as OtpMethod, label: 'SMS', icon: MessageSquare },
    { id: 'voice' as OtpMethod, label: 'Voice', icon: PhoneCall },
    { id: 'auto' as OtpMethod, label: 'Smart', icon: Zap, recommended: true },
  ];

  return (
    <div className="min-h-screen flex">
      {/* LEFT PANEL - Form */}
      <div className="w-full lg:w-[480px] xl:w-[520px] min-h-screen flex flex-col bg-white relative z-10">
        {/* Mobile Hero Banner */}
        <div className="lg:hidden h-52 relative overflow-hidden">
          <img
            src="https://images.unsplash.com/photo-1551836022-deb4988cc6c0?w=800&q=80"
            alt="Woman using smartphone"
            className="absolute inset-0 w-full h-full object-cover"
            style={{ objectPosition: 'center 20%' }}
          />
          <div className="absolute inset-0 bg-gradient-to-b from-emerald-900/60 via-emerald-800/40 to-white" />
          <div className="absolute bottom-4 left-4 right-4">
            <div className="flex items-center gap-2">
              <div className="w-10 h-10 rounded-xl bg-white/20 backdrop-blur flex items-center justify-center">
                <Shield className="w-5 h-5 text-white" />
              </div>
              <span className="text-white font-bold text-lg">Rafiki.ai</span>
            </div>
          </div>
        </div>

        {/* Form Content */}
        <div className="flex-1 flex flex-col justify-center px-6 sm:px-10 lg:px-12 py-8">
          {/* Desktop Logo */}
          <div className="hidden lg:flex items-center gap-3 mb-10">
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-emerald-500 to-emerald-700 flex items-center justify-center shadow-lg shadow-emerald-500/30">
              <Shield className="w-6 h-6 text-white" />
            </div>
            {/* <div>
              <span className="text-xl font-bold text-slate-900">Rafiki.ai</span>
              <p className="text-xs text-slate-500">Government Services Platform</p>
            </div> */}``
          </div>

          {/* Heading */}
          <div className="mb-8">
            <h1 className="text-3xl sm:text-4xl font-bold text-slate-900 mb-2 tracking-tight">
              Karibu Rafiki
              <span className="ml-2 inline-block animate-bounce">🇰🇪</span>
            </h1>
            <p className="text-lg text-emerald-700 font-medium">
              Huduma za Serikali kwa sauti yako.
            </p>
            <p className="text-sm text-slate-500 mt-1">
              Speak. Ask. Get help — instantly.
            </p>
          </div>

          {/* Voice Banner */}
          <div className="mb-8 p-4 rounded-2xl bg-gradient-to-r from-emerald-50 to-teal-50 border border-emerald-100">
            <div className="flex items-start gap-3">
              <div className="w-10 h-10 rounded-full bg-emerald-100 flex items-center justify-center flex-shrink-0">
                <Mic className="w-5 h-5 text-emerald-600" />
              </div>
              <div>
                <p className="text-sm font-semibold text-emerald-800">
                  Voice-first platform
                </p>
                <p className="text-xs text-emerald-600 mt-0.5">
                  Tap the mic anytime to speak in Swahili or English
                </p>
              </div>
            </div>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Phone Input */}
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                Phone Number
              </label>
              <div 
                className={`
                  flex items-center rounded-xl border-2 bg-white overflow-hidden transition-all duration-200
                  ${isFocused ? 'border-emerald-500 ring-4 ring-emerald-500/10' : 'border-slate-200'}
                  ${displayError ? 'border-red-400 ring-4 ring-red-500/10' : ''}
                `}
              >
                {/* Country Code */}
                <div className="flex items-center gap-2 px-4 py-3.5 bg-slate-50 border-r border-slate-200">
                  <span className="text-lg">🇰🇪</span>
                  <span className="font-semibold text-slate-700">+254</span>
                </div>
                {/* Input */}
                <div className="flex-1 flex items-center px-4">
                  <Phone className="w-5 h-5 text-slate-400 mr-3" />
                  <input
                    type="tel"
                    placeholder="712 345 678"
                    value={phoneNumber}
                    onChange={(e) => {
                      setPhoneNumber(e.target.value);
                      if (validationError) setValidationError(null);
                      if (error) clearError();
                    }}
                    onFocus={() => setIsFocused(true)}
                    onBlur={() => setIsFocused(false)}
                    disabled={isLoading}
                    className="w-full py-3.5 text-lg font-medium text-slate-900 placeholder-slate-400 outline-none bg-transparent"
                    autoComplete="tel"
                  />
                </div>
              </div>
              {displayError && (
                <p className="mt-2 text-sm text-red-600 flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-red-500" />
                  {displayError}
                </p>
              )}
            </div>

            {/* OTP Method */}
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-3">
                How would you like to receive your OTP?
              </label>
              <div className="grid grid-cols-3 gap-3">
                {otpOptions.map(({ id, label, icon: Icon, recommended }) => {
                  const isSelected = otpMethod === id;
                  return (
                    <button
                      key={id}
                      type="button"
                      onClick={() => setOtpMethod(id)}
                      disabled={isLoading}
                      className={`
                        relative h-16 rounded-xl flex flex-col items-center justify-center gap-1 font-medium transition-all duration-200
                        ${isSelected 
                          ? 'bg-emerald-600 text-white shadow-lg shadow-emerald-500/30 scale-[1.02]' 
                          : 'bg-slate-50 text-slate-600 hover:bg-slate-100 border border-slate-200'
                        }
                      `}
                    >
                      {recommended && (
                        <span className={`absolute -top-2 text-[10px] font-bold px-2 py-0.5 rounded-full ${isSelected ? 'bg-white text-emerald-600' : 'bg-emerald-600 text-white'}`}>
                          ★ Best
                        </span>
                      )}
                      <Icon className="w-5 h-5" />
                      <span className="text-xs">{label}</span>
                    </button>
                  );
                })}
              </div>
              <p className="mt-2 text-xs text-slate-500">
                Voice verification is great for accessibility.
              </p>
            </div>

            {/* Submit */}
            <button
              type="submit"
              disabled={isLoading}
              className="w-full h-14 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 text-white font-bold text-base flex items-center justify-center gap-2 shadow-lg shadow-emerald-500/30 hover:shadow-xl hover:shadow-emerald-500/40 hover:scale-[1.01] active:scale-[0.99] transition-all duration-200 disabled:opacity-60 disabled:cursor-not-allowed"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  <span>Verifying…</span>
                </>
              ) : (
                <>
                  <span>Continue to Verification</span>
                  <ArrowRight className="w-5 h-5" />
                </>
              )}
            </button>
          </form>

          {/* Trust Badges */}
          <div className="mt-8 pt-6 border-t border-slate-100">
            <div className="flex flex-wrap items-center justify-center gap-x-6 gap-y-2">
              {[
                { icon: CheckCircle, label: 'WCAG 2.1 AA' },
                { icon: Mic, label: 'Voice Enabled' },
                { icon: Globe, label: 'EN / Swahili' },
              ].map(({ icon: Icon, label }) => (
                <div key={label} className="flex items-center gap-1.5 text-xs text-slate-500">
                  <Icon className="w-3.5 h-3.5 text-emerald-600" />
                  <span>{label}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="py-4 px-6 bg-slate-50 border-t border-slate-100">
          <p className="text-center text-xs text-slate-500 mb-2">
            🔒 End-to-end encrypted. Built for Kenya.
          </p>
          <div className="flex justify-center gap-0.5">
            <div className="w-8 h-1 rounded-full bg-black" />
            <div className="w-8 h-1 rounded-full bg-red-600" />
            <div className="w-8 h-1 rounded-full bg-emerald-600" />
          </div>
        </div>
      </div>

      {/* RIGHT PANEL - Hero */}
      <div className="hidden lg:block flex-1 relative overflow-hidden">
        {/* Real Photo - Woman using smartphone */}
        <img
          src="https://images.unsplash.com/photo-1551836022-deb4988cc6c0?w=1920&q=80"
          alt="Woman holding and using her smartphone"
          className="absolute inset-0 w-full h-full object-cover"
          style={{ objectPosition: 'center 15%' }}
        />
        
        {/* Gradient Overlay */}
        <div className="absolute inset-0 bg-gradient-to-r from-emerald-900/50 via-emerald-900/20 to-transparent" />
        <div className="absolute inset-0 bg-gradient-to-t from-emerald-950/70 via-transparent to-emerald-900/20" />
        
        {/* Gradient Overlays for depth */}
        <div className="absolute inset-0 bg-gradient-to-r from-emerald-900/60 via-transparent to-transparent" />
        <div className="absolute inset-0 bg-gradient-to-t from-emerald-950/80 via-transparent to-emerald-900/30" />
        
        {/* Decorative Pattern */}
        <div className="absolute inset-0 opacity-10" style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.4'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")`,
        }} />
        
        {/* Animated Waveform */}
        <div className="absolute bottom-40 left-1/2 -translate-x-1/2 opacity-25 pointer-events-none">
          <svg viewBox="0 0 300 60" className="w-72 h-16">
            {[...Array(30)].map((_, i) => {
              const h = Math.sin(i * 0.4) * 20 + 25;
              return (
                <rect
                  key={i}
                  x={i * 10}
                  y={(60 - h) / 2}
                  width="5"
                  height={h}
                  fill="white"
                  rx="2.5"
                  className="animate-pulse"
                  style={{ animationDelay: `${i * 50}ms`, animationDuration: '1.5s' }}
                />
              );
            })}
          </svg>
        </div>

        {/* Quote Box - Glassmorphism style */}
        <div className="absolute bottom-16 right-8 left-8 lg:left-auto lg:right-12 lg:max-w-md">
          <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-6 border border-white/20 shadow-2xl">
            <div className="flex items-center gap-4 mb-4">
              <button
                className="w-12 h-12 rounded-full bg-emerald-500 flex items-center justify-center shadow-lg shadow-emerald-500/40 hover:bg-emerald-400 transition-colors"
                aria-label="Voice assistant"
              >
                <Mic className="w-6 h-6 text-white" />
              </button>
              <div>
                <p className="text-white/60 text-xs uppercase tracking-wider">Voice Enabled</p>
                <p className="text-white font-semibold">Speak to Rafiki</p>
              </div>
            </div>
            <p className="text-white text-xl lg:text-2xl font-semibold italic leading-relaxed">
              "Sema tu… Rafiki atakusaidia."
            </p>
            <p className="text-white/70 text-sm mt-2">
              Just speak… Rafiki will help you.
            </p>
          </div>
        </div>

        {/* Kenya Flag Stripe - Enhanced */}
        <div className="absolute bottom-0 left-0 right-0 h-3 flex shadow-lg">
          <div className="flex-1 bg-black" />
          <div className="w-1 bg-white" />
          <div className="flex-1 bg-red-600" />
          <div className="w-1 bg-white" />
          <div className="flex-1 bg-emerald-600" />
        </div>
        
        {/* Rafiki Logo Watermark */}
        <div className="absolute top-8 right-8 flex items-center gap-2 opacity-80">
          <div className="w-10 h-10 rounded-xl bg-white/20 backdrop-blur flex items-center justify-center">
            <Shield className="w-5 h-5 text-white" />
          </div>
          <span className="text-white font-bold text-lg tracking-tight">Rafiki.ai</span>
        </div>
      </div>
    </div>
  );
}

export default RegisterPage;
