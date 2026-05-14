---
document_name: AdipoInsight Mock-First 总体框架任务拆解
document_type: AI-readable task framework
project: AdipoInsight
version: v1.0
purpose: 供 Claude Code / Codex / AI 编程助手理解、记忆、拆解与执行，用模拟脚本先搭建医学科研 AI 平台总体框架。
principle: 真实系统骨架 + 模拟计算核心
language: zh-CN
---

# AdipoInsight Mock-First 总体框架任务拆解

## 0. 项目定位

AdipoInsight 第一阶段目标不是直接接入真实 UK Biobank、真实 TSSA-UNet、真实 OpenGWAS、真实 GWAS 计算环境和真实 R 分析流程，而是先搭建一个端到端可运行的医学科研 AI 平台框架。

第一阶段采用 **Mock-First** 策略：

```text
页面是真的
API 是真的
数据库结构是真的
任务调度是真的
文件存储路径是真的
结果 schema 是真的
日志和错误处理是真的
分析脚本暂时使用 mock 模拟
```

系统需要完整模拟以下科研链路：

```text
创建项目
→ 上传或选择模拟 MRI / 表型 / 协变量 / SNP 数据
→ AI 影像分割
→ 脂肪表型提取
→ GWAS 模拟分析
→ OpenGWAS / IEU 数据获取模拟
→ Two-sample MR 模拟分析
→ Mediation MR 模拟分析
→ Risk Modeling 模拟分析
→ 科研报告生成
```

---

## 1. 总体任务树

```text
T0. 项目边界与工程规范建立
T1. 项目基础工程搭建
T2. 核心数据模型与接口协议设计
T3. 后端 API 服务搭建
T4. 文件存储与结果目录系统搭建
T5. 分析任务调度中心搭建
T6. Mock 分析 Skill 脚本体系搭建
T7. 前端 Web 工作台搭建
T8. 分析结果展示模块搭建
T9. 科研报告生成模块搭建
T10. 日志、异常、审计与可追溯机制搭建
T11. 测试数据、演示流程与验收用例搭建
T12. 本地部署、开发文档与 real 模块替换说明
```

---

# T0. 项目边界与工程规范建立

## T0.1 明确 MVP 范围

### T0.1.1 明确当前版本为 Mock-First 框架

当前版本不接入真实 UK Biobank、真实 OpenGWAS、真实 TSSA-UNet、真实 REGENIE。所有计算模块通过 mock 脚本模拟。

### T0.1.2 明确第一版核心闭环

```text
创建项目
→ 上传/选择模拟数据
→ 发起 AI 影像分割任务
→ 生成脂肪表型结果
→ 发起 GWAS 模拟分析
→ 发起 OpenGWAS 模拟获取
→ 发起 MR 模拟分析
→ 发起 Mediation MR 模拟分析
→ 发起风险建模任务
→ 汇总结果
→ 生成科研报告
```

### T0.1.3 明确第一版暂不实现内容

```text
不训练真实 TSSA-UNet
不真实下载 UKB 数据
不真实运行 REGENIE
不真实请求 OpenGWAS
不做用户支付系统
不做复杂权限体系
不做多人协作编辑
不做医院级合规系统
```

---

## T0.2 明确技术栈

### T0.2.1 前端技术栈

```text
Next.js
React
TypeScript
Tailwind CSS
Zustand 或 Redux
Axios / Fetch
ECharts 或 Recharts
```

### T0.2.2 后端技术栈

```text
Python FastAPI
SQLAlchemy
Pydantic
Uvicorn
python-multipart
pandas
BackgroundTasks / RQ / Celery 三选一，MVP 优先 BackgroundTasks
```

### T0.2.3 数据库与存储

```text
PostgreSQL 作为主数据库
本地 storage/ 目录模拟对象存储
后续可替换为 MinIO / OSS / S3
```

### T0.2.4 分析脚本

```text
Python mock scripts
R mock scripts
统一命令行参数
统一输出目录
统一 JSON / CSV 输出格式
```

