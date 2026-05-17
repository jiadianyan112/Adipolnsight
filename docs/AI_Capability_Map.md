# AdipoInsight AI 能力清单与接入优先级

> 版本：v0.2.0-draft
> 日期：2026-05-17
> 原则：一能力一行、逐条可验收、Mock-First 可替换

---

## 能力总览矩阵

| # | 能力名称 | 当前模式 | 优先级 | 依赖 |
|---|---------|---------|--------|------|
| C1 | MRI 影像上传与 AI 分割 | mock | P0 | 无 |
| C2 | 多部位脂肪表型量化 | mock | P0 | C1 |
| C3 | GWAS 全基因组关联分析 | mock | P1 | C2 |
| C4 | 双样本孟德尔随机化分析 | mock | P1 | C3 |
| C5 | 中介孟德尔随机化分析 | mock | P1 | C3, C4 |
| C6 | 肝脏脂肪-骨质疏松风险建模 | mock | P1 | C2, C4, C5 |
| C7 | 科研报告自动生成 | mock | P0 | C1~C6 任一项完成 |
| C8 | AI 智能体问答与任务调度 | 未实现 | P2 | 后端基础设施就绪 |

---

## 详细能力清单

---

### C1 · MRI 影像上传与 AI 分割

| 维度 | 内容 |
|------|------|
| **能力名称** | MRI 影像上传与 AI 分割 |
| **能力描述** | 用户上传腹部 MRI 影像（NIfTI/DICOM），AI 模型自动分割肝脏、内脏脂肪、皮下脂肪、骨髓等解剖结构，输出分割 mask 与 DICE 质量评分 |
| **用户触发入口** | ProjectWorkspacePage → ImageProcessingModule → 上传区拖拽/点击上传 |
| **输入数据** | MRI 影像文件（`.nii.gz` / `.dcm`），单文件 ≤ 200MB |
| **后端接口** | `POST /api/v1/projects/{id}/files`（上传）→ `POST /api/v1/tasks`（task_type=`image_segmentation`） |
| **AI Skill Adapter** | `adapters/image_segmentation/` — MockAdapter 调用 `mock_segmentation.py`；RealAdapter 预留 TSSA-UNet 推理脚本 |
| **输出结果** | `segmentation_metrics.json`（DICE 评分 × 4 个解剖区）、`fat_quantification.csv`（每样本脂肪体积）、`overlay_preview.png`（分割叠加预览图） |
| **前端展示组件** | `ImageProcessingModule`：上传进度条、DICE 评分 badge、脂肪体积摘要卡片、分割预览缩略图 |
| **当前实现模式** | **mock** — `analysis_scripts/segmentation/mock_segmentation.py` 生成随机 DICE 0.87~0.96、随机脂肪体积 |
| **真实方案** | TSSA-UNet / nnUNet 推理脚本，输入 NIfTI → 输出多类分割 mask → 派生脂肪体积 |
| **接入优先级** | **P0** — 整个分析流程的入口，必须最先打通 |
| **验收标准** | ① 上传 MRI 文件后 30s 内返回 task_id；② 任务完成后 `segmentation_metrics.json` 包含 4 个 DICE 值；③ `overlay_preview.png` 可在前端展示；④ DICE 值 < 0.85 时前端展示 QC 警告；⑤ Mock 和 Real 模式可通过环境变量切换 |

---

### C2 · 多部位脂肪表型量化

