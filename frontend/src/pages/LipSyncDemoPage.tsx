/**
 * Debug page: play sample clips against the canvas avatar and inspect viseme sync.
 * Open /lipsync-demo — no login required.
 */
import { useCallback, useEffect, useState } from 'react';
import rafikiAvatar from '../assets/rafiki_avatar.png';
import TalkingAvatar from '../components/avatar/TalkingAvatar';
import { DEFAULT_MOUTH_REGION } from '../components/avatar/lipsyncConfig';
import type { MouthRegion, VisemeCue } from '../components/avatar/visemeShapes';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const SAMPLES = [
  { id: 'hi', label: 'Greeting', text: 'Habari! Mimi ni Rafiki.' },
  { id: 'help', label: 'How can I help', text: 'Karibu. How can I help you today with NTSA or KRA?' },
  { id: 'long', label: 'Longer phrase', text: 'Please have your national ID ready. I will walk you through each step.' },
];

type PreviewResponse = {
  success: boolean;
  audio_base64?: string;
  audio_mime?: string;
  viseme_timeline?: VisemeCue[];
  mouth_region?: MouthRegion;
  fallback?: boolean;
  note?: string;
  error?: string;
};

export default function LipSyncDemoPage() {
  const [region, setRegion] = useState<MouthRegion>(DEFAULT_MOUTH_REGION);
  const [clip, setClip] = useState<{ audioUrl: string; visemes: VisemeCue[]; playId: number } | null>(
    null
  );
  const [status, setStatus] = useState('Idle — pick a sample to check mouth sync.');
  const [busy, setBusy] = useState(false);
  const [showBox, setShowBox] = useState(true);
  const [cueCount, setCueCount] = useState(0);

  useEffect(() => {
    fetch(`${API_BASE}/avatar/lipsync/config`)
      .then((res) => res.json())
      .then((data) => {
        if (data?.mouth_region) setRegion(data.mouth_region);
      })
      .catch(() => {
        /* keep frontend defaults */
      });
  }, []);

  const playSample = useCallback(
    async (text: string, label: string) => {
      setBusy(true);
      setStatus(`Generating ${label}…`);
      try {
        const res = await fetch(`${API_BASE}/avatar/lipsync/preview`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text }),
        });
        const data: PreviewResponse = await res.json();
        if (!data.audio_base64) {
          setStatus(data.error || data.note || 'No audio returned.');
          return;
        }
        const visemes = data.viseme_timeline || [];
        setCueCount(visemes.length);
        setClip({
          audioUrl: `data:${data.audio_mime || 'audio/mpeg'};base64,${data.audio_base64}`,
          visemes,
          playId: Date.now(),
        });
        const mode = visemes.length
          ? `${visemes.length} visemes${data.fallback ? ' (fallback envelope)' : ''}`
          : 'pulse fallback — no visemes';
        setStatus(`Playing ${label}. ${mode}. Aim for ~50–100ms tightness.`);
      } catch (err) {
        setStatus(err instanceof Error ? err.message : 'Preview failed');
      } finally {
        setBusy(false);
      }
    },
    []
  );

  return (
    <main className="lipsync-demo">
      <style>{`
        .lipsync-demo {
          min-height: 100vh;
          margin: 0;
          padding: 32px 20px 64px;
          background: #f7f4ea;
          color: #1f2933;
          font-family: system-ui, sans-serif;
        }
        .lipsync-demo h1 { margin: 0 0 8px; font-size: 1.6rem; }
        .lipsync-demo p { max-width: 40rem; line-height: 1.5; }
        .lipsync-demo__stage {
          position: relative;
          width: min(360px, 90vw);
          aspect-ratio: 1;
          margin: 24px 0;
          border-radius: 50%;
          overflow: hidden;
          border: 1px solid #d6c9a8;
          background: #111;
        }
        .lipsync-demo__row { display: flex; flex-wrap: wrap; gap: 8px; margin: 12px 0; }
        .lipsync-demo button {
          border: 0;
          border-radius: 8px;
          padding: 10px 14px;
          background: #15803d;
          color: #fff;
          cursor: pointer;
        }
        .lipsync-demo button:disabled { opacity: 0.6; cursor: wait; }
        .lipsync-demo label { display: grid; gap: 4px; font-size: 0.85rem; margin: 8px 0; max-width: 240px; }
        .lipsync-demo input[type="number"] { padding: 6px 8px; }
        .lipsync-demo code { background: #efe6d0; padding: 1px 4px; border-radius: 4px; }
      `}</style>
      <h1>Lip-sync demo</h1>
      <p>
        Canvas mouth deformation on the static Rafiki portrait. Play a clip and watch the mouth
        region. Sync should feel within about 50–100ms. Tune the box below or see{' '}
        <code>docs/LIPSYNC_AVATAR.md</code>.
      </p>
      <div className="lipsync-demo__stage">
        <TalkingAvatar
          imageUrl={rafikiAvatar}
          audioUrl={clip?.audioUrl}
          visemeTimeline={clip?.visemes}
          mouthRegion={region}
          playId={clip?.playId}
          debug={showBox}
          autoPlay
        />
      </div>
      <div className="lipsync-demo__row">
        {SAMPLES.map((sample) => (
          <button
            key={sample.id}
            type="button"
            disabled={busy}
            onClick={() => playSample(sample.text, sample.label)}
          >
            {sample.label}
          </button>
        ))}
        <button type="button" onClick={() => setShowBox((value) => !value)}>
          {showBox ? 'Hide mouth box' : 'Show mouth box'}
        </button>
      </div>
      <p>{status}</p>
      <p>{cueCount ? `${cueCount} cues in the last clip.` : null}</p>
      {(['x', 'y', 'width', 'height'] as const).map((key) => (
        <label key={key}>
          {key}
          <input
            type="number"
            step="0.005"
            min="0"
            max="1"
            value={region[key]}
            onChange={(event) =>
              setRegion((current) => ({ ...current, [key]: Number(event.target.value) }))
            }
          />
        </label>
      ))}
    </main>
  );
}
