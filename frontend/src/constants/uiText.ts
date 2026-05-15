/**
 * AdipoInsight 中文文案配置
 * 所有 UI 展示文案集中管理，避免散落硬编码
 */

// ===== 品牌与导航 =====
export const BRAND = {
  name: 'AdipoInsight',
  tagline: '医学科研 AI 分析平台',
  version: 'v0.1.0 Mock-First',
};

export const NAV = {
  myData: '我的数据',
  analysisCenter: '分析中心',
  userMenu: '用户中心',
};

// ===== 项目与状态 =====
export const PROJECT = {
  demoName: '示例任务：肝脏 PDFF 与骨质疏松',
  demoGoal: '研究肝脏脂肪（Liver PDFF）与骨质疏松风险之间的因果关系，并通过血浆蛋白进行中介分析',
  exposure: '暴露因素',
  outcome: '结局变量',
  mediator: '中介变量',
  newProject: '新建项目',
  oneClickDemo: '一键创建示例',
  projects: '项目列表',
  projectSubtitle: '管理您的医学科研分析项目',
  noProjects: '暂无项目',
  noProjectsHint: '点击"一键创建示例"或"新建项目"开始使用',
  loading: '加载中...',
  status: '状态',
};

// ===== 任务状态 =====
export const STATUS: Record<string, string> = {
  pending: '待开始',
  running: '运行中',
  success: '已完成',
  failed: '失败',
  cancelled: '已取消',
  active: '进行中',
};

// ===== 主操作按钮 =====
export const ACTIONS = {
  runFullPipeline: '运行完整分析流程',
  generateReport: '生成分析报告',
  viewResult: '查看结果',
  viewLogs: '查看日志',
  close: '关闭',
  rerun: '重新运行',
  run: '运行',
  saveAndContinue: '保存并继续分析 →',
  uploadFile: '上传文件',
  selectPublicData: '选择公共数据',
  download: '下载',
  fetch: '获取',
};

// ===== 模块标题 =====
export const MODULES = {
  imageProcessing: '影像处理模块',
  imageSubtitle: 'AI 驱动的 MRI 身体成分分析',
  workflowSelection: '分析流程选择',
  workflowSubtitle: '为您的研究选择合适的分析流程',
  analysisModules: '分析模块 · 上下文视图',
  pipelineOverview: '流程总览',
  pipelineSubtitle: '完整分析流程状态与进度',
  uploadMRI: '上传 MRI 影像',
  bodyFatPhenotypes: '已分析脂肪表型',
  summary: '分析摘要',
};

// ===== 脂肪表型指标 =====
export const PHENOTYPES = {
  liverFatFraction: '肝脏脂肪分数',
  pancreaticFatFraction: '胰腺脂肪分数',
  perirenalFat: '肾周脂肪',
  boneMarrowFatFraction: '骨髓脂肪分数',
  totalBodyFat: '全身脂肪',
  visceralFat: '内脏脂肪',
  subcutFat: '皮下脂肪',
  muscleVolume: '肌肉体积',
  liverPDFF: '肝脏 PDFF',
  pancreaticPDFF: '胰腺 PDFF',
  boneDensity: '骨密度',
  satVatRatio: 'SAT/VAT 比值',
};

// ===== Summary 指标 =====
export const SUMMARY_METRICS: Record<string, string> = {
  'Total Body Fat': '全身脂肪',
  'Visceral Fat': '内脏脂肪',
  'Subcut. Fat': '皮下脂肪',
  'Muscle Volume': '肌肉体积',
  'Liver PDFF': '肝脏 PDFF',
  'Pancreatic PDFF': '胰腺 PDFF',
  'Bone Density': '骨密度',
  'SAT/VAT Ratio': 'SAT/VAT 比值',
};

// ===== 工作流卡片 =====
export const WORKFLOWS = {
  gwas: {
    title: '全基因组关联分析（GWAS）',
    subtitle: 'GWAS',
    description: '通过大规模基因组扫描识别与体脂表型相关的遗传变异。',
    letter: 'A',
  },
  mr: {
    title: '孟德尔随机化分析（MR）',
    subtitle: 'MR',
    description: '利用遗传工具变量估计脂肪性状对疾病结局的因果效应。',
    letter: 'B',
  },
  mediation: {
    title: '中介机制筛选',
    subtitle: '中介 MR',
    description: '通过多步 MR 发现连接脂肪性状与疾病结局的血浆蛋白中介因子。',
    letter: 'C',
  },
};

// ===== GWAS 模块 =====
export const GWAS = {
  uploadGenomicData: '上传基因组数据',
  uploadGenomicHint: '支持 PLINK / VCF / BED 格式',
  gwasAnalysisProgress: 'GWAS 分析进度',
  manhattanPreview: '曼哈顿图 — 预览',
  totalSNPs: 'SNP 总数',
  significantLoci: '显著位点',
  leadSNPs: '先导 SNP',
  gwasAnalysis: 'GWAS 分析',
  opengwasFetch: 'OpenGWAS 数据获取',
  notAvailable: '—',
};

