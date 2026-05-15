import { useState } from 'react';
import type { AnalysisTask } from '../../types';
import StatusBadge from '../shared/StatusBadge';
import SecondaryButton from '../shared/SecondaryButton';
import PrimaryButton from '../shared/PrimaryButton';

interface Props {
  mediationTask?: AnalysisTask;
  onViewResult?: (taskId: number) => void;
  onRunTask?: (taskType: string) => void;
}

const DATA_SOURCES = [
  { value: 'decode', label: '冰岛血浆蛋白 pQTL 数据（4,907）' },
  { value: 'metabolite', label: '代谢物 GWAS 数据' },
  { value: 'gwas_catalog', label: 'GWAS Catalog / OpenGWAS' },
];

const TASKS = [
  { key: 'potential_mediators', label: '潜在中介因子', desc: '识别候选血浆蛋白中介因子' },
  { key: 'mediation_mr', label: '中介 MR 分析', desc: '两步孟德尔随机化分析' },
];

const RESULTS_DATA = [
  {
    mediator: 'FGF21',
    betaA: 0.284, betaB: 0.512, indirect: 0.145, se: 0.038,
    pval: '1.2×10⁻⁴', propMediated: '32.8%', significant: true,
  },
  {
    mediator: 'GDF15',
    betaA: 0.198, betaB: 0.447, indirect: 0.088, se: 0.029,
    pval: '2.6×10⁻³', propMediated: '19.9%', significant: true,
  },
  {
    mediator: 'IGFBP1',
    betaA: 0.156, betaB: 0.389, indirect: 0.061, se: 0.024,
    pval: '0.012', propMediated: '13.8%', significant: true,
  },
  {
    mediator: 'LEP',
    betaA: 0.122, betaB: 0.341, indirect: 0.042, se: 0.019,
    pval: '0.025', propMediated: '9.5%', significant: true,
  },
  {
    mediator: 'ADIPOQ',
    betaA: -0.094, betaB: 0.298, indirect: -0.028, se: 0.013,
    pval: '0.034', propMediated: '6.3%', significant: true,
  },
  {
    mediator: 'SHBG',
    betaA: 0.078, betaB: 0.265, indirect: 0.021, se: 0.011,
    pval: '0.058', propMediated: '4.7%', significant: false,
  },
];

