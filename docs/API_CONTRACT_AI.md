# AdipoInsight AI API 契约文档

> 版本：v0.3.0-draft
> 日期：2026-05-17
> 状态：契约定义（后端实现以本文档为准）
> Base URL：`http://localhost:8000/api`

---

## 接口总览

| # | Method | Path | 能力 | 前端页面 |
|---|--------|------|------|---------|
| 1 | POST | `/api/files/upload` | 文件上传 | ImageProcessingModule |
| 2 | POST | `/api/ai/segmentation/jobs` | C1 影像分割 | ImageProcessingModule |
| 3 | POST | `/api/ai/phenotype/jobs` | C2 表型量化 | ImageProcessingModule |
| 4 | POST | `/api/ai/gwas/jobs` | C3 GWAS | GWASModule |
| 5 | POST | `/api/ai/mr/jobs` | C4 双样本 MR | MRModule |
| 6 | POST | `/api/ai/mediation-mr/jobs` | C5 中介 MR | MediationMRModule |
| 7 | POST | `/api/ai/risk-modeling/jobs` | C6 风险建模 | TaskCard / Pipeline |
| 8 | POST | `/api/ai/report/jobs` | C7 报告生成 | ProjectWorkspacePage |
| 9 | GET | `/api/ai/jobs/{jobId}` | 任务状态 | 所有页面（轮询） |
| 10 | GET | `/api/ai/jobs/{jobId}/result` | 任务结果 | UnifiedResultView |
| 11 | POST | `/api/ai/jobs/{jobId}/cancel` | 取消任务 | TaskCard |

---

## 通用约定

### 命名规则

```
/api/files/upload                         — 文件
/api/ai/{capability}/jobs                 — 创建 AI 任务
/api/ai/jobs/{jobId}                      — 查询任务状态
/api/ai/jobs/{jobId}/result               — 查询任务结果
/api/ai/jobs/{jobId}/cancel               — 取消任务
```

### 通用 Response Envelope

所有接口返回统一的顶层结构：

```json
{
  "success": true,
  "data": { ... },
  "error": null,
  "request_id": "req_a1b2c3d4"
}
```

失败时：

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "SCRIPT_EXECUTION_FAILED",
    "message": "GWAS 脚本退出码 1：缺少 phenotype 列",
    "details": { "exit_code": 1, "stderr": "..." }
  },
  "request_id": "req_a1b2c3d4"
}
```

### 通用错误码

| 错误码 | HTTP Status | 含义 |
|--------|------------|------|
| `INVALID_PARAMETER` | 400 | 请求参数不合法 |
| `PROJECT_NOT_FOUND` | 404 | 项目不存在 |
| `JOB_NOT_FOUND` | 404 | 任务不存在 |
| `RESULT_NOT_FOUND` | 404 | 结果未生成 |
| `FILE_NOT_FOUND` | 404 | 文件不存在 |
| `FILE_TOO_LARGE` | 413 | 文件超过大小限制 |
| `UNSUPPORTED_FORMAT` | 415 | 文件格式不支持 |
| `ADAPTER_NOT_FOUND` | 500 | 未找到能力适配器 |
| `SCRIPT_NOT_FOUND` | 500 | 分析脚本不存在 |
| `SCRIPT_EXECUTION_FAILED` | 500 | 分析脚本执行失败 |
| `OUTPUT_JSON_INVALID` | 500 | 脚本输出格式错误 |
| `TASK_TIMEOUT` | 504 | 任务超时（300s） |
| `UPSTREAM_DEPENDENCY_FAILED` | 409 | 上游依赖未完成 |
| `JOB_ALREADY_CANCELLED` | 409 | 任务已被取消 |
| `DATABASE_ERROR` | 500 | 数据库异常 |
| `INTERNAL_ERROR` | 500 | 未知内部错误 |

### 任务状态机

```
pending ──→ running ──→ success
  │           │
  └──→ cancelled         └──→ failed
