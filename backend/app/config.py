import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
STORAGE_DIR = BASE_DIR / "storage"
MOCK_DATA_DIR = BASE_DIR / "mock_data"
ANALYSIS_SCRIPTS_DIR = BASE_DIR / "analysis_scripts"
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite+aiosqlite:///{BASE_DIR}/adipoinsight.db")
SYNC_DATABASE_URL = DATABASE_URL.replace("+aiosqlite", "").replace("sqlite+aiosqlite", "sqlite")
