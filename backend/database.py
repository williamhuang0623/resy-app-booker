from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from config import settings

# Render provides DATABASE_URL as postgres:// — SQLAlchemy 2.x requires postgresql://
_url = settings.database_url.replace("postgres://", "postgresql://", 1)

engine = create_engine(_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