---

## T0.3 工程目录规范

### T0.3.1 单仓库结构

```text
adipoinsight/
  frontend/
  backend/
  analysis_scripts/
  storage/
  mock_data/
  docs/
  docker/
  README.md
```

### T0.3.2 后端目录

```text
backend/
  app/
    main.py
    api/
    core/
    db/
    models/
    schemas/
    services/
    tasks/
    utils/
  scripts/
  requirements.txt
```

### T0.3.3 前端目录

```text
frontend/
  app/
  components/
  features/
  services/
  stores/
  types/
  utils/
```

### T0.3.4 分析脚本目录

```text
analysis_scripts/
  segmentation/
  gwas/
  opengwas/
  mr/
  mediation_mr/
  risk_modeling/
  report/
```

---

# T1. 项目基础工程搭建

## T1.1 初始化代码仓库

### T1.1.1 创建根目录

```text
创建 adipoinsight 项目根目录
初始化 Git
创建 README.md
创建 .gitignore
```

### T1.1.2 创建基础目录

```text
frontend/
backend/
analysis_scripts/
mock_data/
storage/
docs/
docker/
```

### T1.1.3 建立环境变量文件

```text
.env.example
.env.local.example
backend/.env.example
frontend/.env.example
```

### T1.1.4 建立启动说明

```text
docs/00_local_setup.md
docs/01_project_overview.md
```

---

## T1.2 搭建后端 FastAPI 工程

### T1.2.1 初始化 FastAPI

```text
创建 backend/app/main.py
提供 GET /health
提供 GET /api/v1/version
```

### T1.2.2 配置后端依赖

创建 `backend/requirements.txt`，至少包含：

```text
fastapi
uvicorn
sqlalchemy
pydantic
python-multipart
pandas
alembic
psycopg2-binary
```

### T1.2.3 配置后端启动脚本

```text
backend/run_dev.sh
backend/run_dev.ps1
```

### T1.2.4 配置 CORS

允许前端本地开发端口访问后端。

---

## T1.3 搭建前端 Next.js 工程

### T1.3.1 初始化 Next.js

```text
创建 frontend 项目
启用 TypeScript
启用 Tailwind CSS
```

### T1.3.2 创建基础布局

```text
全局 Layout
左侧导航栏
顶部项目状态栏
```

### T1.3.3 创建基础页面

```text
/
/projects/new
/projects/[projectId]
/projects/[projectId]/workspace
```

### T1.3.4 配置 API Client

创建：

```text
frontend/services/apiClient.ts
```

功能：

```text
统一请求 baseURL
统一错误处理
统一 loading 状态封装
```

---

# T2. 核心数据模型与接口协议设计

## T2.1 核心业务对象

### T2.1.1 Project 项目模型

```text
project_id
project_name
research_goal
exposure
outcome
mediator_set
status
created_at
updated_at
```

### T2.1.2 Sample 样本模型

```text
sample_id
project_id
subject_id
mri_file_path
phenotype_file_path
covariate_file_path
genotype_file_path
qc_status
created_at
```

### T2.1.3 FileAsset 文件资产模型

```text
file_id
project_id
sample_id
file_name
file_type
file_path
file_size
mime_type
created_at
```

### T2.1.4 AnalysisTask 分析任务模型

```text
task_id
project_id
sample_id
task_type
task_name
status
progress
input_json
output_json
error_code
error_message
started_at
finished_at
created_at
updated_at
```

### T2.1.5 AnalysisResult 分析结果模型

```text
result_id
task_id
project_id
result_type
summary_json
output_files_json
created_at
```

### T2.1.6 Report 报告模型

```text
report_id
project_id
title
content_markdown
markdown_path
pdf_path
status
created_at
updated_at
```

### T2.1.7 AuditLog 审计日志模型

```text
log_id
project_id
task_id
action
operator
detail_json
created_at
```

---

## T2.2 任务类型枚举

### T2.2.1 task_type

