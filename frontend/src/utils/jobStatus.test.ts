import { describe, it, expect } from 'vitest';
import {
  normalizeJobStatus,
  isTerminal,
  isSuccess,
  isFailed,
  isRunning,
  isActive,
  isSuccessRaw,
  isFailedRaw,
  isTerminalRaw,
  isActiveRaw,
} from './jobStatus';

describe('normalizeJobStatus', () => {
  it('maps success variants to succeeded', () => {
    expect(normalizeJobStatus('success')).toBe('succeeded');
    expect(normalizeJobStatus('succeeded')).toBe('succeeded');
    expect(normalizeJobStatus('completed')).toBe('succeeded');
    expect(normalizeJobStatus('complete')).toBe('succeeded');
  });

  it('maps pending/queued to queued', () => {
    expect(normalizeJobStatus('pending')).toBe('queued');
    expect(normalizeJobStatus('queued')).toBe('queued');
  });

  it('maps running/processing to running', () => {
    expect(normalizeJobStatus('running')).toBe('running');
    expect(normalizeJobStatus('processing')).toBe('running');
  });

  it('maps failed/error to failed', () => {
    expect(normalizeJobStatus('failed')).toBe('failed');
    expect(normalizeJobStatus('error')).toBe('failed');
  });

  it('maps cancelled/canceled to cancelled', () => {
    expect(normalizeJobStatus('cancelled')).toBe('cancelled');
    expect(normalizeJobStatus('canceled')).toBe('cancelled');
  });

  it('returns unknown for null/undefined/empty', () => {
    expect(normalizeJobStatus(null)).toBe('unknown');
    expect(normalizeJobStatus(undefined)).toBe('unknown');
    expect(normalizeJobStatus('')).toBe('unknown');
    expect(normalizeJobStatus('bogus_status')).toBe('unknown');
  });

  it('is case-insensitive and trim-tolerant', () => {
    expect(normalizeJobStatus('  SUCCESS  ')).toBe('succeeded');
    expect(normalizeJobStatus('Failed')).toBe('failed');
  });
});

describe('status type guards', () => {
  it('isTerminal', () => {
    expect(isTerminal('succeeded')).toBe(true);
    expect(isTerminal('failed')).toBe(true);
    expect(isTerminal('cancelled')).toBe(true);
    expect(isTerminal('running')).toBe(false);
    expect(isTerminal('queued')).toBe(false);
  });

  it('isSuccess', () => {
    expect(isSuccess('succeeded')).toBe(true);
    expect(isSuccess('failed')).toBe(false);
  });

  it('isFailed', () => {
    expect(isFailed('failed')).toBe(true);
    expect(isFailed('succeeded')).toBe(false);
  });

  it('isRunning', () => {
    expect(isRunning('running')).toBe(true);
    expect(isRunning('succeeded')).toBe(false);
  });

  it('isActive', () => {
    expect(isActive('queued')).toBe(true);
    expect(isActive('running')).toBe(true);
    expect(isActive('succeeded')).toBe(false);
    expect(isActive('failed')).toBe(false);
  });
});

describe('Raw string helpers', () => {
  it('isSuccessRaw handles both success and succeeded', () => {
    expect(isSuccessRaw('success')).toBe(true);
    expect(isSuccessRaw('succeeded')).toBe(true);
    expect(isSuccessRaw('completed')).toBe(true);
    expect(isSuccessRaw('failed')).toBe(false);
    expect(isSuccessRaw('running')).toBe(false);
  });

  it('isFailedRaw handles failed and error', () => {
    expect(isFailedRaw('failed')).toBe(true);
    expect(isFailedRaw('error')).toBe(true);
    expect(isFailedRaw('success')).toBe(false);
  });

  it('isTerminalRaw handles all terminal variants', () => {
    expect(isTerminalRaw('succeeded')).toBe(true);
    expect(isTerminalRaw('success')).toBe(true);
    expect(isTerminalRaw('failed')).toBe(true);
    expect(isTerminalRaw('cancelled')).toBe(true);
    expect(isTerminalRaw('running')).toBe(false);
  });

  it('isActiveRaw handles pending/queued and running', () => {
    expect(isActiveRaw('pending')).toBe(true);
    expect(isActiveRaw('queued')).toBe(true);
    expect(isActiveRaw('running')).toBe(true);
    expect(isActiveRaw('succeeded')).toBe(false);
    expect(isActiveRaw('failed')).toBe(false);
  });
});

describe('Regression guards: status cross-compatibility', () => {
  // Guards against the bug where old AnalysisTask uses 'success' but
  // new JobManager uses 'succeeded' — both must normalize identically.
  it('old API "success" === new API "succeeded" after normalize', () => {
    expect(normalizeJobStatus('success')).toBe(normalizeJobStatus('succeeded'));
  });

  it('old API "pending" === new API "queued" after normalize', () => {
    expect(normalizeJobStatus('pending')).toBe(normalizeJobStatus('queued'));
  });

  it('isSuccessRaw treats both old and new equally', () => {
    expect(isSuccessRaw('success')).toBe(isSuccessRaw('succeeded'));
  });

  it('isActiveRaw treats pending as active', () => {
    expect(isActiveRaw('pending')).toBe(true);
  });
});