```

终态：`success`、`failed`、`cancelled`
非终态：`pending`、`running`

### Job 对象通用结构

```json
{
  "job_id": 42,
  "project_id": 3,
  "capability": "gwas_analysis",
  "status": "running",
  "progress": 45,
  "progress_stage": "处理中",
  "input": { ... },
  "output_summary": null,
  "output_files": [],
  "error_code": "",
  "error_message": "",
  "created_at": "2026-05-17T14:30:00Z",
  "started_at": "2026-05-17T14:30:01Z",
  "finished_at": null,
  "updated_at": "2026-05-17T14:30:15Z"
}
```

---

## 接口详细定义

---

### 1. POST /api/files/upload

| 属性 | 内容 |
|------|------|
| **作用** | 上传医学影像或科研数据文件 |
| **Content-Type** | `multipart/form-data` |
| **最大文件大小** | 200 MB |
| **对应前端页面** | `ImageProcessingModule`（上传区） |
| **对应 Adapter** | 无（纯 I/O 操作，由 `StorageService` 处理） |

**Request（multipart/form-data）**：

| Field | Type | Required | 说明 |
|-------|------|----------|------|
| `file` | binary | yes | 文件内容 |
| `project_id` | integer | yes | 所属项目 ID |
| `file_type` | string | yes | `mri` / `phenotype` / `covariates` / `genotype` |

**cURL 示例**：
```bash
curl -X POST http://localhost:8000/api/files/upload \
  -F "file=@T1_abdomen.nii.gz" \
  -F "project_id=3" \
  -F "file_type=mri"
```

**Response 200**：
```json
{
  "success": true,
  "data": {
    "file_id": 15,
    "project_id": 3,
    "file_name": "T1_abdomen.nii.gz",
    "file_type": "mri",
    "file_path": "storage/projects/3/raw/mri/20260517_143000_T1_abdomen.nii.gz",
    "file_size": 45678901,
    "checksum_sha256": "e3b0c44298fc1c14...",
    "created_at": "2026-05-17T14:30:00Z"
  },
  "error": null,
  "request_id": "req_a1b2c3d4"
}
```

**错误响应**：

| Status | error.code | 场景 |
|--------|-----------|------|
| 400 | `INVALID_PARAMETER` | file_type 不在枚举中 |
| 404 | `PROJECT_NOT_FOUND` | project_id 不存在 |
| 413 | `FILE_TOO_LARGE` | 文件 > 200MB |
| 415 | `UNSUPPORTED_FORMAT` | 文件后缀不在白名单 |
| 500 | `INTERNAL_ERROR` | 存储写入失败 |

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "UNSUPPORTED_FORMAT",
    "message": "不支持的文件格式：.mp4。支持：.nii, .nii.gz, .dcm, .dicom, .csv, .tsv, .vcf, .vcf.gz, .bed, .bim, .fam",
    "details": { "received_extension": ".mp4" }
  },
  "request_id": "req_e5f6g7h8"
}
```

---

### 2. POST /api/ai/segmentation/jobs

| 属性 | 内容 |
|------|------|
| **作用** | 创建 AI 影像分割任务（C1） |
| **对应前端页面** | `ImageProcessingModule` |
| **对应 Adapter** | `adapters/image_segmentation/` |
| **依赖** | 无 |

**Request Body（JSON）**：
```json
{
  "project_id": 3,
  "file_id": 15,
  "target_structures": ["liver", "visceral_fat", "subcutaneous_fat", "bone_marrow"],
  "model_version": "tssa-unet-v2",
  "options": {
    "use_gpu": true,
    "batch_size": 1
  }
}
```

| Field | Type | Required | Default | 说明 |
|-------|------|----------|---------|------|
| `project_id` | integer | yes | — | 项目 ID |
| `file_id` | integer | yes | — | 已上传 MRI 文件 ID |
| `target_structures` | string[] | no | 全部 4 项 | 目标解剖结构 |
| `model_version` | string | no | `"tssa-unet-v2"` | 模型版本 |
| `options` | object | no | `{}` | 推理选项 |

**Response 201**：
```json
{
  "success": true,
  "data": {
    "job_id": 42,
    "project_id": 3,
    "capability": "image_segmentation",
    "status": "pending",
    "progress": 0,
    "progress_stage": "初始化",
    "input": {
      "file_id": 15,
      "target_structures": ["liver", "visceral_fat", "subcutaneous_fat", "bone_marrow"],
      "model_version": "tssa-unet-v2"
    },
    "output_summary": null,
    "output_files": [],
    "created_at": "2026-05-17T14:30:00Z"
  },
  "error": null,
  "request_id": "req_a1b2c3d4"
}
```

**错误响应**：

| Status | error.code | 场景 |
|--------|-----------|------|
| 400 | `INVALID_PARAMETER` | target_structures 含无效值 |
| 404 | `PROJECT_NOT_FOUND` | project_id 不存在 |
| 404 | `FILE_NOT_FOUND` | file_id 不存在或类型非 mri |
| 500 | `ADAPTER_NOT_FOUND` | 适配器未注册 |

