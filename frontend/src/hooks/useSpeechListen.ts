import { useCallback, useRef, useState } from 'react';

type SpeechRecCtor = new () => {
  lang: string;
  interimResults: boolean;
  continuous: boolean;
  maxAlternatives: number;
  start: () => void;
  stop: () => void;
  abort: () => void;
  onresult: ((event: { results: ArrayLike<ArrayLike<{ transcript: string }>> }) => void) | null;
  onerror: ((event: { error?: string }) => void) | null;
  onend: (() => void) | null;
};

function speechCtor(): SpeechRecCtor | null {
  const w = window as unknown as {
    SpeechRecognition?: SpeechRecCtor;
    webkitSpeechRecognition?: SpeechRecCtor;
  };
  return w.SpeechRecognition || w.webkitSpeechRecognition || null;
}

export function useSpeechListen(language: 'en' | 'sw') {
  const [listening, setListening] = useState(false);
  const recRef = useRef<InstanceType<SpeechRecCtor> | null>(null);
  const supported = typeof window !== 'undefined' && Boolean(speechCtor());

  const stop = useCallback(() => {
    try {
      recRef.current?.abort();
    } catch {
      /* already stopped */
    }
    recRef.current = null;
    setListening(false);
  }, []);

  const listen = useCallback((): Promise<string> => {
    const Ctor = speechCtor();
    if (!Ctor) {
      return Promise.reject(new Error('no-speech-api'));
    }
    stop();
    return new Promise((resolve, reject) => {
      const rec = new Ctor();
      recRef.current = rec;
      rec.lang = language === 'sw' ? 'sw-KE' : 'en-KE';
      rec.interimResults = false;
      rec.continuous = false;
      rec.maxAlternatives = 3;
      rec.onresult = (event) => {
        const first = event.results[0]?.[0]?.transcript?.trim() || '';
        setListening(false);
        recRef.current = null;
        if (first) resolve(first);
        else reject(new Error('empty'));
      };
      rec.onerror = (event) => {
        setListening(false);
        recRef.current = null;
        reject(new Error(event.error || 'speech-error'));
      };
      rec.onend = () => {
        setListening(false);
        recRef.current = null;
      };
      try {
        setListening(true);
        rec.start();
      } catch (err) {
        setListening(false);
        recRef.current = null;
        reject(err instanceof Error ? err : new Error('speech-error'));
      }
    });
  }, [language, stop]);

  return { listen, stop, listening, supported };
}