export default function MediationMRModule({ mediationTask, onViewResult, onRunTask }: Props) {
  const [selectedSource, set已选中Source] = useState('decode');
  const hasMediation = mediationTask && mediationTask.id;
  const mediationSuccess = mediationTask?.status === 'success';

  return (
    <div className="space-y-4">
      {/* ===== Outer gold header ===== */}
      <div className="card-dashboard bg-gold-50/60 border-gold-200 overflow-hidden">
        {/* Title bar */}
        <div className="bg-gold-500/10 border-b border-gold-200 px-5 py-3 flex items-center gap-3">
          <span className="shrink-0 w-7 h-7 rounded-lg bg-gold-500 text-white flex items-center justify-center text-xs font-heading font-bold">
            C
          </span>
          <div>
            <h3 className="section-title text-gold-800">中介机制筛选</h3>
            <p className="text-xs text-gold-600/80 mt-0.5">
              发现连接脂肪性状与疾病结局的血浆蛋白中介因子
            </p>
          </div>
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-gold-500/15 border border-gold-300/50 text-xs font-heading font-medium text-gold-700 ml-auto">
            <span className="w-1.5 h-1.5 rounded-full bg-gold-500" />
            已选中
          </span>
        </div>

        {/* Inner title */}
        <div className="px-5 pt-4 pb-2">
          <div className="flex items-center gap-2">
            <svg className="w-4 h-4 text-gold-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 00-2.455 2.456z" />
            </svg>
            <h4 className="font-heading font-semibold text-base text-gold-800">中介 MR 分析</h4>
            {mediationTask && <StatusBadge status={mediationTask.status} />}
          </div>
        </div>

        {/* ===== Main content: 2 columns ===== */}
        <div className="px-5 pb-5 grid grid-cols-1 lg:grid-cols-5 gap-4">
          {/* ===== LEFT: Controls (2 cols) ===== */}
          <div className="lg:col-span-2 space-y-4">
            {/* 选择公共数据 */}
            <div className="bg-white rounded-xl border border-gold-200 p-4">
              <h5 className="font-heading font-semibold text-sm text-text-primary mb-3">
                选择公共数据
              </h5>

              {/* Data source descriptions */}
              <div className="space-y-2 mb-3">
                <div className="flex items-start gap-2">
                  <div className="w-1.5 h-1.5 rounded-full bg-gold-400 mt-1.5 shrink-0" />
                  <p className="text-xs text-text-secondary leading-relaxed">
                    4,907 种冰岛血浆蛋白 pQTL 数据，来源于 deCODE 遗传学研究
                  </p>
                </div>
                <div className="flex items-start gap-2">
                  <div className="w-1.5 h-1.5 rounded-full bg-teal-400 mt-1.5 shrink-0" />
                  <p className="text-xs text-text-secondary leading-relaxed">
                    代谢物 GWAS 汇总统计数据
                  </p>
                </div>
              </div>

              {/* Dropdown */}
              <div className="relative mb-3">
                <select
                  value={selectedSource}
                  onChange={(e) => set已选中Source(e.target.value)}
                  className="w-full appearance-none bg-surface border border-border rounded-lg px-3 py-2 text-sm text-text-primary font-medium cursor-pointer focus:outline-none focus:ring-2 focus:ring-gold-400/50 focus:border-gold-400"
                >
                  {DATA_SOURCES.map((ds) => (
                    <option key={ds.value} value={ds.value}>{ds.label}</option>
                  ))}
                </select>
                <svg className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted pointer-events-none" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
                </svg>
              </div>

              <PrimaryButton
                variant="gold"
                size="sm"
                className="w-full"
                onClick={() => {}}
              >
                选择公共数据
              </PrimaryButton>
            </div>

            {/* 已选中 Tasks */}
            <div className="bg-white rounded-xl border border-gold-200 p-4">
              <h5 className="font-heading font-semibold text-sm text-text-primary mb-3">
                已选中 tasks
              </h5>
              <div className="space-y-2">
                {TASKS.map((task) => {
                  const isMediationMr = task.key === 'mediation_mr';
                  const taskStatus = isMediationMr
                    ? (mediationTask?.status || 'pending')
                    : (mediationSuccess ? 'success' : 'pending');

                  const statusIcon = taskStatus === 'success'
                    ? (
                      <svg className="w-4 h-4 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                      </svg>
                    ) : taskStatus === 'running'
                    ? (
                      <svg className="w-4 h-4 text-navy-600 animate-spin" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                      </svg>
                    )
                    : (
                      <div className="w-4 h-4 rounded-full border-2 border-text-muted" />
                    );

                  return (
                    <div
                      key={task.key}
                      className={`flex items-center gap-3 p-2.5 rounded-lg transition-card ${
                        taskStatus === 'success' ? 'bg-green-50/50 border border-green-100' : 'bg-surface'
                      }`}
                    >
                      {statusIcon}
                      <div className="min-w-0 flex-1">
                        <p className="text-xs font-heading font-semibold text-text-primary">{task.label}</p>
                        <p className="text-[10px] text-text-muted mt-0.5">{task.desc}</p>
                      </div>
                      {taskStatus === 'success' && (
                        <span className="text-[10px] font-heading font-medium text-green-600">已完成</span>
                      )}
                      {taskStatus === 'running' && (
                        <span className="text-[10px] font-heading font-medium text-navy-600">运行中...</span>
                      )}
                    </div>
                  );
                })}
              </div>

              {/* Mediation task controls */}
              <div className="mt-4 pt-3 border-t border-border">
                {!hasMediation && onRunTask && (
                  <PrimaryButton
                    variant="gold"
                    size="sm"
                    className="w-full"
                    onClick={() => onRunTask('mediation_mr')}
                  >
                    运行中介 MR
                  </PrimaryButton>
                )}
                {mediationSuccess && onViewResult && (
                  <SecondaryButton
                    size="sm"
                    className="w-full"
                    onClick={() => onViewResult(mediationTask!.id)}
                  >
                    查看完整中介分析结果
                  </SecondaryButton>
                )}
              </div>
            </div>
          </div>

          {/* ===== RIGHT: Mechanism Diagram + Mediators (3 cols) ===== */}
          <div className="lg:col-span-3 space-y-4">
            {/* 机制流程图 Diagram */}
            <div className="bg-white rounded-xl border border-gold-200 p-4">
              <h5 className="font-heading font-semibold text-sm text-text-primary mb-4">
                潜在中介因子 — 机制流程图
              </h5>

              {/* Flow diagram */}
              <div className="flex items-center justify-center gap-2 py-4">
                {/* Adipose / Liver PDFF */}
                <div className="flex flex-col items-center gap-2">
                  <div className="w-16 h-16 rounded-2xl bg-red-50 border-2 border-red-200 flex items-center justify-center shadow-sm">
                    <svg width="32" height="32" viewBox="0 0 24 24" fill="none">
                      <path d="M12 3C8 3 5 7 5 10c0 4 3 8 7 11 4-3 7-7 7-11 0-3-3-7-7-7z" stroke="var(--color-danger-600)" strokeWidth="1.5" fill="var(--color-danger-100)" />
                      <circle cx="10" cy="9" r="1.5" fill="var(--color-danger-600)" opacity="0.6" />
                      <circle cx="13" cy="8" r="1" fill="var(--color-danger-600)" opacity="0.4" />
                    </svg>
                  </div>
                  <div className="text-center">
                    <p className="text-[11px] font-heading font-bold text-text-primary">脂肪组织</p>
                    <p className="text-[10px] text-text-muted">Liver PDFF</p>
                    <div className="mt-1 px-2 py-0.5 rounded-full bg-red-50 border border-red-100 text-[9px] font-medium text-red-600">
                      暴露因素
                    </div>
                  </div>
                </div>

                {/* Arrow 1: 间接效应 */}
                <div className="flex flex-col items-center px-2">
                  <div className="flex items-center">
                    <div className="h-0.5 w-8 bg-gold-400" />
                    <svg className="w-3 h-3 text-gold-500 -ml-0.5" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M5 12h14M12 5l7 7-7 7" />
                    </svg>
                  </div>
                  <span className="text-[9px] text-gold-600 font-medium mt-1 whitespace-nowrap">βᴬ = 0.284</span>
                  <span className="text-[8px] text-text-muted whitespace-nowrap">步骤一：暴露 → 中介</span>
                </div>

                {/* 血浆蛋白 */}
                <div className="flex flex-col items-center gap-2">
                  <div className="w-16 h-16 rounded-2xl bg-gold-100 border-2 border-gold-300 flex items-center justify-center shadow-sm">
                    <svg width="32" height="32" viewBox="0 0 24 24" fill="none">
                      <circle cx="12" cy="12" r="9" stroke="var(--color-gold-500)" strokeWidth="1.5" fill="var(--color-gold-100)" />
                      <circle cx="9" cy="10" r="2.2" fill="var(--color-gold-500)" opacity="0.6" />
                      <circle cx="14.5" cy="11" r="2.8" fill="var(--color-gold-500)" opacity="0.5" />
                      <circle cx="11" cy="15" r="2" fill="var(--color-gold-500)" opacity="0.4" />
                      <line x1="9" y1="10" x2="14.5" y2="11" stroke="var(--color-gold-500)" strokeWidth="0.8" opacity="0.4" />
                      <line x1="11" y1="15" x2="9" y2="10" stroke="var(--color-gold-500)" strokeWidth="0.8" opacity="0.4" />
                      <line x1="11" y1="15" x2="14.5" y2="11" stroke="var(--color-gold-500)" strokeWidth="0.8" opacity="0.4" />
                    </svg>
                  </div>
                  <div className="text-center">
                    <p className="text-[11px] font-heading font-bold text-text-primary">血浆蛋白</p>
                    <p className="text-[10px] text-text-muted">FGF21, GDF15, IGFBP1...</p>
                    <div className="mt-1 px-2 py-0.5 rounded-full bg-gold-50 border border-gold-200 text-[9px] font-medium text-gold-700">
                      中介因子
                    </div>
                  </div>
                </div>

                {/* Arrow 2: 直接效应 */}
                <div className="flex flex-col items-center px-2">
                  <div className="flex items-center">
                    <div className="h-0.5 w-8 bg-navy-400" />
                    <svg className="w-3 h-3 text-navy-600 -ml-0.5" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M5 12h14M12 5l7 7-7 7" />
                    </svg>
                  </div>
                  <span className="text-[9px] text-navy-600 font-medium mt-1 whitespace-nowrap">βᴮ = 0.512</span>
                  <span className="text-[8px] text-text-muted whitespace-nowrap">步骤二：中介 → 结局</span>
                </div>

                {/* 骨质疏松 */}
                <div className="flex flex-col items-center gap-2">
                  <div className="w-16 h-16 rounded-2xl bg-blue-50 border-2 border-blue-200 flex items-center justify-center shadow-sm">
                    <svg width="32" height="32" viewBox="0 0 24 24" fill="none">
                      <rect x="3" y="5" width="18" height="14" rx="3" stroke="var(--color-navy-600)" strokeWidth="1.5" fill="var(--color-blue-100)" />
                      <circle cx="8.5" cy="12" r="1.5" fill="var(--color-navy-600)" opacity="0.6" />
                      <circle cx="14" cy="12" r="1.5" fill="var(--color-navy-600)" opacity="0.4" />
                      <line x1="5" y1="14" x2="10.5" y2="14" stroke="var(--color-navy-600)" strokeWidth="1" opacity="0.3" />
                      <line x1="11.5" y1="14" x2="17" y2="14" stroke="var(--color-navy-600)" strokeWidth="1" opacity="0.3" />
                    </svg>
                  </div>
                  <div className="text-center">
                    <p className="text-[11px] font-heading font-bold text-text-primary">骨质疏松</p>
                    <p className="text-[10px] text-text-muted">骨密度 ↓</p>
                    <div className="mt-1 px-2 py-0.5 rounded-full bg-blue-50 border border-blue-100 text-[9px] font-medium text-blue-600">
                      结局变量
                    </div>
                  </div>
                </div>
              </div>

              {/* Total effect summary */}
              <div className="flex items-center justify-center gap-3 mt-2 pt-3 border-t border-border">
                <div className="text-center">
                  <span className="text-[10px] text-text-muted">间接效应</span>
                  <p className="text-sm font-heading font-bold text-gold-600">β = 0.145</p>
                  <p className="text-[9px] text-text-muted">32.8% mediated</p>
                </div>
                <div className="w-px h-8 bg-border" />
                <div className="text-center">
                  <span className="text-[10px] text-text-muted">直接效应</span>
                  <p className="text-sm font-heading font-bold text-navy-600">β = 0.297</p>
                  <p className="text-[9px] text-text-muted">67.2% direct</p>
                </div>
                <div className="w-px h-8 bg-border" />
                <div className="text-center">
                  <span className="text-[10px] text-text-muted">总效应</span>
                  <p className="text-sm font-heading font-bold text-text-primary">β = 0.442</p>
                  <p className="text-[9px] text-text-muted">p = 4.8×10⁻⁵</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* ===== Results Table (full width) ===== */}
        <div className="px-5 pb-5">
          <div className="bg-white rounded-xl border border-gold-200 p-4">
            <h5 className="font-heading font-semibold text-sm text-text-primary mb-3">
              中介 MR 分析结果
            </h5>
            <div className="table-scroll">
              <table className="w-full text-[11px]" aria-label="Mediation MR results table">
                <thead>
                  <tr className="text-text-muted border-b-2 border-border">
                    <th className="text-left py-2 px-2 font-heading font-semibold">中介因子</th>
                    <th className="text-right py-2 px-2 font-heading font-semibold">βᴬ (Exp.→Med.)</th>
                    <th className="text-right py-2 px-2 font-heading font-semibold">βᴮ (Med.→Out.)</th>
                    <th className="text-right py-2 px-2 font-heading font-semibold">间接效应</th>
                    <th className="text-right py-2 px-2 font-heading font-semibold">P value</th>
                    <th className="text-right py-2 px-2 font-heading font-semibold">Prop. Mediated</th>
                    <th className="text-center py-2 px-2 font-heading font-semibold">Significant</th>
                  </tr>
                </thead>
                <tbody>
                  {RESULTS_DATA.map((row, i) => (
                    <tr
                      key={row.mediator}
                      className={`border-b border-border-light last:border-0 transition-card ${
                        i % 2 === 0 ? 'bg-surface/50' : 'bg-white'
                      } hover:bg-gold-50/30`}
                    >
                      <td className="py-2 px-2">
                        <span className="font-heading font-semibold text-text-primary">{row.mediator}</span>
                      </td>
                      <td className={`py-2 px-2 text-right font-heading font-semibold ${row.betaA >= 0 ? 'text-text-primary' : 'text-danger-600'}`}>
                        {row.betaA > 0 ? '+' : ''}{row.betaA.toFixed(3)}
                      </td>
                      <td className="py-2 px-2 text-right font-heading font-semibold text-text-primary">
                        {row.betaB.toFixed(3)}
                      </td>
                      <td className={`py-2 px-2 text-right font-heading font-bold ${row.indirect > 0 ? 'text-gold-600' : 'text-danger-600'}`}>
                        {row.indirect > 0 ? '+' : ''}{row.indirect.toFixed(3)}
                        <span className="text-text-muted font-normal ml-0.5">±{row.se.toFixed(3)}</span>
                      </td>
                      <td className={`py-2 px-2 text-right font-heading font-semibold ${row.significant ? 'text-green-600' : 'text-text-muted'}`}>
                        {row.pval}
                      </td>
                      <td className="py-2 px-2 text-right">
                        <span className={`inline-flex items-center px-1.5 py-0.5 rounded-full text-[10px] font-heading font-semibold ${
                          row.significant ? 'bg-gold-50 text-gold-700' : 'bg-surface text-text-muted'
                        }`}>
                          {row.propMediated}
                        </span>
                      </td>
                      <td className="py-2 px-2 text-center">
                        {row.significant ? (
                          <svg className="w-4 h-4 text-green-500 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                          </svg>
                        ) : (
                          <span className="text-text-muted">—</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Legend */}
            <div className="flex items-center gap-4 mt-3 pt-2 border-t border-border text-[10px] text-text-muted">
              <span className="flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-gold-400" /> Indirect effect
              </span>
              <span className="flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-green-500" /> p &lt; 0.05
              </span>
              <span className="flex items-center gap-1">
                <span>路径 A：</span> 暴露 → 中介
              </span>
              <span className="flex items-center gap-1">
                <span>路径 B：</span> 中介 → 结局
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
