"""
AdipoInsight AI 能力 Pydantic Schema 定义

与前端 types/ 目录中 TypeScript 类型保持一一对应。
所有 schema 均可被 API 路由和 Adapter 层复用。
"""

from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field


# ===== AI 能力类型枚举 =====

AI_CAPABILITY_TYPE = Literal[
    "image_segmentation",
    "phenotype_quantification",
    "gwas_analysis",
    "opengwas_fetch",
    "mendelian_randomization",
    "mediation_mr",
    "risk_modeling",
    "report_generation",
    "result_interpretation",
]

AI_JOB_STATUS = Literal["pending", "running", "success", "failed", "cancelled"]

AI_JOB_ERROR_CODE = Literal[
    "ADAPTER_NOT_FOUND",
    "INVALID_INPUT",
    "SCRIPT_NOT_FOUND",
    "SCRIPT_EXECUTION_FAILED",
    "OUTPUT_JSON_INVALID",
    "OUTPUT_FILE_MISSING",
    "TASK_TIMEOUT",
    "FILE_NOT_FOUND",
    "DATABASE_ERROR",
    "UPSTREAM_DEPENDENCY_FAILED",
    "UNKNOWN_ERROR",
]

ADAPTER_MODE = Literal["mock", "real", "hybrid"]

FILE_TYPE = Literal["mri", "phenotype", "covariates", "genotype"]

SEGMENTATION_TARGET = Literal[
    "liver", "visceral_fat", "subcutaneous_fat", "bone_marrow",
    "pancreas", "kidney", "muscle",
]

MR_METHOD = Literal["IVW", "MR-Egger", "Weighted Median", "Weighted Mode"]

MEDIATOR_SOURCE = Literal["decode_plasma", "metabolite_gwas", "gwas_catalog", "custom"]

RISK_LEVEL = Literal["Low", "Medium", "High"]


# ===== 文件上传 =====

class UploadedFileResponse(BaseModel):
    id: int
    project_id: int
    file_name: str
    file_type: FILE_TYPE
    file_path: str
    file_size: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ===== 影像分割 C1 =====

class SegmentationRequest(BaseModel):
    project_id: int
    file_id: int
    target_structures: list[SEGMENTATION_TARGET] = ["liver", "visceral_fat", "subcutaneous_fat", "bone_marrow"]


class DiceScores(BaseModel):
    """各解剖结构 DICE 相似系数 (0-1)"""
    liver: float
    pancreas: float
    visceral_fat: float
    subcutaneous_fat: float
    bone_marrow: float


class VolumeMetrics(BaseModel):
    """体积与定量指标（贴合 MRI 身体成分分析场景）"""
    liver_volume_cm3: float
    visceral_fat_volume_cm3: float
    subcutaneous_fat_volume_cm3: float
    pancreatic_fat_fraction_pct: float
    liver_pdff_pct: float
    bone_marrow_fat_fraction_pct: float
    muscle_volume_L: float
    sat_vat_ratio: float
    total_body_fat_pct: float
    bone_density_g_cm3: float


class QualityControl(BaseModel):
    """分割质量评估"""
    status: Literal["passed", "warning", "failed"]
    overall_quality_score: float = Field(ge=0, le=1)
    motion_artifact_detected: bool
    field_inhomogeneity_score: float
    snr_estimate_db: float
    coverage_completeness: float = Field(ge=0, le=1)


class SegmentationResult(BaseModel):
    """完整的 AI 分割输出"""
    segmentation_id: str
    model_name: str
    model_version: str
    target_regions: list[str]
    dice_scores: DiceScores
    volume_metrics: VolumeMetrics
    quality_control: QualityControl
    mask_preview_url: str = ""
    overlay_preview_url: str = ""
    warnings: list[str] = []


class SegmentationOutputFiles(BaseModel):
    segmentation_metrics_json: str
    fat_quantification_csv: str
    overlay_preview_png: str


# ===== 脂肪表型量化 C2 =====

class PhenotypeSummary(BaseModel):
    liver_pdff: float
    visceral_fat_volume: float
    subcutaneous_fat_volume: float
    bone_marrow_fat_fraction: float
    total_body_fat_pct: float
    muscle_volume: float
    sat_vat_ratio: float
    bone_density: float


class PhenotypeQuantificationResult(PhenotypeSummary):
    qc_status: Literal["passed", "warning", "failed"]


# ===== GWAS 分析 C3 =====

class GWASAnalysisRequest(BaseModel):
    project_id: int
    phenotype: str
    covariates: list[str] = []
    maf_threshold: float = 0.01
    hwe_threshold: float = 1e-6


class GWASSummary(BaseModel):
    phenotype: str
    sample_size: int
    significant_loci_count: int
    lead_snps_count: int
    lambda_gc: float


class GWASSignificantLocus(BaseModel):
    locus_id: int
    chr: int
    start: int
    end: int
    lead_snp: str
    n_snps: int
    min_pvalue: float


