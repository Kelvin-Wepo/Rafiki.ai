/**
 * Turn spoken English / Kiswahili into Kenyan ID, phone, OTP, or a name.
 */

const DIGIT_WORDS: Record<string, string> = {
  zero: '0',
  oh: '0',
  o: '0',
  nought: '0',
  sifuri: '0',
  one: '1',
  moja: '1',
  two: '2',
  too: '2',
  to: '2',
  mbili: '2',
  three: '3',
  tree: '3',
  tatu: '3',
  four: '4',
  for: '4',
  nne: '4',
  five: '5',
  tano: '5',
  six: '6',
  sita: '6',
  seven: '7',
  saba: '7',
  eight: '8',
  ate: '8',
  nane: '8',
  nine: '9',
  niner: '9',
  tisa: '9',
  plus: '',
  and: '',
  na: '',
};

const NAME_PREFIXES = [
  /^my name is\s+/i,
  /^i am\s+/i,
  /^i'm\s+/i,
  /^it is\s+/i,
  /^it's\s+/i,
  /^call me\s+/i,
  /^ninaitwa\s+/i,
  /^nimeitwa\s+/i,
  /^jina langu ni\s+/i,
  /^jina langu\s+/i,
  /^mimi ni\s+/i,
];

const YES = /^(yes|yeah|yep|correct|right|ndiyo|sawa|sahihi|confirm|ok|okay|1)$/i;
const NO = /^(no|nope|wrong|hapana|siyo|repeat|again|2)$/i;

function tokenize(raw: string): string[] {
  return raw
    .toLowerCase()
    .replace(/[+,.\-_/]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
    .split(' ')
    .filter(Boolean);
}

export function digitsFromSpeech(raw: string): string {
  const tokens = tokenize(raw);
  let digits = '';
  for (const token of tokens) {
    if (/^\d+$/.test(token)) {
      digits += token;
      continue;
    }
    if (token in DIGIT_WORDS) {
      digits += DIGIT_WORDS[token];
    }
  }
  return digits;
}

export function parseKenyanPhone(raw: string): string | null {
  let digits = digitsFromSpeech(raw);
  if (digits.startsWith('254') && digits.length >= 12) {
    digits = digits.slice(-9);
  } else if (digits.startsWith('0') && digits.length >= 10) {
    digits = digits.slice(1, 10);
  } else if (digits.length === 9) {
    // already without leading 0 / 254
  } else if (digits.length > 9) {
    digits = digits.slice(-9);
  }

  if (!/^[17]\d{8}$/.test(digits)) return null;
  return `+254${digits}`;
}

export function parseKenyanId(raw: string): string | null {
  const digits = digitsFromSpeech(raw);
  if (/^\d{7,8}$/.test(digits)) return digits;
  return null;
}

export function parseOtpCode(raw: string): string | null {
  const digits = digitsFromSpeech(raw);
  if (/^\d{6}$/.test(digits)) return digits;
  return null;
}

export function parseSpokenName(raw: string): string | null {
  let text = raw.trim();
  for (const prefix of NAME_PREFIXES) {
    text = text.replace(prefix, '');
  }
  text = text.replace(/[^a-zA-Z\s'-]/g, ' ').replace(/\s+/g, ' ').trim();
  if (text.length < 3) return null;
  const titled = text
    .split(' ')
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1).toLowerCase())
    .join(' ');
  return titled.length >= 3 ? titled : null;
}

export function parseYesNo(raw: string): 'yes' | 'no' | null {
  const text = raw.trim();
  if (YES.test(text)) return 'yes';
  if (NO.test(text)) return 'no';
  return null;
}

export function formatPhoneForSpeech(phone: string): string {
  const local = phone.replace(/^\+254/, '0');
  return local.split('').join(' ');
}