---

### 3. POST /api/ai/phenotype/jobs

| 属性 | 内容 |
|------|------|
| **作用** | 创建脂肪表型量化任务（C2） |
| **对应前端页面** | `ImageProcessingModule`（"保存并继续分析"按钮） |
| **对应 Adapter** | `adapters/phenotype_quantification/` |
| **依赖** | C1 影像分割必须已完成 |

**Request Body（JSON）**：
```json
{
  "project_id": 3,
  "segmentation_job_id": 42
}
```

| Field | Type | Required | 说明 |
|-------|------|----------|------|
| `project_id` | integer | yes | 项目 ID |
| `segmentation_job_id` | integer | yes | 已完成的分割任务 ID（取其输出） |

**Response 201**：
```json
{
  "success": true,
  "data": {
    "job_id": 43,
    "project_id": 3,
    "capability": "phenotype_quantification",
    "status": "pending",
    "progress": 0,
    "progress_stage": "初始化",
    "input": {
      "segmentation_job_id": 42
    },
    "output_summary": null,
    "output_files": [],
    "created_at": "2026-05-17T14:30:05Z"
  },
  "error": null,
  "request_id": "req_i9j0k1l2"
}
```

**错误响应**：

| Status | error.code | 场景 |
|--------|-----------|------|
| 404 | `JOB_NOT_FOUND` | segmentation_job_id 不存在 |
| 409 | `UPSTREAM_DEPENDENCY_FAILED` | C1 任务未成功完成 |

---

### 4. POST /api/ai/gwas/jobs

| 属性 | 内容 |
|------|------|
| **作用** | 创建 GWAS 全基因组关联分析任务（C3） |
| **对应前端页面** | `GWASModule` |
| **对应 Adapter** | `adapters/gwas_analysis/` |
| **依赖** | C2 表型量化已完成 |

**Request Body（JSON）**：
```json
{
  "project_id": 3,
  "phenotype": "Liver_PDFF",
  "covariates": ["age", "sex", "bmi", "PC1", "PC2", "PC3", "PC4", "PC5", "PC6", "PC7", "PC8", "PC9", "PC10"],
  "maf_threshold": 0.01,
  "hwe_threshold": 1e-6,
  "geno_file_id": 16
}
```

| Field | Type | Required | Default | 说明 |
|-------|------|----------|---------|------|
| `project_id` | integer | yes | — | 项目 ID |
| `phenotype` | string | yes | — | 表型列名（来自 C2 输出） |
| `covariates` | string[] | no | `[]` | 协变量列表 |
| `maf_threshold` | number | no | `0.01` | 最小等位基因频率阈值 |
| `hwe_threshold` | number | no | `1e-6` | Hardy-Weinberg 平衡 p 阈值 |
| `geno_file_id` | integer | no | — | 基因型文件 ID |

**Response 201**：
```json
{
  "success": true,
  "data": {
    "job_id": 44,
    "project_id": 3,
    "capability": "gwas_analysis",
    "status": "pending",
    "progress": 0,
    "progress_stage": "初始化",
    "input": {
      "phenotype": "Liver_PDFF",
      "covariates": ["age", "sex", "bmi", "PC1", "PC2", "PC3"],
      "maf_threshold": 0.01,
      "hwe_threshold": 1e-6
    },
    "output_summary": null,
    "output_files": [],
    "created_at": "2026-05-17T14:30:10Z"
  },
  "error": null,
  "request_id": "req_m3n4o5p6"
}
```

**错误响应**：

| Status | error.code | 场景 |
|--------|-----------|------|
| 400 | `INVALID_PARAMETER` | phenotype 为空、maf_threshold 不在 0~0.5 范围 |
| 404 | `FILE_NOT_FOUND` | geno_file_id 不存在 |

---

### 5. POST /api/ai/mr/jobs

| 属性 | 内容 |
|------|------|
| **作用** | 创建双样本孟德尔随机化分析任务（C4） |
| **对应前端页面** | `MRModule` |
| **对应 Adapter** | `adapters/two_sample_mr/` |
| **依赖** | C3 GWAS（暴露）+ OpenGWAS 数据（结局）已完成 |

