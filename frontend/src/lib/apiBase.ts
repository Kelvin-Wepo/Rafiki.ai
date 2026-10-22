/**
 * Backend origin for fetch/axios.
 * In Vite dev, leave this empty so requests stay on the same host and the
 * dev-server proxy forwards them — that avoids CORS and "Failed to fetch"
 * when the UI is opened as 127.0.0.1 but the API is localhost (or vice versa).
 */
export const API_BASE_URL: string =
  import.meta.env.VITE_API_URL || (import.meta.env.DEV ? '' : 'http://localhost:8000');

export function isUnreachableServerError(err: unknown): boolean {
  if (err instanceof TypeError && /fetch|network/i.test(err.message)) return true;
  if (err && typeof err === 'object' && 'message' in err) {
    return /failed to fetch|networkerror|load failed/i.test(String((err as { message: unknown }).message));
  }
  return false;
}

export function unreachableServerMessage(): string {
  return 'Cannot reach the Rafiki server. Start the backend on port 8000, then try again.';
}