| 维度 | 内容 |
|------|------|
| **能力名称** | 多部位脂肪表型量化 |
| **能力描述** | 基于分割结果，计算肝脏 PDFF、内脏脂肪体积、皮下脂肪体积、骨髓脂肪分数、肌肉体积、SAT/VAT 比值等定量表型指标 |
| **用户触发入口** | ProjectWorkspacePage → "保存并继续分析" 按钮 → 自动触发（C1 成功后） |
| **输入数据** | C1 输出的 `segmentation_metrics.json` + `fat_quantification.csv` |
| **后端接口** | `POST /api/v1/tasks`（task_type=`phenotype_quantification`） |
| **AI Skill Adapter** | `adapters/phenotype_quantification/` — MockAdapter 从 C1 输出派生计算；RealAdapter 调用标准化后处理 pipeline |
| **输出结果** | `phenotype_summary.json`（8 项指标：liver_pdff, visceral_fat_volume, subcutaneous_fat_volume, bone_marrow_fat_fraction, total_body_fat_pct, muscle_volume, sat_vat_ratio, bone_density）、`phenotype_detail.csv`（逐样本） |
| **前端展示组件** | `ImageProcessingModule`：4 个 MiniChartCard（趋势迷你图）、`MetricSummaryCard`（8 格摘要网格） |
| **当前实现模式** | **mock（隐式）** — 当前前端组件中硬编码了 PHENOTYPE_DATA 和 SUMMARY_METRICS 常量，未走后端 |
| **真实方案** | 调用 C1 分割 mask → 体素计数 → 物理单位换算（基于 DICOM header 的 voxel spacing） |
| **接入优先级** | **P0** — 所有下游分析（GWAS/MR/Risk）的暴露变量来源，必须紧随 C1 打通 |
| **验收标准** | ① C1 成功后自动触发 C2 任务；② `phenotype_summary.json` 包含全部 8 项指标；③ 前端 MiniChartCard 的 value/trend/sparkline 从 store 读取而非硬编码；④ 指标值与输入影像的体素分辨率一致（偏差 ≤ 5%） |

---

### C3 · GWAS 全基因组关联分析

| 维度 | 内容 |
|------|------|
| **能力名称** | GWAS 全基因组关联分析 |
| **能力描述** | 以 C2 输出的定量表型（如 Liver_PDFF）为因变量，对上传的基因型数据进行全基因组关联扫描，产出曼哈顿图、显著位点列表、先导 SNP |
| **用户触发入口** | ProjectWorkspacePage → GWASModule → "运行" 按钮（gwas_analysis） |
| **输入数据** | 基因型数据（PLINK bed/bim/fam 或 VCF）+ 表型数据（来自 C2）+ 协变量（age, sex, BMI, PC1-10） |
| **后端接口** | `POST /api/v1/tasks`（task_type=`gwas_analysis`, parameters=`{phenotype: "Liver_PDFF"}`） |
| **AI Skill Adapter** | `adapters/gwas_analysis/` — MockAdapter 调用 `mock_gwas.py`；RealAdapter 调用 REGENIE / PLINK2 / SAIGE |
| **输出结果** | `gwas_summary_stats.tsv`（全基因组 SNP 关联统计）、`lead_snps.csv`（先导 SNP）、`significant_loci.csv`（显著基因座）、`gwas_summary.json`（λ_GC、样本量、显著位点数） |
| **前端展示组件** | `GWASModule`：曼哈顿图（Recharts ScatterChart）、SNP 统计卡片（总数/显著/先导） |
| **当前实现模式** | **mock** — `mock_gwas.py` 生成随机 12 个 SNP；前端曼哈顿图数据由 `generateManhattanData()` 在前端随机生成 |
| **真实方案** | REGENIE step1 + step2，输入 PLINK binary + 表型 + 协变量，输出全基因组关联统计 |
| **接入优先级** | **P1** — MR 分析的前置依赖，但对端到端闭环非阻塞 |
| **验收标准** | ① 曼哈顿图数据从 `gwas_summary_stats.tsv` 解析，不从前端随机生成；② λ_GC 合理范围 0.95~1.10；③ 显著位点数与样本量/表型遗传力匹配；④ 支持 22 条常染色体 + X 染色体 |

---

### C4 · 双样本孟德尔随机化分析

