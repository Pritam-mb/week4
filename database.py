"""
database.py -- SQLAlchemy async models for Graveyard of Dead Software
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Text, Integer, DateTime, Boolean, Float
from datetime import datetime
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

_raw_db_url = os.getenv("DATABASE_URL")
if not _raw_db_url or not _raw_db_url.strip():
    DATABASE_URL = f"sqlite+aiosqlite:///{Path(__file__).parent.resolve() / 'graveyard.db'}"
elif _raw_db_url.startswith("sqlite://"):
    DATABASE_URL = _raw_db_url.replace("sqlite://", "sqlite+aiosqlite://", 1)
else:
    DATABASE_URL = _raw_db_url

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


class Base(DeclarativeBase):
    pass


class Grave(Base):
    __tablename__ = "graves"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(500))
    url: Mapped[str] = mapped_column(String(2000))

    # Wayback dates
    first_archived: Mapped[str | None] = mapped_column(String(50), nullable=True)
    last_seen_alive: Mapped[str | None] = mapped_column(String(50), nullable=True)
    archive_url: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    first_archive_url: Mapped[str | None] = mapped_column(String(2000), nullable=True)

    # Lifeline chart data -- JSON string: {"2009": 12, "2010": 12, ...}
    lifeline_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Browserbase
    screenshot_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    replay_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    extracted_fields_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Exhumer walk-back attempts log -- JSON list of attempt dicts
    exhume_attempts: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Gemma-generated
    epitaph: Mapped[str | None] = mapped_column(String(500), nullable=True)
    eulogy: Mapped[str | None] = mapped_column(Text, nullable=True)
    cause_of_death: Mapped[str | None] = mapped_column(String(300), nullable=True)
    cause_label: Mapped[str | None] = mapped_column(String(100), nullable=True)
    cause_evidence: Mapped[str | None] = mapped_column(Text, nullable=True)
    cause_is_rumored: Mapped[bool] = mapped_column(Boolean, default=True)
    survived_by: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Fact-checker output
    eulogy_verified: Mapped[str | None] = mapped_column(Text, nullable=True)
    claims_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    unsupported_before: Mapped[int | None] = mapped_column(Integer, nullable=True)
    unsupported_after: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Visitor memories -- JSON list of {"text":..., "ts":...}
    memories_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Meta
    marigolds: Mapped[int] = mapped_column(Integer, default=0)
    is_seed: Mapped[bool] = mapped_column(Boolean, default=False)
    llm_provider: Mapped[str | None] = mapped_column(String(50), nullable=True)
    llm_model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    dig_status: Mapped[str] = mapped_column(String(50), default="done")


class DigJob(Base):
    __tablename__ = "dig_jobs"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    url: Mapped[str] = mapped_column(String(2000))
    status: Mapped[str] = mapped_column(String(50), default="pending")
    message: Mapped[str] = mapped_column(String(500), default="Queued...")
    grave_slug: Mapped[str | None] = mapped_column(String(200), nullable=True)
    error: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    stage: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class BenchmarkResult(Base):
    """Stores Eval A results -- HTTP vs Browserbase comparison."""
    __tablename__ = "benchmark_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    url: Mapped[str] = mapped_column(String(2000))
    site_type: Mapped[str] = mapped_column(String(50), default="unknown")
    path: Mapped[str] = mapped_column(String(50))
    usable: Mapped[bool] = mapped_column(Boolean, default=False)
    chars: Mapped[int] = mapped_column(Integer, default=0)
    secs: Mapped[float | None] = mapped_column(Float, nullable=True)
    fields_filled: Mapped[int] = mapped_column(Integer, default=0)
    era: Mapped[str | None] = mapped_column(String(50), nullable=True)
    error: Mapped[str | None] = mapped_column(String(500), nullable=True)
    run_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        def _migrate(connection):
            from sqlalchemy import text
            res = connection.execute(text('PRAGMA table_info(graves)')).fetchall()
            cols = {r[1] for r in res}
            if 'extracted_fields_json' not in cols:
                connection.execute(text('ALTER TABLE graves ADD COLUMN extracted_fields_json TEXT'))
            if 'llm_provider' not in cols:
                connection.execute(text('ALTER TABLE graves ADD COLUMN llm_provider VARCHAR(50)'))
            if 'llm_model' not in cols:
                connection.execute(text('ALTER TABLE graves ADD COLUMN llm_model VARCHAR(100)'))

            res_jobs = connection.execute(text('PRAGMA table_info(dig_jobs)')).fetchall()
            cols_jobs = {r[1] for r in res_jobs}
            if 'stage' not in cols_jobs:
                connection.execute(text('ALTER TABLE dig_jobs ADD COLUMN stage VARCHAR(50)'))

            res_bench = connection.execute(text('PRAGMA table_info(benchmark_results)')).fetchall()
            cols_bench = {r[1] for r in res_bench}
            if 'fields_filled' not in cols_bench:
                connection.execute(text('ALTER TABLE benchmark_results ADD COLUMN fields_filled INTEGER DEFAULT 0'))
            if 'era' not in cols_bench:
                connection.execute(text('ALTER TABLE benchmark_results ADD COLUMN era VARCHAR(50)'))

        await conn.run_sync(_migrate)


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
