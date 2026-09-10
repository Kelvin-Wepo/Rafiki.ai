/**
 * Frontend slugs for agency workflows.
 * Must stay in sync with backend GUIDED_SERVICES in agency_workflows.py.
 */

export const GUIDED_SERVICE_SLUGS = [
  'passport-apply',
  'passport-renew',
  'ntsa-apply',
  'ntsa-renew',
  'ntsa-appointment',
  'id-replace',
  'brs-register',
  'dci-good-conduct',
  'kra-pin',
  'kra-itax',
  'kra-nil',
  'land-rates',
  'nhif',
  'ncpwd',
  'ntsa',
  'kra',
  'brs',
  'dci',
  'immigration',
  'health',
  'boma-yangu',
  'county',
  'nrb',
  'agencies',
  'huduma',
  'emergency',
] as const;

export type GuidedServiceSlug = (typeof GUIDED_SERVICE_SLUGS)[number];

export function isGuidedServiceSlug(value: string | null | undefined): value is GuidedServiceSlug {
  return !!value && (GUIDED_SERVICE_SLUGS as readonly string[]).includes(value);
}

/** Chat path that opens a specific service after sign-in. */
export function chatPathForService(slug: string, language?: 'en' | 'sw'): string {
  const params = new URLSearchParams({ service: slug });
  if (language) params.set('lang', language);
  return `/chat?${params.toString()}`;
}

/** Login path that continues into a specific service. */
export function loginPathForService(slug: string): string {
  return `/login?next=${encodeURIComponent(chatPathForService(slug))}`;
}

/** Only allow in-app redirects after login (blocks open redirects). */
export function safeAuthNext(next: string | null | undefined): string {
  if (!next) return '/chat';
  let decoded = next;
  try {
    decoded = decodeURIComponent(next);
  } catch {
    decoded = next;
  }
  if (decoded.startsWith('/chat')) return decoded;
  return '/chat';
}