| 维度 | 内容 |
|------|------|
| **能力名称** | 双样本孟德尔随机化分析（Two-Sample MR） |
| **能力描述** | 以 C3 选出的显著 SNP 为工具变量（暴露），从 OpenGWAS 获取结局性状的 GWAS 汇总统计，执行 IVW / MR-Egger / Weighted Median / Weighted Mode 四种 MR 方法，估计因果效应 |
| **用户触发入口** | ProjectWorkspacePage → MRModule → "运行" 按钮（mendelian_randomization） |
| **输入数据** | 暴露 GWAS（C3 输出 `gwas_summary_stats.tsv`）+ 结局 GWAS（OpenGWAS 获取或用户上传）+ 参数（clump_r2, clump_kb, p_threshold） |
| **后端接口** | `POST /api/v1/tasks`（task_type=`mendelian_randomization`, parameters=`{exposure, outcome}`） |
| **AI Skill Adapter** | `adapters/two_sample_mr/` — MockAdapter 调用 `mock_mr.py`；RealAdapter 调用 TwoSampleMR R package 或 Python 等价实现 |
| **输出结果** | `mr_results.csv`（4 种方法的 β, SE, OR, CI, P）、`heterogeneity.csv`（Cochran's Q）、`pleiotropy.csv`（MR-Egger intercept）、`mr_summary.json` |
| **前端展示组件** | `MRModule`：SNP-暴露 vs SNP-结局散点图（ComposedChart + IVW 拟合线）、MR 估计值表（方法/β/CI/P） |
| **当前实现模式** | **mock** — `mock_mr.py` 生成随机 β 0.1~0.3；前端 MR_ESTIMATES 硬编码 4 行数据，散点图由 `generateMRData()` 前端生成 |
| **真实方案** | R `TwoSampleMR` 包（harmonise + mr），或 Python `MendelianRandomization` 包 |
| **接入优先级** | **P1** — 核心科学价值模块，但对初始闭环可延后 |
| **验收标准** | ① 散点图数据从 `mr_results.csv` 解析，IVW 斜率与 `mr_summary.json` 中的 β 一致；② 4 种方法全部返回；③ MR-Egger intercept P > 0.05 时无水平多效性警告；④ 工具变量 F-statistic > 10 |

---

### C5 · 中介孟德尔随机化分析

| 维度 | 内容 |
|------|------|
| **能力名称** | 中介孟德尔随机化分析（Mediation MR） |
| **能力描述** | 以血浆蛋白 pQTL 为中介因子，执行两步 MR（暴露 → 中介蛋白 → 结局），识别介导脂肪性状与疾病结局之间因果路径的血浆蛋白 |
| **用户触发入口** | ProjectWorkspacePage → MediationMRModule → "运行中介 MR" 按钮 |
| **输入数据** | 暴露 GWAS（C3）+ 结局 GWAS（C4）+ 中介 pQTL 数据（deCODE 4,907 种血浆蛋白或用户上传） |
| **后端接口** | `POST /api/v1/tasks`（task_type=`mediation_mr`, parameters=`{exposure, outcome, mediator_source}`） |
| **AI Skill Adapter** | `adapters/mediation_mr/` — MockAdapter 调用 `mock_mediation_mr.py`；RealAdapter 调用两步 MR pipeline |
| **输出结果** | `mediation_results.csv`（βᴬ, βᴮ, indirect_effect, proportion_mediated, p_mediation）、`candidate_proteins.csv`、`mediation_summary.json`（显著中介因子列表） |
| **前端展示组件** | `MediationMRModule`：机制流程图（暴露→中介→结局 + 效应值）、中介 MR 结果表（6 列） |
| **当前实现模式** | **mock** — `mock_mediation_mr.py` 随机生成 6 个蛋白；前端 RESULTS_DATA 硬编码 6 行（FGF21/GDF15/IGFBP1/LEP/ADIPOQ/SHBG） |
| **真实方案** | 步骤一：暴露 SNP → 蛋白水平（cis-pQTL + trans-pQTL）；步骤二：蛋白 SNP → 结局；乘积法 + delta method SE |
| **接入优先级** | **P1** — 差异化能力，但对闭环非阻塞 |
| **验收标准** | ① 机制流程图的 βᴬ / βᴮ / 间接效应值从后端数据解析；② 结果表按 p_mediation 排序，p < 0.05 的行标绿；③ 至少识别 1 个 FDR < 0.05 的中介蛋白；④ 显著蛋白可点击查看详细路径信息 |

---

### C6 · 肝脏脂肪-骨质疏松风险建模

