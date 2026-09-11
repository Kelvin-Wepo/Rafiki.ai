/** Canonical ElevenLabs Conversational AI agent (voice + prompt live in ElevenLabs). */
export const RAFIKI_ELEVENLABS_AGENT_ID = 'agent_8201m28ec9h6fs3vwcvtg1dvnrzq';

export function agentMessageText(message: unknown): { source: 'ai' | 'user' | 'unknown'; text: string } | null {
  if (!message) return null;
  if (typeof message === 'string') {
    const text = message.trim();
    return text ? { source: 'unknown', text } : null;
  }
  if (typeof message !== 'object') return null;

  const record = message as Record<string, unknown>;
  const text = String(
    record.message ??
      record.text ??
      (record.agent_response_event as { agent_response?: string } | undefined)?.agent_response ??
      (record.user_transcription_event as { user_transcript?: string } | undefined)?.user_transcript ??
      ''
  ).trim();
  if (!text) return null;

  const rawSource = String(record.source ?? record.role ?? record.type ?? '').toLowerCase();
  const source: 'ai' | 'user' | 'unknown' =
    rawSource.includes('ai') || rawSource.includes('agent') || rawSource === 'assistant'
      ? 'ai'
      : rawSource.includes('user')
        ? 'user'
        : 'unknown';
  return { source, text };
}