**Request Body（JSON）**：
```json
{
  "project_id": 3,
  "exposure": "Liver_PDFF",
  "outcome": "Osteoporosis",
  "exposure_gwas_job_id": 44,
  "outcome_source": "opengwas",
  "outcome_id": "ukb-b-12141",
  "methods": ["IVW", "MR-Egger", "Weighted Median", "Weighted Mode"],
  "clump_r2": 0.001,
  "clump_kb": 10000,
  "p_threshold": 5e-8
}
```

| Field | Type | Required | Default | 说明 |
|-------|------|----------|---------|------|
| `project_id` | integer | yes | — | 项目 ID |
| `exposure` | string | yes | — | 暴露名称 |
| `outcome` | string | yes | — | 结局名称 |
| `exposure_gwas_job_id` | integer | yes | — | 暴露 GWAS 任务 ID |
| `outcome_source` | string | no | `"opengwas"` | `opengwas` / `upload` / `job_id` |
| `outcome_id` | string | no | — | OpenGWAS ID（如 ukb-b-12141） |
| `outcome_gwas_job_id` | integer | no | — | 如果 outcome_source=job_id |
| `methods` | string[] | no | 全部 4 种 | MR 方法列表 |
| `clump_r2` | number | no | `0.001` | LD clumping R² |
| `clump_kb` | integer | no | `10000` | LD clumping 窗口 kb |
| `p_threshold` | number | no | `5e-8` | 工具变量显著性阈值 |

**Response 201**：
```json
{
  "success": true,
  "data": {
    "job_id": 45,
    "project_id": 3,
    "capability": "mendelian_randomization",
    "status": "pending",
    "progress": 0,
    "progress_stage": "初始化",
    "input": {
      "exposure": "Liver_PDFF",
      "outcome": "Osteoporosis",
      "exposure_gwas_job_id": 44,
      "outcome_source": "opengwas",
      "outcome_id": "ukb-b-12141",
      "methods": ["IVW", "MR-Egger", "Weighted Median", "Weighted Mode"]
    },
    "output_summary": null,
    "output_files": [],
    "created_at": "2026-05-17T14:30:15Z"
  },
  "error": null,
  "request_id": "req_q7r8s9t0"
}
```

**错误响应**：

| Status | error.code | 场景 |
|--------|-----------|------|
| 400 | `INVALID_PARAMETER` | methods 含无效值 |
| 404 | `JOB_NOT_FOUND` | exposure_gwas_job_id 不存在 |
| 409 | `UPSTREAM_DEPENDENCY_FAILED` | 暴露 GWAS 未成功 |

---

### 6. POST /api/ai/mediation-mr/jobs

| 属性 | 内容 |
|------|------|
| **作用** | 创建中介孟德尔随机化分析任务（C5） |
| **对应前端页面** | `MediationMRModule` |
| **对应 Adapter** | `adapters/mediation_mr/` |
| **依赖** | C3 GWAS + C4 MR 已完成 |

**Request Body（JSON）**：
```json
{
  "project_id": 3,
  "exposure": "Liver_PDFF",
  "outcome": "Osteoporosis",
  "mediator_source": "decode_plasma",
  "gwas_job_id": 44,
  "mr_job_id": 45,
  "correction_method": "fdr",
  "alpha": 0.05
}
```

| Field | Type | Required | Default | 说明 |
|-------|------|----------|---------|------|
| `project_id` | integer | yes | — | 项目 ID |
| `exposure` | string | yes | — | 暴露名称 |
| `outcome` | string | yes | — | 结局名称 |
| `mediator_source` | string | yes | — | `decode_plasma` / `metabolite_gwas` / `gwas_catalog` / `custom` |
| `gwas_job_id` | integer | yes | — | 暴露 GWAS 任务 ID |
| `mr_job_id` | integer | no | — | MR 任务 ID（用于 IV 选择） |
| `custom_mediator_file_id` | integer | no | — | mediator_source=custom 时的文件 ID |
| `correction_method` | string | no | `"fdr"` | `bonferroni` / `fdr` / `none` |
| `alpha` | number | no | `0.05` | 显著性阈值 |

**Response 201**：
```json
{
  "success": true,
  "data": {
    "job_id": 46,
    "project_id": 3,
    "capability": "mediation_mr",
    "status": "pending",
    "progress": 0,
    "progress_stage": "初始化",
    "input": {
      "exposure": "Liver_PDFF",
      "outcome": "Osteoporosis",
      "mediator_source": "decode_plasma",
      "gwas_job_id": 44,
      "correction_method": "fdr",
      "alpha": 0.05
    },
    "output_summary": null,
    "output_files": [],
    "created_at": "2026-05-17T14:30:20Z"
  },
  "error": null,
  "request_id": "req_u1v2w3x4"
}
```

