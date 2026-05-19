import { describe, it, expect } from 'vitest';
import { computePipelineProgress, normalizeTaskStep } from './pipelineProgress';
import type { AnalysisTask } from '../types';

// Helper to create a minimal mock task
function makeTask(overrides: Partial<AnalysisTask> & { task_type: string }): AnalysisTask {
  const now = '2026-05-19T00:00:00Z';
  return {
    id: 1,
    project_id: 1,
    task_name: overrides.task_type,
    status: 'pending',
    progress: 0,
    input_json: '{}',
    output_json: '{}',
    error_code: '',
    error_message: '',
    started_at: null,
    finished_at: null,
    created_at: now,
    updated_at: now,
    ...overrides,
  };
}

const PIPELINE = [
  'image_segmentation',
  'gwas_analysis',
  'opengwas_fetch',
  'mendelian_randomization',
  'mediation_mr',
  'risk_modeling',
  'report_generation',
];

describe('normalizeTaskStep', () => {
  it('returns task_type for standard tasks', () => {
    const task = makeTask({ task_type: 'gwas_analysis' });
    expect(normalizeTaskStep(task)).toBe('gwas_analysis');
  });

  it('trims whitespace', () => {
    const task = makeTask({ task_type: '  mediation_mr ' });
    expect(normalizeTaskStep(task)).toBe('mediation_mr');
  });

  it('returns _unknown_ for empty task_type', () => {
    const task = makeTask({ task_type: '' });
    expect(normalizeTaskStep(task)).toBe('_unknown_');
  });
});

describe('computePipelineProgress', () => {
  it('empty tasks → 0/7, 0%', () => {
    const p = computePipelineProgress([], PIPELINE);
    expect(p.completed).toBe(0);
    expect(p.running).toBe(0);
    expect(p.failed).toBe(0);
    expect(p.total).toBe(7);
    expect(p.percent).toBe(0);
    expect(p.extraTaskCount).toBe(0);
  });

  it('one success per step → 7/7, 100%', () => {
    const tasks = PIPELINE.map((tt, i) =>
      makeTask({ id: i + 1, task_type: tt, status: 'success' }));
    const p = computePipelineProgress(tasks, PIPELINE);
    expect(p.completed).toBe(7);
    expect(p.total).toBe(7);
    expect(p.percent).toBe(100);
  });

  it('duplicate GWAS tasks → counts only once', () => {
    // Simulate: user ran GWAS first, then full pipeline created second GWAS
    const tasks = [
      makeTask({ id: 1, task_type: 'gwas_analysis', status: 'success', finished_at: '2026-01-01T00:00:00Z' }),
      makeTask({ id: 2, task_type: 'gwas_analysis', status: 'success', finished_at: '2026-01-02T00:00:00Z' }),
    ];
    const p = computePipelineProgress(tasks, PIPELINE);
    // completed should be 1 for gwas_analysis, plus 6 pending = 7 total
    expect(p.completed).toBe(1);
    expect(p.total).toBe(7);
    expect(p.percent).toBe(14); // 1/7 ≈ 14%
    // GWAS step should have taskCount=2
    const gwasStep = p.steps.find(s => s.step === 'gwas_analysis');
    expect(gwasStep?.taskCount).toBe(2);
    expect(gwasStep?.status).toBe('succeeded');
  });

  it('full pipeline with one duplicate GWAS → max 7/7', () => {
    const tasks = [
      ...PIPELINE.map((tt, i) =>
        makeTask({ id: i + 1, task_type: tt, status: 'success' })),
      // extra GWAS
      makeTask({ id: 99, task_type: 'gwas_analysis', status: 'success' }),
    ];
    const p = computePipelineProgress(tasks, PIPELINE);
    expect(p.completed).toBe(7); // capped at total
    expect(p.percent).toBe(100);
  });

  it('status priority: success wins over running, failed in same step', () => {
    const tasks = [
      makeTask({ id: 1, task_type: 'gwas_analysis', status: 'failed' }),
      makeTask({ id: 2, task_type: 'gwas_analysis', status: 'running' }),
      makeTask({ id: 3, task_type: 'gwas_analysis', status: 'success' }),
    ];
    const p = computePipelineProgress(tasks, PIPELINE);
    expect(p.completed).toBe(1);
    expect(p.failed).toBe(0); // success overrides
  });

  it('running has priority over failed', () => {
    const tasks = [
      makeTask({ id: 1, task_type: 'gwas_analysis', status: 'failed' }),
      makeTask({ id: 2, task_type: 'gwas_analysis', status: 'running' }),
    ];
    const p = computePipelineProgress(tasks, PIPELINE);
    expect(p.running).toBe(1);
    expect(p.completed).toBe(0);
  });

  it('failed step counts as failed, not completed', () => {
    const tasks = [
      makeTask({ id: 1, task_type: 'gwas_analysis', status: 'failed' }),
    ];
    const p = computePipelineProgress(tasks, PIPELINE);
    expect(p.failed).toBe(1);
    expect(p.completed).toBe(0);
    expect(p.percent).toBe(0);
  });

  it('unknown task_type does not affect pipeline counts', () => {
    const tasks = [
      makeTask({ id: 1, task_type: 'gwas_analysis', status: 'success' }),
      makeTask({ id: 2, task_type: 'custom_analysis', status: 'success' }),
    ];
    const p = computePipelineProgress(tasks, PIPELINE);
    expect(p.completed).toBe(1); // only gwas
    expect(p.extraTaskCount).toBe(1); // custom_analysis
  });

  it('_unknown_ tasks counted as extra', () => {
    const tasks = [
      makeTask({ id: 1, task_type: '' }),
    ];
    const p = computePipelineProgress(tasks, PIPELINE);
    expect(p.completed).toBe(0);
    expect(p.extraTaskCount).toBe(1);
  });

  it('all statuses mixed → correct counts', () => {
    const tasks = [
      makeTask({ id: 1, task_type: 'image_segmentation', status: 'success' }),
      makeTask({ id: 2, task_type: 'gwas_analysis', status: 'running' }),
      makeTask({ id: 3, task_type: 'opengwas_fetch', status: 'failed' }),
      makeTask({ id: 4, task_type: 'mendelian_randomization', status: 'pending' }),
      makeTask({ id: 5, task_type: 'mediation_mr', status: 'cancelled' }),
    ];
    const p = computePipelineProgress(tasks, PIPELINE);
    expect(p.completed).toBe(1);
    expect(p.running).toBe(1);
    expect(p.failed).toBe(1);
    expect(p.pending).toBe(4); // 2 pipeline steps pending + unknown steps
    expect(p.percent).toBe(14); // 1/7
  });

  it('percent never exceeds 100 even with many duplicates', () => {
    const tasks = PIPELINE.flatMap((tt, i) => [
      makeTask({ id: i * 10 + 1, task_type: tt, status: 'success' }),
      makeTask({ id: i * 10 + 2, task_type: tt, status: 'success' }),
      makeTask({ id: i * 10 + 3, task_type: tt, status: 'success' }),
    ]); // 21 tasks, 3 per step, all success
    const p = computePipelineProgress(tasks, PIPELINE);
    expect(p.completed).toBe(7);
    expect(p.percent).toBe(100);
  });
});