```text
image_segmentation
gwas_analysis
opengwas_fetch
mendelian_randomization
mediation_mr
risk_modeling
report_generation
```

### T2.2.2 task_status

```text
pending
running
success
failed
cancelled
```

### T2.2.3 result_type

```text
segmentation_result
gwas_result
opengwas_result
mr_result
mediation_result
risk_result
report_result
```

---

## T2.3 统一任务输入输出协议

### T2.3.1 统一任务输入 JSON

```json
{
  "project_id": "project_001",
  "task_type": "mendelian_randomization",
  "input_files": [],
  "parameters": {
    "exposure": "Liver_PDFF",
    "outcome": "Osteoporosis",
    "method": "IVW"
  }
}
```

### T2.3.2 统一任务输出 JSON

```json
{
  "task_id": "task_001",
  "status": "success",
  "summary": {},
  "output_files": [],
  "logs": [],
  "finished_at": ""
}
```

### T2.3.3 统一错误输出 JSON

```json
{
  "task_id": "task_001",
  "status": "failed",
  "error_code": "MOCK_SCRIPT_FAILED",
  "error_message": "mock script execution failed",
  "trace_id": "trace_001"
}
```

---

# T3. 后端 API 服务搭建

## T3.1 项目管理 API

```text
POST   /api/v1/projects
GET    /api/v1/projects
GET    /api/v1/projects/{project_id}
PUT    /api/v1/projects/{project_id}
DELETE /api/v1/projects/{project_id}
```

## T3.2 样本与文件 API

```text
POST /api/v1/projects/{project_id}/files/mri
POST /api/v1/projects/{project_id}/files/phenotype
POST /api/v1/projects/{project_id}/files/covariates
POST /api/v1/projects/{project_id}/files/genotype
GET  /api/v1/projects/{project_id}/files
GET  /api/v1/files/{file_id}
```

## T3.3 分析任务 API

```text
POST /api/v1/tasks
GET  /api/v1/tasks/{task_id}
GET  /api/v1/projects/{project_id}/tasks
POST /api/v1/tasks/{task_id}/cancel
POST /api/v1/tasks/{task_id}/rerun
```

## T3.4 结果 API

```text
GET /api/v1/tasks/{task_id}/results
GET /api/v1/projects/{project_id}/results
GET /api/v1/projects/{project_id}/results/segmentation
GET /api/v1/projects/{project_id}/results/gwas
GET /api/v1/projects/{project_id}/results/mr
GET /api/v1/projects/{project_id}/results/mediation
GET /api/v1/projects/{project_id}/results/risk
```

## T3.5 报告 API

```text
POST /api/v1/projects/{project_id}/reports/generate
GET  /api/v1/projects/{project_id}/reports
GET  /api/v1/reports/{report_id}
```

---

# T4. 文件存储与结果目录系统搭建

## T4.1 storage 目录设计

### T4.1.1 项目级目录

```text
storage/projects/{project_id}/
```

### T4.1.2 样本级目录

```text
storage/projects/{project_id}/samples/{sample_id}/
```

### T4.1.3 原始文件目录

```text
raw/
  mri/
  phenotype/
  covariates/
  genotype/
```

### T4.1.4 分析输出目录

```text
outputs/
  segmentation/
  gwas/
  opengwas/
  mr/
  mediation_mr/
  risk_modeling/
  report/
```

---

## T4.2 文件保存服务

### T4.2.1 StorageService 方法

```text
save_uploaded_file()
get_project_storage_path()
get_sample_storage_path()
get_task_output_path()
list_project_files()
```

### T4.2.2 文件命名规则

```text
{timestamp}_{file_type}_{original_filename}
```

### T4.2.3 文件元信息

```text
file_id
file_name
file_type
file_path
file_size
uploaded_at
```

### T4.2.4 对象存储兼容设计

```text
StorageAdapter
  LocalStorageAdapter
  MinIOStorageAdapter  # 预留
  S3StorageAdapter     # 预留
```

---

# T5. 分析任务调度中心搭建

## T5.1 TaskOrchestrator