**错误响应**：

| Status | error.code | 场景 |
|--------|-----------|------|
| 400 | `INVALID_PARAMETER` | mediator_source 不在枚举中、alpha 超出 0~1 |
| 404 | `JOB_NOT_FOUND` | gwas_job_id 不存在 |
| 409 | `UPSTREAM_DEPENDENCY_FAILED` | GWAS 任务未成功 |

---

### 7. POST /api/ai/risk-modeling/jobs

| 属性 | 内容 |
|------|------|
| **作用** | 创建疾病风险建模任务（C6） |
| **对应前端页面** | 通过 `TaskCard` / Pipeline 自动触发 |
| **对应 Adapter** | `adapters/risk_modeling/` |
| **依赖** | C2 表型 + C4 MR + C5 中介 MR（至少 MR 完成）|

**Request Body（JSON）**：
```json
{
  "project_id": 3,
  "exposure": "Liver_PDFF",
  "outcome": "Osteoporosis",
  "phenotype_job_id": 43,
  "mr_job_id": 45,
  "mediation_mr_job_id": 46,
  "grouping": "quartile",
  "covariates": ["age", "sex", "bmi"]
}
```

| Field | Type | Required | Default | 说明 |
|-------|------|----------|---------|------|
| `project_id` | integer | yes | — | 项目 ID |
| `exposure` | string | yes | — | 暴露名称 |
| `outcome` | string | yes | — | 结局名称 |
| `phenotype_job_id` | integer | yes | — | 表型量化任务 ID |
| `mr_job_id` | integer | no | — | MR 任务 ID |
| `mediation_mr_job_id` | integer | no | — | 中介 MR 任务 ID |
| `grouping` | string | no | `"quartile"` | `quartile` / `tertile` / `median` |
| `covariates` | string[] | no | `[]` | 纳入模型的协变量 |

**Response 201**：
```json
{
  "success": true,
  "data": {
    "job_id": 47,
    "project_id": 3,
    "capability": "risk_modeling",
    "status": "pending",
    "progress": 0,
    "progress_stage": "初始化",
    "input": {
      "exposure": "Liver_PDFF",
      "outcome": "Osteoporosis",
      "phenotype_job_id": 43,
      "mr_job_id": 45,
      "grouping": "quartile",
      "covariates": ["age", "sex", "bmi"]
    },
    "output_summary": null,
    "output_files": [],
    "created_at": "2026-05-17T14:30:25Z"
  },
  "error": null,
  "request_id": "req_y5z6a7b8"
}
```

**错误响应**：

| Status | error.code | 场景 |
|--------|-----------|------|
| 400 | `INVALID_PARAMETER` | grouping 不在枚举中 |
| 404 | `JOB_NOT_FOUND` | phenotype_job_id 不存在 |

---

### 8. POST /api/ai/report/jobs

| 属性 | 内容 |
|------|------|
| **作用** | 创建科研报告生成任务（C7） |
| **对应前端页面** | `ProjectWorkspacePage`（"生成分析报告"按钮） / `ReportPage` |
| **对应 Adapter** | `adapters/report_generation/` |
| **依赖** | 至少 1 个分析任务已完成 |

**Request Body（JSON）**：
```json
{
  "project_id": 3,
  "title": "肝脏 PDFF 与骨质疏松因果关系 — 科研分析报告",
  "sections": ["segmentation", "phenotype", "gwas", "mr", "mediation_mr", "risk_modeling", "discussion", "limitations"],
  "language": "zh-CN",
  "include_job_ids": [42, 43, 44, 45, 46, 47]
}
```

| Field | Type | Required | Default | 说明 |
|-------|------|----------|---------|------|
| `project_id` | integer | yes | — | 项目 ID |
| `title` | string | no | `"{项目名} — Analysis Report"` | 报告标题 |
| `sections` | string[] | no | 全部已完成 | 包含的章节 |
| `language` | string | no | `"zh-CN"` | `zh-CN` / `en` |
| `include_job_ids` | integer[] | no | 全部已完成 | 纳入报告的任务 ID 列表 |
| `enable_llm_discussion` | boolean | no | `false` | 是否用 LLM 生成讨论段落 |