// ===== MR 模块 =====
export const MR = {
  uploadOutcomeData: '上传结局数据',
  uploadOutcomeHint: '结局性状的 GWAS 汇总统计数据',
  mrAnalysisProgress: 'MR 分析进度',
  scatterPreview: '散点图 — SNP 效应',
  mrAnalysis: 'MR 分析',
  downloadExample: '下载示例结局数据',
  method: '方法',
  beta: 'β',
  ci95: '95% CI',
  pValue: 'P 值',
  snpExposureEffect: 'SNP-暴露效应',
  snpOutcomeEffect: 'SNP-结局效应',
};

// ===== 中介机制模块 =====
export const MEDIATION = {
  moduleTitle: '中介机制筛选',
  moduleSubtitle: '发现连接脂肪性状与疾病结局的血浆蛋白中介因子',
  innerTitle: '中介 MR 分析',
  selected: '已选中',
  selectPublicData: '选择公共数据',
  decodeDesc: '4,907 种冰岛血浆蛋白 pQTL 数据，来源于 deCODE 遗传学研究',
  metaboliteDesc: '代谢物 GWAS 汇总统计数据',
  dataSource1: '冰岛血浆蛋白 pQTL 数据（4,907）',
  dataSource2: '代谢物 GWAS 数据',
  dataSource3: 'GWAS Catalog / OpenGWAS',
  potentialMediators: '潜在中介因子',
  potentialMediatorsDesc: '识别候选血浆蛋白中介因子',
  mediationMRAnalysis: '中介 MR 分析',
  mediationMRDesc: '两步孟德尔随机化分析',
  complete: '已完成',
  running: '运行中...',
  mechanismFlow: '潜在中介因子 — 机制流程图',
  adiposeTissue: '脂肪组织',
  liverPDFF: '肝脏 PDFF',
  exposure: '暴露因素',
  plasmaProteins: '血浆蛋白',
  mediator: '中介因子',
  osteoporosis: '骨质疏松',
  outcome: '结局变量',
  boneMineralDensity: '骨密度 ↓',
  step1: '步骤一：暴露 → 中介',
  step2: '步骤二：中介 → 结局',
  indirectEffect: '间接效应',
  directEffect: '直接效应',
  totalEffect: '总效应',
  mediated: '% 中介',
  direct: '% 直接',
  resultsTitle: '中介 MR 分析结果',
  // 结果表头
  colMediator: '中介因子',
  colBetaA: '路径 A 效应值',
  colBetaB: '路径 B 效应值',
  colIndirect: '间接效应',
  colP: 'P 值',
  colPropMediated: '中介比例',
  colSignificant: '显著',
  legendIndirect: '间接效应',
  legendSignificant: 'p < 0.05',
  legendBetaA: '路径 A：暴露 → 中介',
  legendBetaB: '路径 B：中介 → 结局',
  runMediation: '运行中介 MR',
  viewFullResults: '查看完整中介分析结果',
};

// ===== 流程步骤标签 =====
export const PIPELINE_LABELS: Record<string, string> = {
  image_segmentation: 'AI 影像分割',
  gwas_analysis: 'GWAS 分析',
  opengwas_fetch: 'OpenGWAS 数据获取',
  mendelian_randomization: '孟德尔随机化分析',
  mediation_mr: '中介 MR 分析',
  risk_modeling: '风险建模',
  report_generation: '报告生成',
};

// ===== Pipeline Overview =====
export const PIPELINE = {
  complete: '已完成',
  running: '运行中',
  failed: '失败',
  pending: '待开始',
  of: '/',
  pipelineComplete: '流程完成',
  inProgress: '进行中',
  runningStatus: '{running} 个运行中',
  failedStatus: '{failed} 个失败',
  stepComplete: '已完成',
};

// ===== 上传区域 =====
export const UPLOAD = {
  uploadFile: '上传文件',
  dragDrop: '拖拽或点击上传',
  uploading: '上传中...',
  niftiDICOM: 'NIfTI、DICOM — 拖拽或点击上传',
  formatDICOM: 'DICOM',
  formatNIfTI: 'NIfTI',
  formatJPGPNG: 'JPG/PNG',
  formatTSV: '.tsv',
  formatCSV: '.csv',
  formatOpenGWAS: 'OpenGWAS ID',
  formatPLINK: 'PLINK / VCF / BED',
  gwascatSummary: '结局性状的 GWAS 汇总统计数据',
  segmentationRunning: 'AI 影像分割进行中...',
  segmentationStatus: 'AI 影像分割状态',
  viewSegmentationResult: '查看影像分割结果',
};

// ===== 通用 =====
export const COMMON = {
  loading: '加载中...',
  reportGenerating: '报告生成中或暂不可用...',
  runFirstHint: '请先运行任务以启报告生成',
  resultDetail: '结果详情',
  activeLabel: '进行中',
  completedLabel: '已完成',
};

// ===== 统计指标 label 映射 =====
export const STAT_LABELS: Record<string, string> = {
  'Total SNPs': 'SNP 总数',
  'Significant Loci': '显著位点',
  'Lead SNPs': '先导 SNP',
};

// ===== 趋势文本 =====
export const TRENDS: Record<string, string> = {
  'from baseline': '相对基线',
  'variation': '波动范围',
};