### T5.1.1 创建服务

```text
backend/app/services/task_orchestrator.py
```

### T5.1.2 按 task_type 路由 Skill Runner

```text
image_segmentation       → SegmentationSkillRunner
gwas_analysis            → GWASSkillRunner
opengwas_fetch           → OpenGWASSkillRunner
mendelian_randomization  → MRSkillRunner
mediation_mr             → MediationMRSkillRunner
risk_modeling            → RiskModelSkillRunner
report_generation        → ReportSkillRunner
```

### T5.1.3 任务生命周期

```text
create task
set status pending
set status running
run script
parse output
save result
set status success
handle error
set status failed
```

### T5.1.4 任务进度标准

```text
0%   created
10%  preparing inputs
30%  running mock script
70%  parsing outputs
90%  saving results
100% success
```

---

## T5.2 Skill Runner 基类

### T5.2.1 BaseSkillRunner 方法

```text
prepare_inputs()
build_command()
run()
parse_outputs()
save_results()
```

### T5.2.2 子进程调用

```text
使用 subprocess 调用 Python / R 脚本
捕获 stdout
捕获 stderr
记录 exit_code
```

### T5.2.3 日志写入

每个 task 生成：

```text
run.log
command.txt
output_manifest.json
```

### T5.2.4 失败处理

```text
脚本不存在
脚本执行失败
输出文件缺失
输出 JSON 格式错误
任务超时
```

---

# T6. Mock 分析 Skill 脚本体系搭建

## T6.1 Image Segmentation Mock Skill

### T6.1.1 脚本路径

```text
analysis_scripts/segmentation/mock_segmentation.py
```

### T6.1.2 命令行参数

```bash
python mock_segmentation.py \
  --input-mri path/to/mri.nii.gz \
  --output-dir storage/.../segmentation \
  --task-id task_001
```

### T6.1.3 输出文件

```text
mask.nii.gz
overlay_preview.png
segmentation_metrics.json
fat_quantification.csv
```

### T6.1.4 输出 JSON 示例

```json
{
  "liver_pdff": 11.42,
  "visceral_fat_volume": 3850.2,
  "subcutaneous_fat_volume": 6420.7,
  "bone_marrow_fat_fraction": 0.36,
  "dice_liver": 0.94,
  "dice_visceral_fat": 0.91,
  "qc_status": "passed"
}
```

---

## T6.2 GWAS Mock Skill

### T6.2.1 脚本路径

```text
analysis_scripts/gwas/mock_gwas.py
```

### T6.2.2 命令行参数

```bash
python mock_gwas.py \
  --phenotype Liver_PDFF \
  --sample-size 40484 \
  --output-dir storage/.../gwas \
  --task-id task_002
```

### T6.2.3 输出文件

```text
gwas_summary_stats.tsv
lead_snps.csv
significant_loci.csv
manhattan_plot.png
qq_plot.png
gwas_summary.json
```

### T6.2.4 输出 JSON 示例

```json
{
  "phenotype": "Liver_PDFF",
  "sample_size": 40484,
  "significant_loci_count": 18,
  "lead_snps_count": 12,
  "lambda_gc": 1.03
}
```

---

## T6.3 OpenGWAS / IEU API Mock Skill

### T6.3.1 脚本路径

```text
analysis_scripts/opengwas/mock_opengwas_fetch.py
```

### T6.3.2 命令行参数

```bash
python mock_opengwas_fetch.py \
  --outcome-id ukb-b-12141 \
  --snp-list lead_snps.csv \
  --output-dir storage/.../opengwas \
  --task-id task_003
```

### T6.3.3 输出文件

```text
outcome_summary_stats.tsv
harmonised_preview.csv
opengwas_metadata.json
```

### T6.3.4 输出 JSON 示例

```json
{
  "outcome_id": "ukb-b-12141",
  "outcome_name": "Osteoporosis",
  "matched_snps": 12,
  "proxy_snps_used": 0,
  "source": "Mock IEU OpenGWAS"
}
```