**Response 201**：
```json
{
  "success": true,
  "data": {
    "job_id": 48,
    "project_id": 3,
    "capability": "report_generation",
    "status": "pending",
    "progress": 0,
    "progress_stage": "初始化",
    "input": {
      "title": "肝脏 PDFF 与骨质疏松因果关系 — 科研分析报告",
      "sections": ["segmentation", "phenotype", "gwas", "mr", "mediation_mr", "risk_modeling"],
      "language": "zh-CN",
      "include_job_ids": [42, 43, 44, 45, 46, 47]
    },
    "output_summary": null,
    "output_files": [],
    "created_at": "2026-05-17T14:30:30Z"
  },
  "error": null,
  "request_id": "req_c9d0e1f2"
}
```

---

### 9. GET /api/ai/jobs/{jobId}

| 属性 | 内容 |
|------|------|
| **作用** | 查询单个任务的当前状态与进度 |
| **对应前端页面** | 所有页面（轮询 `TaskStore.startPolling`） |
| **对应 Adapter** | 无（直接查 DB） |

**Response 200（运行中）**：
```json
{
  "success": true,
  "data": {
    "job_id": 44,
    "project_id": 3,
    "capability": "gwas_analysis",
    "status": "running",
    "progress": 45,
    "progress_stage": "处理中",
    "input": {
      "phenotype": "Liver_PDFF",
      "covariates": ["age", "sex", "bmi"],
      "maf_threshold": 0.01
    },
    "output_summary": null,
    "output_files": [],
    "error_code": "",
    "error_message": "",
    "created_at": "2026-05-17T14:30:10Z",
    "started_at": "2026-05-17T14:30:10Z",
    "finished_at": null,
    "updated_at": "2026-05-17T14:31:00Z"
  },
  "error": null,
  "request_id": "req_g3h4i5j6"
}
```

**Response 200（成功）**：
```json
{
  "success": true,
  "data": {
    "job_id": 44,
    "project_id": 3,
    "capability": "gwas_analysis",
    "status": "success",
    "progress": 100,
    "progress_stage": "完成",
    "input": { "phenotype": "Liver_PDFF", "covariates": ["age", "sex", "bmi"] },
    "output_summary": {
      "phenotype": "Liver_PDFF",
      "sample_size": 40484,
      "significant_loci_count": 18,
      "lead_snps_count": 12,
      "lambda_gc": 1.02
    },
    "output_files": [
      "gwas_summary_stats.tsv",
      "lead_snps.csv",
      "significant_loci.csv",
      "gwas_summary.json",
      "manhattan.png",
      "qq_plot.png"
    ],
    "error_code": "",
    "error_message": "",
    "created_at": "2026-05-17T14:30:10Z",
    "started_at": "2026-05-17T14:30:10Z",
    "finished_at": "2026-05-17T14:35:22Z",
    "updated_at": "2026-05-17T14:35:22Z"
  },
  "error": null,
  "request_id": "req_g3h4i5j6"
}
```

**Response 200（失败）**：
```json
{
  "success": true,
  "data": {
    "job_id": 44,
    "project_id": 3,
    "capability": "gwas_analysis",
    "status": "failed",
    "progress": 30,
    "progress_stage": "已提交执行",
    "input": { "phenotype": "Liver_PDFF" },
    "output_summary": null,
    "output_files": [],
    "error_code": "SCRIPT_EXECUTION_FAILED",
    "error_message": "GWAS 脚本退出码 1：Error: phenotype column 'Liver_PDFF' not found in phenotype file",
    "created_at": "2026-05-17T14:30:10Z",
    "started_at": "2026-05-17T14:30:10Z",
    "finished_at": "2026-05-17T14:30:12Z",
    "updated_at": "2026-05-17T14:30:12Z"
  },
  "error": null,
  "request_id": "req_g3h4i5j6"
}
```

**响应说明**：
- `status=running` 时 `output_summary` 和 `output_files` 为 `null`
- `status=success` 时 `output_summary` 包含能力特定的摘要数据
- `status=failed` 时 `error_code` + `error_message` 包含失败原因
- 前端根据 `status` 字段决定展示轮询动画/成功结果/错误信息

**错误响应**：

| Status | error.code | 场景 |
|--------|-----------|------|
| 404 | `JOB_NOT_FOUND` | jobId 不存在 |

---

### 10. GET /api/ai/jobs/{jobId}/result

| 属性 | 内容 |
|------|------|
| **作用** | 获取任务的完整分析结果（含已解析的 summary 和文件列表） |
| **对应前端页面** | `UnifiedResultView` |
| **对应 Adapter** | 无（查询 `analysis_results` 表） |

