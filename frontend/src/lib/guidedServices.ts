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

export const GUIDED_SERVICE_TITLES: Record<GuidedServiceSlug, string> = {
  'passport-apply': 'Apply for a Passport',
  'passport-renew': 'Renew a Passport',
  'ntsa-apply': 'Apply for a Driving Licence',
  'ntsa-renew': 'Renew Driving Licence',
  'ntsa-appointment': 'Book an NTSA Appointment',
  'id-replace': 'Replace a Lost ID',
  'brs-register': 'Register a Business',
  'dci-good-conduct': 'Police Clearance',
  'kra-pin': 'Register for a KRA PIN',
  'kra-itax': 'KRA iTax',
  'kra-nil': 'File Nil Returns',
  'land-rates': 'Land Services',
  nhif: 'NHIF Registration',
  ncpwd: 'NCPWD Services',
  ntsa: 'NTSA Services',
  kra: 'KRA Services',
  brs: 'BRS Services',
  dci: 'DCI Services',
  immigration: 'Immigration Services',
  health: 'Ministry of Health',
  'boma-yangu': 'Boma Yangu',
  county: 'County Services',
  nrb: 'National Registration Bureau',
  agencies: 'All Agencies',
  huduma: 'Huduma Centre Lookup',
  emergency: 'Emergency Reporting',
};

const PENDING_SERVICE_KEY = 'rafiki_pending_service';

export function isGuidedServiceSlug(value: string | null | undefined): value is GuidedServiceSlug {
  return !!value && (GUIDED_SERVICE_SLUGS as readonly string[]).includes(value);
}

export function titleForService(slug: string): string {
  return isGuidedServiceSlug(slug) ? GUIDED_SERVICE_TITLES[slug] : slug;
}

/** Chat path that opens a specific service after sign-in. */
export function chatPathForService(slug: string, language?: 'en' | 'sw'): string {
  const params = new URLSearchParams({ service: slug });
  if (language) params.set('lang', language);
  return `/chat?${params.toString()}`;
}

export function rememberPendingService(slug: string): void {
  if (!isGuidedServiceSlug(slug)) return;
  try {
    sessionStorage.setItem(PENDING_SERVICE_KEY, slug);
  } catch {
    /* ignore quota / private mode */
  }
}

export function readPendingService(): GuidedServiceSlug | null {
  try {
    const stored = sessionStorage.getItem(PENDING_SERVICE_KEY);
    return isGuidedServiceSlug(stored) ? stored : null;
  } catch {
    return null;
  }
}

export function clearPendingService(): void {
  try {
    sessionStorage.removeItem(PENDING_SERVICE_KEY);
  } catch {
    /* ignore */
  }
}

function decodeMaybe(value: string): string {
  try {
    return decodeURIComponent(value);
  } catch {
    return value;
  }
}

/** Pull a service slug out of a next path like /chat?service=ntsa-renew. */
export function serviceFromNext(next: string | null | undefined): GuidedServiceSlug | null {
  if (!next) return null;
  const decoded = decodeMaybe(next);
  const queryIndex = decoded.indexOf('?');
  if (queryIndex === -1) return null;
  const nested = new URLSearchParams(decoded.slice(queryIndex + 1));
  const slug = nested.get('service');
  return isGuidedServiceSlug(slug) ? slug : null;
}

/**
 * Resolve where to go after login/signup.
 * Prefer a first-class `service` query param so nested next=/chat?service=…
 * cannot be truncated by URLSearchParams.
 */
export function destinationAfterAuth(searchParams: URLSearchParams): string {
  const fromQuery = searchParams.get('service');
  const slug =
    (isGuidedServiceSlug(fromQuery) ? fromQuery : null) ||
    serviceFromNext(searchParams.get('next')) ||
    readPendingService();

  if (slug) {
    rememberPendingService(slug);
    return chatPathForService(slug);
  }

  return safeAuthNext(searchParams.get('next'));
}

/** Login path that continues into a specific service. */
export function loginPathForService(slug: string): string {
  rememberPendingService(slug);
  const params = new URLSearchParams({
    service: slug,
    next: chatPathForService(slug),
  });
  return `/login?${params.toString()}`;
}

/** Only allow in-app redirects after login (blocks open redirects). */
export function safeAuthNext(next: string | null | undefined): string {
  if (!next) return '/chat';
  const decoded = decodeMaybe(next);
  if (decoded.startsWith('/chat')) return decoded;
  return '/chat';
}
