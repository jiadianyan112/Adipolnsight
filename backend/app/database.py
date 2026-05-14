from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from backend.app.config import SYNC_DATABASE_URL

engine = create_engine(SYNC_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    from backend.app.models import project, sample, file_asset, analysis_task, analysis_result, report, audit_log  # noqa
    Base.metadata.create_all(bind=engine)