**Response 200（GWAS 结果示例）**：
```json
{
  "success": true,
  "data": {
    "job_id": 44,
    "project_id": 3,
    "capability": "gwas_analysis",
    "result": {
      "phenotype": "Liver_PDFF",
      "sample_size": 40484,
      "significant_loci_count": 18,
      "lead_snps_count": 12,
      "lambda_gc": 1.02,
      "significant_loci": [
        {
          "locus_id": 1,
          "chr": 3,
          "start": 100000,
          "end": 200000,
          "lead_snp": "rs1001",
          "n_snps": 50,
          "min_pvalue": 1.2e-10
        }
      ],
      "lead_snps": [
        {
          "snp": "rs1001",
          "chr": 3,
          "bp": 123456,
          "ea": "A",
          "oa": "G",
          "beta": 0.053,
          "se": 0.008,
          "p_value": 1.2e-10
        }
      ]
    },
    "output_files": [
      {
        "name": "gwas_summary_stats.tsv",
        "path": "storage/projects/3/outputs/gwas/gwas_summary_stats.tsv",
        "size": 2456789,
        "mime_type": "text/tab-separated-values"
      },
      {
        "name": "lead_snps.csv",
        "path": "storage/projects/3/outputs/gwas/lead_snps.csv",
        "size": 2048,
        "mime_type": "text/csv"
      },
      {
        "name": "manhattan.png",
        "path": "storage/projects/3/outputs/gwas/manhattan.png",
        "size": 345678,
        "mime_type": "image/png"
      }
    ],
    "created_at": "2026-05-17T14:35:22Z"
  },
  "error": null,
  "request_id": "req_k7l8m9n0"
}
```

**Response 200（MR 结果示例）**：
```json
{
  "success": true,
  "data": {
    "job_id": 45,
    "project_id": 3,
    "capability": "mendelian_randomization",
    "result": {
      "exposure": "Liver_PDFF",
      "outcome": "Osteoporosis",
      "estimates": [
        { "method": "IVW", "beta": 0.38, "se": 0.09, "or": 1.46, "ci_lower": 1.21, "ci_upper": 1.76, "p_value": 0.0004 },
        { "method": "MR-Egger", "beta": 0.42, "se": 0.23, "or": 1.52, "ci_lower": 0.96, "ci_upper": 2.41, "p_value": 0.072 },
        { "method": "Weighted Median", "beta": 0.34, "se": 0.10, "or": 1.40, "ci_lower": 1.15, "ci_upper": 1.71, "p_value": 0.0018 },
        { "method": "Weighted Mode", "beta": 0.36, "se": 0.11, "or": 1.43, "ci_lower": 1.16, "ci_upper": 1.77, "p_value": 0.009 }
      ],
      "heterogeneity": [{ "method": "IVW", "q_statistic": 15.2, "q_df": 10, "q_pval": 0.12 }],
      "pleiotropy": { "egger_intercept": 0.002, "se": 0.004, "pval": 0.62 },
      "primary_method": "IVW",
      "primary_beta": 0.38,
      "primary_or": 1.46,
      "primary_ci_lower": 1.21,
      "primary_ci_upper": 1.76,
      "primary_p_value": 0.0004
    },
    "output_files": [...],
    "created_at": "2026-05-17T14:36:00Z"
  },
  "error": null,
  "request_id": "req_o1p2q3r4"
}
```

**错误响应**：

| Status | error.code | 场景 |
|--------|-----------|------|
| 404 | `JOB_NOT_FOUND` | jobId 不存在 |
| 404 | `RESULT_NOT_FOUND` | 任务未完成，结果尚未生成 |
| 500 | `OUTPUT_JSON_INVALID` | 结果 JSON 解析失败 |

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "RESULT_NOT_FOUND",
    "message": "任务 44 尚未完成（当前状态：running），结果不可用",
    "details": { "job_id": 44, "current_status": "running" }
  },
  "request_id": "req_s5t6u7v8"
}
```

---

### 11. POST /api/ai/jobs/{jobId}/cancel

| 属性 | 内容 |
|------|------|
| **作用** | 取消正在执行或等待中的任务 |
| **对应前端页面** | `TaskCard`（取消按钮） |
| **对应 Adapter** | 无（`TaskOrchestrator` 直接更新状态） |

**限制**：
- 仅 `pending` 和 `running` 状态可取消
- 终态任务（`success`/`failed`/`cancelled`）返回 409

**Response 200**：
```json
{
  "success": true,
  "data": {
    "job_id": 44,
    "project_id": 3,
    "capability": "gwas_analysis",
    "status": "cancelled",
    "progress": 30,
    "progress_stage": "已取消",
    "error_code": "",
    "error_message": "用户手动取消",
    "finished_at": "2026-05-17T14:31:00Z",
    "updated_at": "2026-05-17T14:31:00Z"
  },
  "error": null,
  "request_id": "req_w9x0y1z2"
}
```

**错误响应**：

| Status | error.code | 场景 |
|--------|-----------|------|
| 404 | `JOB_NOT_FOUND` | jobId 不存在 |
| 409 | `JOB_ALREADY_CANCELLED` | 任务已经处于终态 |

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "JOB_ALREADY_CANCELLED",
    "message": "任务 44 已处于终态（success），无法取消",
    "details": { "job_id": 44, "current_status": "success" }
  },
  "request_id": "req_a3b4c5d6"
}
```

