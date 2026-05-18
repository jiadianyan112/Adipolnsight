"""
AdipoInsight 全局配置

所有配置通过环境变量注入，默认值适合本地开发。
生产部署时通过 .env 文件或环境变量覆盖。
"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(
    Path(__file__).resolve().parent.parent.parent / ".env",
    override=False,
)

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# ===== 路径 =====

STORAGE_DIR = BASE_DIR / os.getenv("STORAGE_DIR", "storage")
MOCK_DATA_DIR = BASE_DIR / os.getenv("AI_MOCK_DATA_DIR", "mock_data")
ANALYSIS_SCRIPTS_DIR = BASE_DIR / os.getenv("AI_SCRIPTS_DIR", "analysis_scripts")
UPLOAD_DIR = Path(os.getenv("AI_UPLOAD_DIR", STORAGE_DIR / "uploads"))
RESULT_DIR = Path(os.getenv("AI_RESULT_DIR", STORAGE_DIR / "results"))
JOB_STORAGE_PATH = Path(os.getenv("AI_JOB_STORAGE_PATH", STORAGE_DIR / "jobs"))
LOG_DIR = BASE_DIR / os.getenv("LOG_DIR", "logs")

# ===== 数据库 =====

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"sqlite+aiosqlite:///{BASE_DIR}/adipoinsight.db",
)
SYNC_DATABASE_URL = (
    DATABASE_URL.replace("+aiosqlite", "")
    .replace("sqlite+aiosqlite", "sqlite")
)

# ===== AI 模式 =====

AI_MODE = os.getenv("AI_MODE", "mock")  # mock | script | api | model

# 各能力单独模式覆盖: "image_segmentation=model,gwas_analysis=script"
AI_MODE_PER_SKILL_RAW = os.getenv("AI_MODE_PER_SKILL", "")
AI_MODE_PER_SKILL: dict[str, str] = {}
if AI_MODE_PER_SKILL_RAW:
    for pair in AI_MODE_PER_SKILL_RAW.split(","):
        pair = pair.strip()
        if "=" in pair:
            k, v = pair.split("=", 1)
            AI_MODE_PER_SKILL[k.strip()] = v.strip()

def get_skill_mode(capability_type: str) -> str:
    """获取指定能力的运行模式"""
    return AI_MODE_PER_SKILL.get(capability_type, AI_MODE)

# ===== Job 存储 =====

AI_JOB_STORAGE = os.getenv("AI_JOB_STORAGE", "memory")  # memory | file | db

# ===== 上传限制 =====

MAX_UPLOAD_SIZE = int(os.getenv("MAX_UPLOAD_SIZE", str(200 * 1024 * 1024)))  # 200 MB

ALLOWED_IMAGE_FORMATS = os.getenv(
    "ALLOWED_IMAGE_FORMATS",
    ".nii,.nii.gz,.dcm,.dicom,.zip,.nrrd",
).split(",")

ALLOWED_DATA_FORMATS = os.getenv(
    "ALLOWED_DATA_FORMATS",
    ".csv,.tsv,.vcf,.vcf.gz,.bed,.bim,.fam",
).split(",")

# ===== LLM 配置 =====

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "mock")        # mock | deepseek | openai

# DeepSeek
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash")
DEEPSEEK_REASONING_MODEL = os.getenv("DEEPSEEK_REASONING_MODEL", "deepseek-v4-pro")
DEEPSEEK_ENABLE_THINKING = os.getenv("DEEPSEEK_ENABLE_THINKING", "false").lower() == "true"
DEEPSEEK_REASONING_EFFORT = os.getenv("DEEPSEEK_REASONING_EFFORT", "high")  # high | medium | low

# 通用 LLM 参数
LLM_TIMEOUT_MS = int(os.getenv("LLM_TIMEOUT_MS", "60000"))
LLM_MAX_RETRIES = int(os.getenv("LLM_MAX_RETRIES", "2"))
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "4096"))
LLM_JSON_TEMPERATURE = float(os.getenv("LLM_JSON_TEMPERATURE", "0.2"))
LLM_TEXT_TEMPERATURE = float(os.getenv("LLM_TEXT_TEMPERATURE", "0.4"))

# 兼容旧命名
LLM_API_KEY = os.getenv("LLM_API_KEY", "") or DEEPSEEK_API_KEY
LLM_API_BASE = os.getenv("LLM_API_BASE", "") or DEEPSEEK_BASE_URL
LLM_MODEL = os.getenv("LLM_MODEL", "") or DEEPSEEK_MODEL
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
LLM_LOCAL_URL = os.getenv("LLM_LOCAL_URL", "")

# 前端环境变量白名单（只有这些变量可以暴露到前端）
# DEEPSEEK_API_KEY 绝不在此列表中
FRONTEND_ENV_WHITELIST = {"AI_MODE", "API_PORT", "FRONTEND_PORT"}

# ===== 外部数据 API（预留） =====

OPENGWAS_API_BASE = os.getenv(
    "OPENGWAS_API_BASE",
    "https://gwas-api.mrcieu.ac.uk",
)
GWAS_CATALOG_API_BASE = os.getenv(
    "GWAS_CATALOG_API_BASE",
    "https://www.ebi.ac.uk/gwas/api",
)
DECODE_PQTL_PATH = os.getenv("DECODE_PQTL_PATH", "")

# ===== 脚本路径（预留） =====

PYTHON_SCRIPT_PATH = os.getenv("PYTHON_SCRIPT_PATH", "python")
RSCRIPT_PATH = os.getenv("RSCRIPT_PATH", "Rscript")

# ===== 服务器 =====

API_PORT = int(os.getenv("API_PORT", "8000"))
FRONTEND_PORT = int(os.getenv("FRONTEND_PORT", "5173"))
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")

# ===== 任务 =====

TASK_TIMEOUT_SECONDS = int(os.getenv("TASK_TIMEOUT_SECONDS", "300"))

# ===== 日志 =====

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", str(LOG_DIR / "adipoinsight.log"))

# 确保必要目录存在
for d in [STORAGE_DIR, UPLOAD_DIR, RESULT_DIR, JOB_STORAGE_PATH, LOG_DIR]:
    d.mkdir(parents=True, exist_ok=True)