---

## T6.4 Mendelian Randomization Mock Skill

### T6.4.1 脚本路径

```text
analysis_scripts/mr/mock_two_sample_mr.R
```

### T6.4.2 命令行参数

```bash
Rscript mock_two_sample_mr.R \
  --exposure Liver_PDFF \
  --outcome Osteoporosis \
  --output-dir storage/.../mr \
  --task-id task_004
```

### T6.4.3 输出文件

```text
mr_results.csv
heterogeneity.csv
pleiotropy.csv
single_snp_results.csv
forest_plot.png
scatter_plot.png
mr_summary.json
```

### T6.4.4 输出 JSON 示例

```json
{
  "exposure": "Liver_PDFF",
  "outcome": "Osteoporosis",
  "method": "IVW",
  "beta": 0.184,
  "or": 1.20,
  "ci_lower": 1.06,
  "ci_upper": 1.37,
  "p_value": 0.004,
  "cochran_q_p": 0.31,
  "egger_intercept_p": 0.42
}
```

---

## T6.5 Mediation MR Mock Skill

### T6.5.1 脚本路径

```text
analysis_scripts/mediation_mr/mock_mediation_mr.R
```

### T6.5.2 命令行参数

```bash
Rscript mock_mediation_mr.R \
  --exposure Liver_PDFF \
  --outcome Osteoporosis \
  --mediator-source deCODE_plasma_proteins \
  --output-dir storage/.../mediation_mr \
  --task-id task_005
```

### T6.5.3 输出文件

```text
mediation_results.csv
candidate_proteins.csv
mediation_barplot.png
mediation_summary.json
```

### T6.5.4 候选蛋白

```text
ACY1
H6PD
SHBG
ADH1A
POR
NAAA
```

### T6.5.5 输出 JSON 示例

```json
{
  "exposure": "Liver_PDFF",
  "outcome": "Osteoporosis",
  "mediator_source": "deCODE_plasma_proteins",
  "tested_proteins": 4907,
  "significant_mediators": 5,
  "top_mediators": [
    {
      "protein": "ACY1",
      "beta_a": 0.071,
      "beta_b": 0.013,
      "indirect_effect": 0.0010,
      "proportion_mediated": 1.642,
      "p_mediation": 0.001
    }
  ]
}
```

---

## T6.6 Risk Modeling Mock Skill

### T6.6.1 脚本路径

```text
analysis_scripts/risk_modeling/mock_risk_modeling.py
```

### T6.6.2 命令行参数

```bash
python mock_risk_modeling.py \
  --exposure Liver_PDFF \
  --outcome Osteoporosis \
  --output-dir storage/.../risk_modeling \
  --task-id task_006
```

### T6.6.3 输出文件

```text
ols_results.csv
rcs_results.csv
multinomial_logistic_results.csv
rcs_curve.png
risk_summary.json
```

### T6.6.4 输出 JSON 示例

```json
{
  "pdff_quartile": "Q4",
  "osteopenia_aor": 1.14,
  "osteoporosis_aor": 1.24,
  "risk_level": "High",
  "model_type": "OLS + RCS + Multinomial Logistic"
}
```

---

# T7. 前端 Web 工作台搭建

## T7.1 项目管理页面

### T7.1.1 项目列表页

展示：

```text
项目名称
研究目标
创建时间
项目状态
进入项目工作台按钮
```

### T7.1.2 创建项目页

表单字段：

```text
项目名称
研究目标
暴露变量
结局变量
是否启用中介 MR
是否启用风险建模
```

### T7.1.3 项目详情页

展示：

```text
项目基本信息
数据上传状态
任务完成进度
最新分析结果摘要
```

---

## T7.2 数据上传页面

### T7.2.1 MRI 上传组件

```text
支持 .nii.gz / .dcm / .zip mock 上传
显示上传进度
显示文件大小
显示文件状态
```

### T7.2.2 表型文件上传组件

```text
支持 .csv
展示字段预览
```

### T7.2.3 协变量文件上传组件

