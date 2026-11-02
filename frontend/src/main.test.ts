import { describe, expect, it } from 'vitest';
import { formatValue } from './utils';

describe('formatValue', () => {
  it('shows missing values explicitly', () => {
    expect(formatValue(null, ' MW')).toBe('N/A');
    expect(formatValue(undefined)).toBe('N/A');
  });

  it('formats a numeric MW reading with its unit', () => {
    expect(formatValue(42, ' MW')).toBe('42 MW');
  });

  it('formats large readings with locale separators and one decimal place', () => {
    expect(formatValue(2127.46, ' MW')).toBe('2,127.5 MW');
  });
});
