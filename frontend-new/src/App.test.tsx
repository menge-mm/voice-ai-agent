import { describe, it, expect } from 'vitest';

describe('App Setup', () => {
  it('test environment is configured', () => {
    expect(true).toBe(true);
  });

  it('vitest is working', () => {
    const sum = (a: number, b: number) => a + b;
    expect(sum(1, 2)).toBe(3);
  });
});