describe('Regression guards: critical bugs that must not regress', () => {
  it('BUGFIX: progress never exceeds 100% even with all duplicates', () => {
    // Simulate 3 full pipeline runs → 21 tasks, all success
    const tasks: AnalysisTask[] = [];
    for (let run = 0; run < 3; run++) {
      PIPELINE.forEach((tt, i) => {
        tasks.push(makeTask({ id: run * 10 + i + 1, task_type: tt, status: 'success' }));
      });
    }
    const p = computePipelineProgress(tasks, PIPELINE);
    expect(p.percent).toBeLessThanOrEqual(100);
    expect(p.completed).toBeLessThanOrEqual(p.total);
  });

  it('BUGFIX: 8/7 display never occurs (duplicate GWAS scenario)', () => {
    // Simulate: run GWAS separately, then full pipeline
    const tasks = [
      makeTask({ id: 1, task_type: 'gwas_analysis', status: 'success' }),
      ...PIPELINE.map((tt, i) => makeTask({ id: i + 10, task_type: tt, status: 'success' })),
    ];
    const p = computePipelineProgress(tasks, PIPELINE);
    expect(p.completed).toBe(7);
    expect(p.percent).toBe(100);
    // Display text should always be ≤ total
    expect(`${p.completed}/${p.total}`).toBe('7/7');
  });

  it('BUGFIX: unknown task types do not inflate completed count', () => {
    const tasks = [
      makeTask({ id: 1, task_type: 'gwas_analysis', status: 'success' }),
      makeTask({ id: 2, task_type: 'custom_analysis', status: 'success' }),
      makeTask({ id: 3, task_type: 'another_unknown', status: 'success' }),
    ];
    const p = computePipelineProgress(tasks, PIPELINE);
    expect(p.completed).toBe(1); // only gwas
    expect(p.extraTaskCount).toBe(2);
  });

  it('BUGFIX: progress is 0% when all tasks failed', () => {
    const tasks = PIPELINE.map((tt, i) =>
      makeTask({ id: i + 1, task_type: tt, status: 'failed' }));
    const p = computePipelineProgress(tasks, PIPELINE);
    expect(p.percent).toBe(0);
    expect(p.completed).toBe(0);
    expect(p.failed).toBe(7);
  });

  it('BUGFIX: empty pipeline returns sensible defaults', () => {
    const p = computePipelineProgress([], []);
    expect(p.percent).toBe(0);
    expect(p.total).toBe(0);
    expect(p.completed).toBe(0);
  });
});