class GWASLeadSNP(BaseModel):
    snp: str
    chr: int
    bp: int
    ea: str
    oa: str
    beta: float
    se: float
    p_value: float


class GWASAnalysisResult(GWASSummary):
    significant_loci: list[GWASSignificantLocus]
    lead_snps: list[GWASLeadSNP]


# ===== OpenGWAS 数据获取 =====

class OpenGWASFetchRequest(BaseModel):
    project_id: int
    outcome_id: str


class OpenGWASFetchResult(BaseModel):
    outcome_id: str
    outcome_name: str
    matched_snps: int
    proxy_snps_used: int
    source: str


# ===== 双样本 MR C4 =====

class MRAnalysisRequest(BaseModel):
    project_id: int
    exposure: str
    outcome: str
    clump_r2: float = 0.001
    clump_kb: int = 10000
    p_threshold: float = 5e-8
    methods: list[MR_METHOD] = ["IVW", "MR-Egger", "Weighted Median", "Weighted Mode"]


class MREstimate(BaseModel):
    method: MR_METHOD
    beta: float
    se: float
    or_: float = Field(alias="or")
    ci_lower: float
    ci_upper: float
    p_value: float

    model_config = {"populate_by_name": True}


class MRHeterogeneity(BaseModel):
    method: str
    q_statistic: float
    q_df: int
    q_pval: float


class MRPleiotropy(BaseModel):
    egger_intercept: float
    se: float
    pval: float


class MRAnalysisResult(BaseModel):
    exposure: str
    outcome: str
    estimates: list[MREstimate]
    heterogeneity: list[MRHeterogeneity]
    pleiotropy: MRPleiotropy
    primary_method: MR_METHOD
    primary_beta: float
    primary_or: float
    primary_ci_lower: float
    primary_ci_upper: float
    primary_p_value: float


# ===== 中介 MR C5 =====

class MediationMRRequest(BaseModel):
    project_id: int
    exposure: str
    outcome: str
    mediator_source: MEDIATOR_SOURCE
    correction_method: Literal["bonferroni", "fdr", "none"] = "fdr"
    alpha: float = 0.05


class MediatorProteinResult(BaseModel):
    protein: str
    beta_a: float
    beta_b: float
    indirect_effect: float
    se: float
    proportion_mediated: float
    p_mediation: float
    significant: bool


class MediationMRResult(BaseModel):
    exposure: str
    outcome: str
    mediator_source: MEDIATOR_SOURCE
    tested_proteins: int
    significant_mediators: int
    top_mediators: list[MediatorProteinResult]
    total_indirect_effect: float
    total_direct_effect: float
    total_effect: float
    total_effect_pvalue: float


# ===== 风险建模 C6 =====

class RiskModelingRequest(BaseModel):
    project_id: int
    exposure: str
    outcome: str
    grouping: Literal["quartile", "tertile", "median"] = "quartile"
    covariates: list[str] = []


class OLSResult(BaseModel):
    model: str
    beta: float
    se: float
    p_value: float


class RCSKnot(BaseModel):
    knot: int
    estimate: float
    se: float
    p_value: float


class RiskModelingResult(BaseModel):
    exposure: str
    outcome: str
    grouping: str
    reference_group: str
    pdff_quartile: str
    osteopenia_aor: float
    osteoporosis_aor: float
    risk_level: RISK_LEVEL
    model_type: str
    ols_results: list[OLSResult]
    rcs_results: list[RCSKnot]
    auc: float


# ===== 报告生成 C7 =====

REPORT_TYPE = Literal["summary", "full", "competition"]
REPORT_MODULE = Literal[
    "segmentation", "phenotype", "gwas", "mr", "mediation_mr",
    "risk_modeling", "discussion", "limitations", "methods", "references",
]
REPORT_LANGUAGE = Literal["zh-CN", "en"]
EXPORT_FORMAT_TYPE = Literal["pdf", "docx", "html", "markdown", "latex"]
FIGURE_TYPE = Literal[
    "manhattan", "scatter", "forest", "rcs_curve", "qq_plot",
    "heatmap", "bar_chart", "segmentation_overlay", "mechanism_diagram", "other",
]
REFERENCE_TYPE = Literal["gwas_catalog", "opengwas", "published_paper", "database", "method", "other"]


class ReportGenerationRequest(BaseModel):
    project_id: int
    project_title: str = ""
    selected_jobs: list[str] = []
    selected_modules: list[REPORT_MODULE] = []
    report_type: REPORT_TYPE = "full"
    language: REPORT_LANGUAGE = "zh-CN"
    template: str = ""
    include_figures: bool = True
    include_tables: bool = True
    include_ai_interpretation: bool = True
    custom_notes: str = ""


class TableColumn(BaseModel):
    key: str
    label: str
    align: Literal["left", "center", "right"] = "left"
    format: Literal["number", "scientific", "percentage", "text"] = "text"
    precision: int = 2