| 维度 | 内容 |
|------|------|
| **能力名称** | 肝脏脂肪-骨质疏松风险建模 |
| **能力描述** | 综合影像表型、遗传风险评分、中介蛋白效应，构建多因素临床风险预测模型（OLS + RCS + 多分类 Logistic），预测骨质疏松风险等级 |
| **用户触发入口** | TaskCard → "运行" 按钮（risk_modeling），或在 pipeline 中自动触发 |
| **输入数据** | C2 表型 + C4 MR 估计值 + C5 中介蛋白 + 临床协变量（age, sex, BMI） |
| **后端接口** | `POST /api/v1/tasks`（task_type=`risk_modeling`, parameters=`{exposure, outcome}`） |
| **AI Skill Adapter** | `adapters/risk_modeling/` — MockAdapter 调用 `mock_risk_modeling.py`；RealAdapter 调用 statsmodels / scikit-learn pipeline |
| **输出结果** | `ols_results.csv`、`rcs_results.csv`、`risk_summary.json`（四分位 AOR、风险等级 High/Medium/Low、模型类型） |
| **前端展示组件** | 当前无专用组件，结果通过 `UnifiedResultView` 展示（summary cards + file list） |
| **当前实现模式** | **mock** — `mock_risk_modeling.py` 生成固定 β=0.35, p=0.0001 |
| **真实方案** | Python `statsmodels` OLS + RCS（限制性立方样条）+ `sklearn` 多分类 Logistic Regression |
| **接入优先级** | **P1** — 临床转化价值高，但对技术闭环非必需 |
| **验收标准** | ① 输出 PDFF 四分位分层风险估计；② OLS β 与 MR β 方向一致；③ RCS 曲线展示非线性关系；④ 模型 AUC ≥ 0.70 |

---

### C7 · 科研报告自动生成

| 维度 | 内容 |
|------|------|
| **能力名称** | 科研报告自动生成 |
| **能力描述** | 聚合项目中所有已完成分析的结果，生成结构化的 Markdown 科研报告，包含摘要、方法、结果、讨论、限制说明 |
| **用户触发入口** | ProjectWorkspacePage → "生成分析报告" 按钮；pipeline 最后一步自动触发 |
| **输入数据** | 项目元信息（name, goal, exposure, outcome, mediator）+ 全部 AnalysisResult（C1~C6 的 summary_json） |
| **后端接口** | `POST /api/v1/projects/{id}/reports/generate` → `GET /api/v1/reports/{id}` |
| **AI Skill Adapter** | `adapters/report_generation/` — MockAdapter 调用 `mock_report.py` + `ReportService`；RealAdapter 预留 LLM 驱动的智能报告生成 |
| **输出结果** | `final_report.md`（含 8 个章节：摘要、影像分割、GWAS、OpenGWAS、MR、中介 MR、风险建模、结论与限制） |
| **前端展示组件** | `ReportPage` → `ReportViewer`（react-markdown 渲染） |
| **当前实现模式** | **mock** — `ReportService.generate()` 遍历 AnalysisResult 拼接 Markdown；`mock_report.py` 生成简单模板 |
| **真实方案** | LLM（如 Claude API / GPT-4）接收结构化 JSON 结果 → 生成自然语言讨论与结论段落；模板引擎渲染固定章节框架 |
| **接入优先级** | **P0** — 端到端闭环的出口，用户价值感知最强 |
| **验收标准** | ① 报告在 10s 内生成完成；② 包含全部已完成分析的结果章节；③ 未完成的分析章节标注 "待分析"；④ Markdown 格式通过 react-markdown 正常渲染；⑤ 报告可导出为 PDF（后续） |

---

### C8 · AI 智能体问答与任务调度

| 维度 | 内容 |
|------|------|
| **能力名称** | AI 智能体问答与任务调度 |
| **能力描述** | 提供自然语言交互界面，用户可通过对话方式：① 询问当前项目状态与结果解读；② 调度分析任务（"帮我跑 GWAS 分析"）；③ 获取科学建议（"这个 MR 结果怎么解读"）；④ 自动排错与重跑 |
| **用户触发入口** | 新增：工作区右下角 AI 对话面板（ChatPanel 组件，尚未实现） |
| **输入数据** | 用户自然语言消息 + 当前项目上下文（project_id, tasks, results） |
| **后端接口** | `POST /api/v1/chat`（新增，暂未实现）— payload: `{ project_id, message, conversation_history }` |
| **AI Skill Adapter** | `adapters/agent/` — 调用 LLM API（Claude / GPT-4），Function Calling 模式：意图识别 → 工具调用 → 结果整合 → 自然语言回复 |
| **输出结果** | Markdown 格式的 AI 回复（可包含表格、图表引用）、触发的任务 ID 列表 |
| **前端展示组件** | 新增 `ChatPanel` 组件（对话气泡 + Markdown 渲染 + 快捷操作按钮） |
| **当前实现模式** | **未实现** — 前后端均无对话相关代码 |
| **真实方案** | LLM API + Function Calling：① system prompt 注入 AdipoInsight 项目上下文和可用工具列表；② 工具函数映射到现有 POST /tasks 接口；③ 流式返回（SSE） |
| **接入优先级** | **P2** — 增强型体验功能，需 C1~C7 全部稳定后接入 |
| **验收标准** | ① 用户发 "运行 GWAS" → AI 自动调用 POST /tasks 创建 gwas_analysis 任务；② "当前项目进展如何" → 返回任务完成状态摘要 + 下一步建议；③ "解读这个 MR 结果" → 基于真实 summary_json 生成自然语言解读；④ 对话历史在页面刷新后保留；⑤ 支持流式输出（逐字显示） |

