import { type ReactNode } from 'react';
import { MessageSquareText, Mic } from 'lucide-react';

interface VoiceSectionProps {
  avatar: ReactNode;
  connected: boolean;
  speaking: boolean;
  lastReply: string | null;
  agentName?: string;
  onStart: () => void;
  onStop: () => void;
  onOpenChat: () => void;
}

export function VoiceSection({
  avatar,
  connected,
  speaking,
  lastReply,
  agentName,
  onStart,
  onStop,
  onOpenChat,
}: VoiceSectionProps) {
  const status = speaking ? 'Speaking' : connected ? 'Listening' : 'Ready';
  const name = agentName || 'Rafiki';

  return (
    <section className="rd-voice" aria-label="Voice with Rafiki">
      <div className="rd-mode-switch" role="tablist" aria-label="Choose Chat or Voice">
        <button type="button" role="tab" aria-selected={false} onClick={onOpenChat}>
          <MessageSquareText size={16} strokeWidth={2} aria-hidden="true" />
          Chat
        </button>
        <button type="button" role="tab" aria-selected={true} className="is-active">
          <Mic size={16} strokeWidth={2} aria-hidden="true" />
          Voice
        </button>
      </div>

      <div className="rd-voice-layout">
        <div className="rd-voice-stage">
          <div className="rd-voice-avatar">{avatar}</div>
          <p className="rd-voice-agent">{name}</p>
        </div>

        <div className="rd-voice-panel">
          <h1>Talk to {name}</h1>
          <p className="rd-voice-copy">
            Speak with the Rafiki voice agent. Switch to Chat if you would rather type.
          </p>
          <div
            className={`rd-assistant-state${connected || speaking ? ' rd-assistant-state--live' : ''}`}
            role="status"
          >
            <span className="rd-assistant-dot" aria-hidden="true" />
            <span>{status}</span>
          </div>
          <p className="rd-assistant-copy">
            {lastReply || `${name} is ready. Press start and say how they can help.`}
          </p>
          <button
            type="button"
            className={`rd-btn-primary${connected ? ' rd-btn-primary--stop' : ''}`}
            onClick={connected ? onStop : onStart}
          >
            <Mic size={17} strokeWidth={1.75} aria-hidden="true" />
            {connected ? 'End voice' : 'Start voice'}
          </button>
        </div>
      </div>
    </section>
  );
}

export default VoiceSection;
