/** Play ElevenLabs audio only. Never fall through to the browser voice. */

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

let current: HTMLAudioElement | null = null;
let playGen = 0;

export function stopElevenLabsAudio() {
  playGen += 1;
  if (!current) return;
  current.pause();
  current.src = '';
  current = null;
}

function playUrl(url: string, revokeOnEnd = false): Promise<boolean> {
  stopElevenLabsAudio();
  return new Promise((resolve) => {
    const audio = new Audio(url);
    current = audio;
    const finish = (ok: boolean) => {
      if (current === audio) current = null;
      if (revokeOnEnd) URL.revokeObjectURL(url);
      resolve(ok);
    };
    audio.onended = () => finish(true);
    audio.onerror = () => finish(false);
    audio.play().catch(() => finish(false));
  });
}

export function playElevenLabsBase64(audioBase64: string, mimeType = 'audio/mpeg'): Promise<boolean> {
  const data = audioBase64.trim();
  if (!data) return Promise.resolve(false);
  const bytes = Uint8Array.from(atob(data), (c) => c.charCodeAt(0));
  const url = URL.createObjectURL(new Blob([bytes], { type: mimeType || 'audio/mpeg' }));
  return playUrl(url, true);
}

export async function playElevenLabsText(text: string): Promise<boolean> {
  const trimmed = text.trim();
  if (!trimmed) return false;
  const gen = ++playGen;
  try {
    const response = await fetch(`${API_BASE}/elevenlabs/tts`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: trimmed }),
    });
    if (gen !== playGen) return false;
    if (!response.ok) return false;
    const data = (await response.json()) as {
      success?: boolean;
      audio_data?: string;
      content_type?: string;
    };
    if (gen !== playGen) return false;
    if (!data.success || !data.audio_data) return false;
    return playElevenLabsBase64(data.audio_data, data.content_type || 'audio/mpeg');
  } catch (err) {
    console.error('ElevenLabs TTS failed:', err);
    return false;
  }
}