```text
支持 .csv
展示字段预览
```

### T7.2.4 模拟数据选择组件

```text
提供一键使用 mock dataset
无需真实上传即可启动完整流程
```

---

## T7.3 分析工作台页面

### T7.3.1 工作流步骤条

```text
1. Image Segmentation
2. GWAS Analysis
3. OpenGWAS Fetch
4. Mendelian Randomization
5. Mediation MR
6. Risk Modeling
7. Report Generation
```

### T7.3.2 任务卡片

每个模块展示：

```text
模块名称
输入数据
运行状态
进度条
启动按钮
查看结果按钮
重跑按钮
```

### T7.3.3 任务状态刷新

```text
轮询 GET /tasks/{task_id}
每 2 秒刷新一次
任务成功后自动加载结果
```

### T7.3.4 全流程一键运行

```text
点击 Run Full Pipeline
系统按顺序触发所有 mock 任务
前一个任务 success 后启动下一个任务
```

---

# T8. 分析结果展示模块搭建

## T8.1 影像分割结果展示

### T8.1.1 分割预览卡片

```text
展示 overlay_preview.png
展示 mask 文件路径
展示 QC 状态
```

### T8.1.2 脂肪表型指标卡

```text
Liver PDFF
Visceral Fat Volume
Subcutaneous Fat Volume
Bone Marrow Fat Fraction
```

### T8.1.3 模型性能指标卡

```text
Dice Liver
Dice Visceral Fat
Dice Subcutaneous Fat
Dice Bone Marrow
```

---

## T8.2 GWAS 结果展示

### T8.2.1 GWAS 摘要卡

```text
样本量
表型名称
显著位点数
lead SNP 数
lambda GC
```

### T8.2.2 Manhattan 图展示

```text
展示 manhattan_plot.png
```

### T8.2.3 QQ 图展示

```text
展示 qq_plot.png
```

### T8.2.4 显著 SNP 表格

```text
SNP
CHR
BP
EA
OA
BETA
SE
P
```

---

## T8.3 MR 结果展示

### T8.3.1 MR 摘要卡

```text
Exposure
Outcome
Method
Beta
OR
95% CI
P value
```

### T8.3.2 敏感性分析卡

```text
Cochran's Q P
MR-Egger intercept P
IV count
```

### T8.3.3 森林图展示

```text
展示 forest_plot.png
```

### T8.3.4 散点图展示

```text
展示 scatter_plot.png
```

---

## T8.4 Mediation MR 结果展示

### T8.4.1 候选蛋白排行榜

```text
Protein
Path A beta
Path B beta
Indirect effect
Proportion mediated
P mediation
```

### T8.4.2 中介比例图

```text
展示 mediation_barplot.png
```

### T8.4.3 候选蛋白详情卡

```text
ACY1
H6PD
SHBG
ADH1A
POR
NAAA
```

### T8.4.4 解释性文案区域

```text
说明该蛋白可能介导 Liver PDFF → Osteoporosis 的部分因果效应
标注当前为 mock 结果
```

---

## T8.5 风险建模结果展示

### T8.5.1 风险等级卡

```text
Low / Medium / High
```

### T8.5.2 风险指标卡

```text
Osteopenia aOR
Osteoporosis aOR
PDFF Quartile
```

### T8.5.3 RCS 曲线展示

```text
展示 rcs_curve.png
```

### T8.5.4 风险解释区域

```text
根据 PDFF 分层解释骨量减少和骨质疏松风险
```

---

# T9. 科研报告生成模块搭建

## T9.1 报告生成后端

### T9.1.1 创建报告生成 API

```text
POST /api/v1/projects/{project_id}/reports/generate
```

### T9.1.2 读取所有模块结果

```text
segmentation_result
gwas_result
opengwas_result
mr_result
mediation_result
risk_result
```

### T9.1.3 生成 Markdown 报告

```text
final_report.md
```

### T9.1.4 写入报告记录

```text
写入 reports 表
保存 report_id
保存 markdown 内容
保存文件路径
```