class ReportSection(BaseModel):
    number: int
    title: str
    content: str
    status: Literal["complete", "pending", "skipped"]
    summary: str = ""
    evidence_job_ids: list[str] = []
    related_figures: list[dict] = []
    related_tables: list[dict] = []


class ReportFigure(BaseModel):
    figure_id: str
    number: int
    caption: str
    url: str
    type: FIGURE_TYPE
    section_number: int
    alt_text: str
    source_job_id: str
    dimensions: Optional[dict] = None


class ReportTable(BaseModel):
    table_id: str
    number: int
    caption: str
    columns: list[TableColumn]
    rows: list[dict]
    section_number: int
    source_job_id: str
    footnotes: list[str] = []


class ReportReference(BaseModel):
    ref_id: str
    number: int
    text: str
    doi: str = ""
    type: REFERENCE_TYPE
    cited_in_sections: list[int] = []


class ExportFormat(BaseModel):
    format: EXPORT_FORMAT_TYPE
    label: str
    available: bool
    url: str
    file_size: int = 0


class ReportMetadata(BaseModel):
    version: str
    generated_at: str
    generation_time_seconds: float
    ai_model: str
    data_sources: list[str] = []
    analysis_methods: list[str] = []
    conflict_of_interest: str = ""
    acknowledgments: str = ""


class ReportGenerationResult(BaseModel):
    report_id: str
    project_id: int
    title: str
    subtitle: str = ""
    report_type: REPORT_TYPE = "full"
    language: REPORT_LANGUAGE = "zh-CN"
    sections: list[ReportSection] = []
    figures: list[ReportFigure] = []
    tables: list[ReportTable] = []
    references: list[ReportReference] = []
    limitations: list[str] = []
    key_findings: list[str] = []
    export_formats: list[ExportFormat] = []
    metadata: Optional[ReportMetadata] = None
    content_markdown: str = ""
    completed_sections: int = 0
    total_sections: int = 0
    ai_interpretation: str = ""
    output_files: list[str] = []


# ===== 通用 Job Schema =====

class AIJobCreateRequest(BaseModel):
    project_id: int
    task_type: AI_CAPABILITY_TYPE
    parameters: dict = {}


class AIJobProgress(BaseModel):
    percent: int = Field(ge=0, le=100)
    stage: str
    stage_started_at: Optional[datetime] = None


class AIJobResponse(BaseModel):
    id: int
    project_id: int
    task_type: AI_CAPABILITY_TYPE
    task_name: str
    status: AI_JOB_STATUS
    progress: int
    input_json: str
    output_json: str
    error_code: str
    error_message: str
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AIJobListResponse(BaseModel):
    jobs: list[AIJobResponse]
    total: int


# ===== AI Job API Schemas =====

# URL path capability → 内部 task_type 映射
URL_CAPABILITY_MAP: dict[str, str] = {
    "segmentation": "image_segmentation",
    "phenotype": "phenotype_quantification",
    "gwas": "gwas_analysis",
    "mr": "mendelian_randomization",
    "mediation-mr": "mediation_mr",
    "risk-modeling": "risk_modeling",
    "report": "report_generation",
    "interpretation": "result_interpretation",
}

VALID_URL_CAPABILITIES = Literal[
    "segmentation", "phenotype", "gwas", "mr",
    "mediation-mr", "risk-modeling", "report",
    "interpretation",
]


class CreateJobRequest(BaseModel):
    """POST /api/ai/{capability}/jobs 请求体"""
    project_id: int = Field(..., ge=1, description="项目 ID")
    parameters: dict = Field(default_factory=dict, description="能力特定参数")


class JobStatusResponse(BaseModel):
    """GET /api/ai/jobs/{jobId} 响应 data 字段"""
    job_id: str
    capability_type: str
    status: str
    progress: int
    progress_stage: str
    input: dict
    result: Optional[dict] = None
    output_files: list[str] = []
    error_code: str = ""
    error_message: str = ""
    created_at: str
    started_at: str = ""
    finished_at: str = ""
    updated_at: str
    project_id: int = 0


class JobResultResponse(BaseModel):
    """GET /api/ai/jobs/{jobId}/result 响应 data 字段"""
    job_id: str
    capability_type: str
    status: str
    result: Optional[dict] = None
    output_files: list[str] = []
    created_at: str
    finished_at: str = ""


class CancelJobResponse(BaseModel):
    """POST /api/ai/jobs/{jobId}/cancel 响应 data 字段"""
    job_id: str
    capability_type: str
    status: str
    message: str


# ===== 统一 API Response Envelope =====

class ApiError(BaseModel):
    code: str
    message: str
    details: Optional[dict] = None


class ApiResponse(BaseModel):
    success: bool
    data: Optional[dict] = None
    error: Optional[ApiError] = None
    request_id: str = ""


# ===== Adapter 配置 =====

class AdapterModeConfig(BaseModel):
    """各能力适配器模式配置"""
    global_mode: ADAPTER_MODE = "mock"
    per_skill_overrides: dict[str, ADAPTER_MODE] = {}
