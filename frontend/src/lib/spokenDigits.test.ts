import { describe, expect, it } from 'vitest';
import {
  digitsFromSpeech,
  parseKenyanId,
  parseKenyanPhone,
  parseOtpCode,
  parseSpokenName,
  parseYesNo,
} from './spokenDigits';

describe('spokenDigits', () => {
  it('reads English digit words', () => {
    expect(digitsFromSpeech('zero seven one two three four five six seven eight')).toBe(
      '0712345678'
    );
  });

  it('reads Kiswahili digit words', () => {
    expect(digitsFromSpeech('sifuri saba moja mbili tatu nne tano sita saba nane')).toBe(
      '0712345678'
    );
  });

  it('parses a Kenyan mobile number from speech', () => {
    expect(parseKenyanPhone('zero seven one two three four five six seven eight')).toBe(
      '+254712345678'
    );
    expect(parseKenyanPhone('plus two five four seven one two three four five six seven eight')).toBe(
      '+254712345678'
    );
    expect(parseKenyanPhone('0712 345 678')).toBe('+254712345678');
  });

  it('parses a 7 or 8 digit national ID', () => {
    expect(parseKenyanId('three two four five six seven eight nine')).toBe('32456789');
    expect(parseKenyanId('1234567')).toBe('1234567');
    expect(parseKenyanId('12')).toBeNull();
  });

  it('parses a six-digit OTP', () => {
    expect(parseOtpCode('one two three four five six')).toBe('123456');
    expect(parseOtpCode('123456')).toBe('123456');
  });

  it('strips name preambles', () => {
    expect(parseSpokenName('my name is Jane Wanjiku')).toBe('Jane Wanjiku');
    expect(parseSpokenName('ninaitwa Amina Hassan')).toBe('Amina Hassan');
  });

  it('detects yes and no', () => {
    expect(parseYesNo('ndiyo')).toBe('yes');
    expect(parseYesNo('hapana')).toBe('no');
    expect(parseYesNo('maybe')).toBeNull();
  });
});