---

## 接口 → 页面 → Adapter 映射表

| # | 接口 | 前端触发点 | Store 方法 | AI Adapter |
|---|------|-----------|-----------|-----------|
| 1 | `POST /api/files/upload` | ImageProcessingModule 上传区 | — (aiService) | `StorageService` |
| 2 | `POST /api/ai/segmentation/jobs` | "保存并继续分析" | `createSegmentationJob()` | `image_segmentation/` |
| 3 | `POST /api/ai/phenotype/jobs` | C1 成功后自动 | `createPhenotypeJob()` | `phenotype_quantification/` |
| 4 | `POST /api/ai/gwas/jobs` | GWASModule → "运行" | `createGWASJob()` | `gwas_analysis/` |
| 5 | `POST /api/ai/mr/jobs` | MRModule → "运行" | `createMRJob()` | `two_sample_mr/` |
| 6 | `POST /api/ai/mediation-mr/jobs` | MediationMRModule → "运行中介 MR" | `createMediationMRJob()` | `mediation_mr/` |
| 7 | `POST /api/ai/risk-modeling/jobs` | TaskCard / Pipeline 自动 | `createRiskModelingJob()` | `risk_modeling/` |
| 8 | `POST /api/ai/report/jobs` | "生成分析报告" 按钮 | `createReportJob()` | `report_generation/` |
| 9 | `GET /api/ai/jobs/{jobId}` | startPolling 轮询 | `getJobStatus()` | — (DB query) |
| 10 | `GET /api/ai/jobs/{jobId}/result` | "查看结果" 按钮 | `getJobResult()` | — (DB query) |
| 11 | `POST /api/ai/jobs/{jobId}/cancel` | TaskCard → "取消" | `cancelJob()` | — (status update) |

---

## 附录 A：与现有 /api/v1 路径的关系

| 新路径（本文档） | 现有路径（/api/v1） | 关系 |
|------------------|---------------------|------|
| `POST /api/files/upload` | `POST /api/v1/projects/{id}/files` | 新独立路径，project_id 在 body 中 |
| `POST /api/ai/*/jobs` | `POST /api/v1/tasks` | 新路径按能力分组，旧路径用 task_type 参数 |
| `GET /api/ai/jobs/{id}` | `GET /api/v1/tasks/{id}` | 功能等价 |
| `GET /api/ai/jobs/{id}/result` | `GET /api/v1/tasks/{id}/result` | 功能等价 |
| `POST /api/ai/jobs/{id}/cancel` | 无 | 全新能力 |

> **共存策略**：新 `/api/ai/` 路径与旧 `/api/v1/` 路径并存。旧前端继续用 v1，新 AI Service 使用新路径。后端 FastAPI router 新增 `api/ai_router.py` 承载 `/api/ai/*` 端点。

## 附录 B：进度阶段与 progress 值的对应关系

| progress | stage | 说明 |
|----------|-------|------|
| 0 | 初始化 | 任务已创建，等待执行 |
| 10 | 校验输入 | 参数验证、依赖检查 |
| 20 | 构建执行命令 | 创建 CLI/HTTP 请求 |
| 30 | 已提交执行 | 子进程/外部调用已启动 |
| 50 | 处理中 | 中间文件已生成 |
| 70 | 解析结果 | 外部调用完成，解析输出 |
| 90 | 持久化结果 | 写入 DB + Storage |
| 100 | 完成 | 全部完成 |

## 附录 C：版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v0.3.0-draft | 2026-05-17 | 初始契约，11 个 AI 端点定义 |
