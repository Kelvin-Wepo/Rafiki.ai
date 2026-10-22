/**
 * Spoken Access onboarding: collect name, ID and phone, then verify by SMS.
 */

import { useCallback, useEffect, useRef, useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { useSpeechListen } from '../../hooks/useSpeechListen';
import { playElevenLabsText, stopElevenLabsAudio } from '../../lib/elevenlabsAudio';
import {
  formatPhoneForSpeech,
  parseKenyanId,
  parseKenyanPhone,
  parseOtpCode,
  parseSpokenName,
  parseYesNo,
} from '../../lib/spokenDigits';
import {
  startSmsLogin,
  startVoiceRegistration,
  verifySmsLogin,
  verifyVoiceRegistration,
} from '../../services/authService';
import { setAccessModeEnabled } from '../../lib/accessMode';

export type VoiceOnboardingMode = 'signup' | 'signin';

type Step =
  | 'name'
  | 'confirmName'
  | 'id'
  | 'confirmId'
  | 'phone'
  | 'confirmPhone'
  | 'otp'
  | 'done';

const COPY = {
  en: {
    signupTitle: 'Create your account by voice',
    signinTitle: 'Sign in by voice',
    name: 'What is your full name, as on your national ID?',
    heardName: (n: string) => `I heard ${n}. Press 1 if that is right, or 2 to say it again.`,
    id: 'What is your national ID number? Speak the digits slowly, or press them.',
    heardId: (n: string) => `I heard ID ${n.split('').join(' ')}. Press 1 if that is right, or 2 to say it again.`,
    phone: 'What phone number can receive SMS? Start with zero seven.',
    heardPhone: (n: string) =>
      `I heard ${formatPhoneForSpeech(n)}. Press 1 if that is right, or 2 to say it again.`,
    otp: 'I sent a six digit code by SMS. Speak the code, or press the numbers.',
    again: 'I did not catch that. Please try again.',
    listen: 'Speak now',
    stop: 'Stop',
    listening: 'Listening',
    yes: 'Yes, that is right',
    no: 'Say it again',
    resend: 'Send the SMS again',
    typeHint: 'Or type it here',
    submit: 'Use this',
    doneSignup: 'Your Rafiki account is ready. I also sent you a welcome SMS.',
    doneSignin: 'You are signed in. Welcome back.',
    noMic: 'This browser cannot hear you. Type in the large box, then press Use this.',
  },
  sw: {
    signupTitle: 'Fungua akaunti kwa sauti',
    signinTitle: 'Ingia kwa sauti',
    name: 'Jina lako kamili kama lilivyo kwenye kitambulisho ni nani?',
    heardName: (n: string) => `Nimesikia ${n}. Bonyeza 1 kama ni sahihi, au 2 kusema tena.`,
    id: 'Nambari ya kitambulisho ni ipi? Sema tarakimu polepole, au zibonyeze.',
    heardId: (n: string) => `Nimesikia kitambulisho ${n.split('').join(' ')}. Bonyeza 1 kama ni sahihi, au 2 kusema tena.`,
    phone: 'Nambari gani ya simu inapokea SMS? Anza na sifuri saba.',
    heardPhone: (n: string) =>
      `Nimesikia ${formatPhoneForSpeech(n)}. Bonyeza 1 kama ni sahihi, au 2 kusema tena.`,
    otp: 'Nimekutumia nambari ya tarakimu sita kwa SMS. Sema au bonyeza.',
    again: 'Sikukusikia. Tafadhali jaribu tena.',
    listen: 'Ongea sasa',
    stop: 'Simama',
    listening: 'Nasikiliza',
    yes: 'Ndiyo, ni sahihi',
    no: 'Sema tena',
    resend: 'Tuma SMS tena',
    typeHint: 'Au andika hapa',
    submit: 'Tumia hii',
    doneSignup: 'Akaunti yako ya Rafiki iko tayari. Nimekutumia SMS ya kukaribisha.',
    doneSignin: 'Umeingia. Karibu tena.',
    noMic: 'Kivinjari hiki hakiwezi kusikia. Andika kwenye kisanduku kikubwa, kisha bonyeza Tumia hii.',
  },
};

function firstStep(mode: VoiceOnboardingMode): Step {
  return mode === 'signup' ? 'name' : 'phone';
}

function promptFor(
  t: (typeof COPY)['en'],
  step: Step,
  draft: { name: string; id: string; phone: string }
): string {
  if (step === 'name') return t.name;
  if (step === 'confirmName') return t.heardName(draft.name);
  if (step === 'id') return t.id;
  if (step === 'confirmId') return t.heardId(draft.id);
  if (step === 'phone') return t.phone;
  if (step === 'confirmPhone') return t.heardPhone(draft.phone);
  if (step === 'otp') return t.otp;
  return '';
}

export function VoiceOnboarding({
  mode,
  language,
  onFinished,
  onCancel,
  onAnnounce,
}: {
  mode: VoiceOnboardingMode;
  language: 'en' | 'sw';
  onFinished: () => void;
  onCancel: () => void;
  onAnnounce?: (text: string) => void;
}) {
  const t = COPY[language];
  const { completeSession } = useAuth();
  const { listen, stop, listening, supported } = useSpeechListen(language);
  const [step, setStep] = useState<Step>(() => firstStep(mode));
  const [draft, setDraft] = useState({ name: '', id: '', phone: '', otp: '' });
  const [typed, setTyped] = useState('');
  const [heard, setHeard] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const spokenStep = useRef<string>('');

  const say = useCallback(
    async (text: string) => {
      onAnnounce?.(text);
      stopElevenLabsAudio();
      await playElevenLabsText(text);
    },
    [onAnnounce]
  );

  useEffect(() => {
    const key = `${mode}:${step}:${draft.name}:${draft.id}:${draft.phone}`;
    if (spokenStep.current === key) return;
    spokenStep.current = key;
    const text =
      step === 'done' ? (mode === 'signup' ? t.doneSignup : t.doneSignin) : promptFor(t, step, draft);
    if (!text) return;
    void say(text);
  }, [draft, mode, say, step, t]);

  const rejectAndRetry = useCallback(
    async (collectStep: Step) => {
      setError(t.again);
      setStep(collectStep);
      await say(t.again);
    },
    [say, t.again]
  );

  const sendCodeRef = useRef<(phone: string) => Promise<void>>(async () => undefined);
  const submitOtpRef = useRef<(otp: string) => Promise<void>>(async () => undefined);

  const sendCode = useCallback(
    async (phone: string) => {
      const target = phone || draft.phone;
      if (!target) return;
      setBusy(true);
      setError(null);
      try {
        if (mode === 'signup') {
          const res = await startVoiceRegistration(draft.name, target, draft.id, language);
          if (!res.success) {
            setError(res.message);
            await say(res.message);
            if (res.error === 'phone_exists') setStep('phone');
            else if (res.error === 'id_exists') setStep('id');
            return;
          }
          setDraft((d) => ({ ...d, phone: target, otp: res.test_mode && res.otp ? res.otp : d.otp }));
        } else {
          const res = await startSmsLogin(target);
          if (!res.success) {
            setError(res.message);
            await say(res.message);
            setStep('phone');
            return;
          }
          setDraft((d) => ({ ...d, phone: target }));
        }
        setStep('otp');
      } finally {
        setBusy(false);
      }
    },
    [draft.id, draft.name, draft.phone, language, mode, say]
  );

  const submitOtp = useCallback(
    async (otp: string) => {
      if (!draft.phone) return;
      setBusy(true);
      setError(null);
      try {
        const res =
          mode === 'signup'
            ? await verifyVoiceRegistration(draft.phone, otp)
            : await verifySmsLogin(draft.phone, otp);
        if (!res.success) {
          setError(res.message);
          await say(res.message);
          return;
        }
        setAccessModeEnabled(true);
        if (res.user && res.access_token) {
          completeSession(res.user, res.access_token, res.session_id);
        }
        setStep('done');
        await say(mode === 'signup' ? t.doneSignup : t.doneSignin);
        onFinished();
      } finally {
        setBusy(false);
      }
    },
    [completeSession, draft.phone, mode, onFinished, say, t.doneSignin, t.doneSignup]
  );

  sendCodeRef.current = sendCode;
  submitOtpRef.current = submitOtp;

  const handleTranscriptStable = useCallback(
    async (raw: string) => {
      const text = raw.trim();
      if (!text) {
        await rejectAndRetry(
          step === 'confirmName' ? 'name' : step === 'confirmId' ? 'id' : step === 'confirmPhone' ? 'phone' : step
        );
        return;
      }
      setHeard(text);
      setError(null);

      if (step === 'name') {
        const name = parseSpokenName(text);
        if (!name) return rejectAndRetry('name');
        setDraft((d) => ({ ...d, name }));
        setStep('confirmName');
        return;
      }
      if (step === 'confirmName') {
        const yn = parseYesNo(text);
        if (yn === 'yes') setStep('id');
        else if (yn === 'no') setStep('name');
        else await rejectAndRetry('confirmName');
        return;
      }
      if (step === 'id') {
        const id = parseKenyanId(text);
        if (!id) return rejectAndRetry('id');
        setDraft((d) => ({ ...d, id }));
        setStep('confirmId');
        return;
      }
      if (step === 'confirmId') {
        const yn = parseYesNo(text);
        if (yn === 'yes') setStep('phone');
        else if (yn === 'no') setStep('id');
        else await rejectAndRetry('confirmId');
        return;
      }
      if (step === 'phone') {
        const phone = parseKenyanPhone(text);
        if (!phone) return rejectAndRetry('phone');
        setDraft((d) => ({ ...d, phone }));
        setStep('confirmPhone');
        return;
      }
      if (step === 'confirmPhone') {
        const yn = parseYesNo(text);
        if (yn === 'yes') await sendCodeRef.current(draft.phone);
        else if (yn === 'no') setStep('phone');
        else await rejectAndRetry('confirmPhone');
        return;
      }
      if (step === 'otp') {
        const otp = parseOtpCode(text);
        if (!otp) return rejectAndRetry('otp');
        await submitOtpRef.current(otp);
      }
    },
    [draft.phone, rejectAndRetry, step]
  );

  const startListen = useCallback(async () => {
    if (busy || step === 'done') return;
    setError(null);
    try {
      const text = await listen();
      await handleTranscriptStable(text);
    } catch (err) {
      const code = err instanceof Error ? err.message : '';
      if (code === 'no-speech-api' || code === 'not-allowed') {
        setError(t.noMic);
      } else if (code !== 'aborted') {
        setError(t.again);
      }
    }
  }, [busy, handleTranscriptStable, listen, step, t.again, t.noMic]);

  const applyTyped = useCallback(async () => {
    if (!typed.trim()) return;
    await handleTranscriptStable(typed);
    setTyped('');
  }, [handleTranscriptStable, typed]);

  const pressDigit = useCallback(
    (digit: string) => {
      if (step === 'otp') {
        setTyped((current) => (current + digit).replace(/\D/g, '').slice(0, 6));
        return;
      }
      if (step === 'id' || step === 'phone') {
        setTyped((current) => (current + digit).replace(/\D/g, '').slice(0, 12));
      }
    },
    [step]
  );

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      const target = event.target as HTMLElement | null;
      if (target && (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA')) return;
      if (event.key === 'Escape' || event.key === '0') {
        stop();
        onCancel();
        return;
      }
      if (step.startsWith('confirm') && event.key === '1') {
        event.preventDefault();
        void handleTranscriptStable('yes');
      } else if (step.startsWith('confirm') && event.key === '2') {
        event.preventDefault();
        void handleTranscriptStable('no');
      } else if (event.key === '1' && !step.startsWith('confirm') && step !== 'done') {
        event.preventDefault();
        void startListen();
      } else if (/^[0-9]$/.test(event.key) && (step === 'otp' || step === 'id' || step === 'phone')) {
        pressDigit(event.key);
      } else if (event.key === 'Enter' && typed) {
        event.preventDefault();
        void applyTyped();
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [applyTyped, handleTranscriptStable, onCancel, pressDigit, startListen, step, stop, typed]);

  const confirming = step.startsWith('confirm');
  const collecting = step === 'name' || step === 'id' || step === 'phone' || step === 'otp';
  const showPad = step === 'id' || step === 'phone' || step === 'otp';

  return (
    <section className="ra-stage" aria-labelledby="ra-voice-title">
      <h1 id="ra-voice-title" className="ra-title">
        {mode === 'signup' ? t.signupTitle : t.signinTitle}
      </h1>
      <p className={`ra-status${listening ? ' is-live' : ''}`} role="status">
        <span className="ra-dot" aria-hidden="true" />
        {listening ? t.listening : promptFor(t, step, draft) || (mode === 'signup' ? t.doneSignup : t.doneSignin)}
      </p>
      <p className="ra-transcript">{heard || promptFor(t, step, draft)}</p>

      {step !== 'done' && collecting && (
        <button
          type="button"
          className="ra-key ra-key--primary"
          onClick={() => (listening ? stop() : void startListen())}
          disabled={busy}
        >
          <span className="ra-key-num" aria-hidden="true">
            1
          </span>
          <span className="ra-key-copy">
            <span>{listening ? t.stop : t.listen}</span>
            <span className="ra-key-sub">{supported ? '' : t.noMic}</span>
          </span>
        </button>
      )}

      {confirming && (
        <div className="ra-keys" role="list">
          <button type="button" className="ra-key ra-key--primary" onClick={() => void handleTranscriptStable('yes')}>
            <span className="ra-key-num" aria-hidden="true">
              1
            </span>
            <span className="ra-key-copy">
              <span>{t.yes}</span>
            </span>
          </button>
          <button type="button" className="ra-key" onClick={() => void handleTranscriptStable('no')}>
            <span className="ra-key-num" aria-hidden="true">
              2
            </span>
            <span className="ra-key-copy">
              <span>{t.no}</span>
            </span>
          </button>
        </div>
      )}

      {collecting && (
        <form
          className="ra-composer-row"
          onSubmit={(event) => {
            event.preventDefault();
            void applyTyped();
          }}
        >
          <label className="sr-only" htmlFor="ra-voice-type">
            {t.typeHint}
          </label>
          <input
            id="ra-voice-type"
            className="ra-input"
            value={typed}
            onChange={(event) => setTyped(event.target.value)}
            placeholder={t.typeHint}
            inputMode={showPad ? 'numeric' : 'text'}
            autoComplete="off"
          />
          <button type="submit" className="ra-key ra-key--primary" disabled={busy || !typed.trim()}>
            {t.submit}
          </button>
        </form>
      )}

      {showPad && (
        <div className="ra-pad" role="group" aria-label={language === 'sw' ? 'Tarakimu' : 'Digits'}>
          {['1', '2', '3', '4', '5', '6', '7', '8', '9', '0'].map((digit) => (
            <button key={digit} type="button" className="ra-pad-key" onClick={() => pressDigit(digit)}>
              {digit}
            </button>
          ))}
        </div>
      )}

      {step === 'otp' && (
        <button
          type="button"
          className="ra-chip"
          onClick={() => void sendCode(draft.phone)}
          disabled={busy || !draft.phone}
        >
          {t.resend}
        </button>
      )}

      {error && (
        <p className="ra-error" role="alert">
          {error}
        </p>
      )}
    </section>
  );
}