---

## 优先级执行路线

```
Phase 0 (当前)         Phase 1 (P0)              Phase 2 (P1)              Phase 3 (P2)
─────────────         ─────────────             ─────────────             ─────────────
                      C1                        C3                        C8
Mock 脚本可运行   →   MRI 上传+分割打通    →    GWAS 真实数据对接     →    AI Agent 问答
                       C2                        C4                       
前端硬编码数据        表型量化从后端取数        双样本 MR 打通
                       C7                        C5
                      报告生成真实闭环           中介 MR 打通
                                                 C6
                                                 风险建模对接
```

---

## 模式切换策略

| 能力 | Mock → Real 替换难度 | 关键风险 | 建议切换时机 |
|------|---------------------|---------|-------------|
| C1 影像分割 | 中 — 需 GPU 环境 + 模型权重 | 模型推理时间不可控（当前 mock 0.5s） | Phase 1 末期 |
| C2 表型量化 | 低 — 纯数值计算 | 依赖 C1 mask 质量 | 紧跟 C1 Real |
| C3 GWAS | 高 — 需 REGENIE + 大型基因型数据 | 计算资源（数小时级） | Phase 2 |
| C4 双样本 MR | 中 — 需 R 环境或 Python 移植 | R/Python 互操作 | Phase 2 |
| C5 中介 MR | 中 — 依赖于 pQTL 数据库 | 数据库授权 | Phase 2 后期 |
| C6 风险建模 | 低 — statsmodels/sklearn | 临床可解释性 | Phase 2 后期 |
| C7 报告生成 | 低 — LLM API 调用 | LLM 幻觉风险 | Phase 1 末期 |
| C8 AI Agent | 中 — Function Calling 架构 | 工具调用准确性 | Phase 3 |

---

## 附录：能力间数据依赖图

```
上传 MRI 影像
    │
    ▼
[C1] AI 影像分割 ──────────────────────────────────────┐
    │ mask + DICE                                        │
    ▼                                                    │
[C2] 脂肪表型量化 ─────────────────────────────────┐    │
    │ phenotype_summary (Liver_PDFF, VAT, SAT...)   │    │
    ├──────────────────────────┐                    │    │
    ▼                          ▼                    │    │
[C3] GWAS 分析          上传基因组数据              │    │
    │ lead_snps + stats          │                   │    │
    ├──────────────────┐         │                   │    │
    ▼                  ▼         ▼                   │    │
[C4] 双样本 MR     OpenGWAS 获取                     │    │
    │ causal β                                       │    │
    ├─────────────────────┐                          │    │
    ▼                     ▼                          │    │
[C5] 中介 MR         [C6] 风险建模                   │    │
    │ mediator proteins   │ risk_level                │    │
    └─────────┬───────────┘                          │    │
              ▼                                      │    │
         [C7] 科研报告生成 ◄─────────────────────────┘    │
              │                                           │
              ▼                                           │
         [C8] AI 智能体问答（全能力可调用）               │
```

> 实线箭头 = 数据依赖（上游输出是下游输入）；虚线箭头 = 可选依赖

---

## 文档版本记录

| 版本 | 日期 | 变更 |
|------|------|------|
| v0.2.0-draft | 2026-05-17 | 初始版本，覆盖 8 项 AI 能力 |