---

## T9.2 报告内容结构

```text
1. 项目摘要
2. 影像分割结果
3. 脂肪表型指标
4. GWAS 结果
5. OpenGWAS 数据获取结果
6. MR 因果推断结果
7. Mediation MR 中介蛋白结果
8. Risk Modeling 风险建模结果
9. 结论
10. 当前 mock-first 限制
11. 后续真实模块替换说明
```

---

# T10. 日志、异常、审计与可追溯机制搭建

## T10.1 任务日志

每个任务保存：

```text
run.log
command.txt
output_manifest.json
```

前端任务详情页展示：

```text
stdout
stderr
exit_code
start_time
finish_time
```

---

## T10.2 错误处理

### T10.2.1 错误码

```text
SCRIPT_NOT_FOUND
SCRIPT_EXECUTION_FAILED
OUTPUT_FILE_MISSING
OUTPUT_JSON_INVALID
TASK_TIMEOUT
FILE_UPLOAD_FAILED
DATABASE_ERROR
```

### T10.2.2 后端统一异常返回

```json
{
  "error_code": "OUTPUT_JSON_INVALID",
  "message": "The mock script output JSON is invalid.",
  "trace_id": "trace_001"
}
```

### T10.2.3 前端错误展示

```text
展示错误类型
展示错误原因
提供重跑按钮
```

---

## T10.3 审计记录

### T10.3.1 audit_logs 表

```text
log_id
project_id
task_id
action
operator
detail_json
created_at
```

### T10.3.2 记录关键行为

```text
创建项目
上传文件
启动任务
取消任务
重跑任务
生成报告
```

### T10.3.3 前端审计时间线

```text
项目详情页展示操作时间线
```

---

# T11. 测试数据、演示流程与验收用例搭建

## T11.1 Mock 数据集

### T11.1.1 模拟 MRI 文件占位

```text
mock_data/mri/mock_mri_001.nii.gz
```

### T11.1.2 模拟表型文件

```text
mock_data/phenotype/mock_phenotype.csv
```

### T11.1.3 模拟协变量文件

```text
mock_data/covariates/mock_covariates.csv
```

### T11.1.4 模拟 SNP 文件

```text
mock_data/genetics/mock_lead_snps.csv
```

---

## T11.2 一键演示流程

### T11.2.1 demo seed 脚本

```text
backend/scripts/seed_demo_project.py
```

### T11.2.2 自动创建演示项目

```text
项目名称：Demo - Liver PDFF and Osteoporosis
暴露变量：Liver_PDFF
结局变量：Osteoporosis
中介变量：deCODE plasma proteins
```

### T11.2.3 自动挂载 mock 数据

```text
MRI
phenotype
covariates
lead SNPs
```

### T11.2.4 一键运行全部 mock 分析

```text
backend/scripts/run_all_demo_tasks.py
```

---

## T11.3 验收用例

### T11.3.1 创建项目验收

```text
用户能创建项目
项目能进入详情页
数据库中有 project 记录
```

### T11.3.2 文件上传验收

```text
用户能上传文件
文件能保存到 storage
数据库中有文件元信息
```

### T11.3.3 任务执行验收

```text
用户能启动 segmentation 任务
任务状态从 pending → running → success
输出文件真实生成
结果写入数据库
```

### T11.3.4 全流程验收

```text
用户点击 Run Full Pipeline
系统依次完成：
segmentation
gwas
opengwas
mr
mediation_mr
risk_modeling
report_generation
```

### T11.3.5 报告验收

```text
用户能打开报告页
报告包含所有模块结果
报告能保存为 Markdown
```

---

# T12. 本地部署、开发文档与 real 模块替换说明

## T12.1 本地部署

### T12.1.1 后端启动文档

