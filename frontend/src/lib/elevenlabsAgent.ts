/** Runtime ElevenLabs agent — loaded from GET /elevenlabs/config, not a hardcoded ID. */

export const RAFIKI_AGENT_ID = 'agent_8201m28ec9h6fs3vwcvtg1dvnrzq';
export const JUA_AGENT_ID = 'agent_5601kydx2f3vetnv3e9yf9tmam58';
export const WANJIKU_AGENT_ID = 'agent_0601kbntk14cet68q60vzy6y55v7';

export type ElevenLabsRuntimeConfig = {
  success: boolean;
  configured?: boolean;
  agent_id?: string;
  name?: string;
  voice_id?: string;
  tts_model?: string;
  branch_id?: string;
  first_message?: string;
  language?: string;
  api_key_hint?: string;
  error?: string;
};

export async function fetchElevenLabsConfig(apiBase: string): Promise<ElevenLabsRuntimeConfig> {
  const response = await fetch(`${apiBase}/elevenlabs/config`);
  if (!response.ok) {
    return { success: false, error: `Could not load voice config (${response.status})` };
  }
  const config = (await response.json()) as ElevenLabsRuntimeConfig;
  return {
    ...config,
    agent_id: ensureRafikiAgentId(config.agent_id, config.name, config.first_message),
  };
}

export function ensureRafikiAgentId(
  agentId?: string,
  name?: string,
  firstMessage?: string
): string {
  const id = (agentId || '').trim();
  const blob = `${name || ''} ${firstMessage || ''}`.toLowerCase();
  if (!id || id === JUA_AGENT_ID || id === WANJIKU_AGENT_ID || /\bjua\b/.test(blob)) {
    return RAFIKI_AGENT_ID;
  }
  return id;
}

export function agentMessageText(message: unknown): { source: 'ai' | 'user' | 'unknown'; text: string } | null {
  if (!message) return null;
  if (typeof message !== 'object') {
    if (typeof message === 'string') {
      const text = message.trim();
      return text ? { source: 'unknown', text } : null;
    }
    return null;
  }

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