```bash
cd backend
python -m venv .venv
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### T12.1.2 前端启动文档

```bash
cd frontend
npm install
npm run dev
```

### T12.1.3 数据库启动文档

```text
使用本地 PostgreSQL
或使用 docker-compose 启动 PostgreSQL
```

### T12.1.4 一键启动脚本

```text
scripts/start_dev.ps1
scripts/start_dev.sh
```

---

## T12.2 开发文档

```text
docs/architecture.md
docs/api.md
docs/database_schema.md
docs/task_orchestrator.md
docs/mock_skills.md
docs/real_module_replacement.md
```

---

## T12.3 real 模块替换说明

### T12.3.1 TSSA-UNet 替换

```text
将 mock_segmentation.py 替换为 run_tssa_unet_inference.py
保持输入参数和输出 JSON 不变
```

### T12.3.2 OpenGWAS 替换

```text
将 mock_opengwas_fetch.py 替换为 real_opengwas_fetch.py
通过 IEU API 获取真实 outcome summary data
保持输出 schema 不变
```

### T12.3.3 MR 脚本替换

```text
将 mock_two_sample_mr.R 替换为 run_two_sample_mr.R
保持 mr_summary.json 和图表输出不变
```

### T12.3.4 Mediation MR 替换

```text
将 mock_mediation_mr.R 替换为 run_mediation_mr.R
接入真实 pQTL 数据
保持 mediation_summary.json 不变
```

### T12.3.5 GWAS 替换

```text
将 mock_gwas.py 替换为 run_regenie_pipeline.sh
保留 gwas_summary.json、manhattan_plot.png、qq_plot.png 等输出协议
```

---

# 2. 推荐 Claude Code 执行顺序

```text
第 1 轮：
完成项目目录、FastAPI 后端、Next.js 前端、README、基础启动。

第 2 轮：
完成数据库模型、Pydantic schema、项目 API、任务 API、文件 API。

第 3 轮：
完成 storage 文件系统、任务调度中心、BaseSkillRunner。

第 4 轮：
完成所有 mock scripts：
segmentation
gwas
opengwas
mr
mediation_mr
risk_modeling

第 5 轮：
完成前端项目管理页、上传页、分析工作台。

第 6 轮：
完成各模块结果展示页。

第 7 轮：
完成报告生成模块。

第 8 轮：
完成日志、错误处理、审计记录。

第 9 轮：
完成 mock 数据、一键演示流程、验收用例。

第 10 轮：
完成部署文档、架构文档、real 模块替换说明。
```

---

# 3. 最终交付物清单

```text
1. 可运行的前端 Web 系统
2. 可运行的 FastAPI 后端
3. PostgreSQL 数据库结构
4. 本地文件存储结构
5. 分析任务调度中心
6. 6 类 mock 分析脚本
7. 项目管理页面
8. 数据上传页面
9. 分析工作台页面
10. 分割结果展示页面
11. GWAS 结果展示页面
12. MR 结果展示页面
13. Mediation MR 结果展示页面
14. 风险建模结果展示页面
15. 科研报告生成页面
16. 一键演示数据
17. 一键运行 mock pipeline
18. 系统架构文档
19. API 文档
20. 数据库设计文档
21. Mock skill 说明文档
22. 后续真实模型/API/脚本替换说明
```

---

# 4. 最关键验收标准

```text
用户能从创建项目开始，一路运行到科研报告生成。
每一步都有任务状态、输出文件、结果 JSON、日志和页面展示。
底层虽然是 mock 脚本，但未来可以逐个替换为真实 TSSA-UNet、OpenGWAS API、MR R 脚本和 GWAS 流程。
```

---

# 5. 给 AI 编程助手的总指令

```text
你需要基于本 Markdown 文件搭建 AdipoInsight Mock-First 系统。
禁止只做静态页面。
禁止把结果硬编码在前端。
必须实现真实 API、真实任务记录、真实文件输出、真实任务状态流转、真实日志和真实结果 schema。
计算部分允许使用 mock 脚本，但 mock 脚本必须像真实分析脚本一样被后端调度执行。
所有模块都要保留未来替换为 real 模块的接口边界。
每完成一个阶段，需要更新 README 和 docs 中对应文档。
```
