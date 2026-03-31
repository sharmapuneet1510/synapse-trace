"""Synapse Trace — Database layer.

Default: SQLite (development).
Production: set DATABASE_URL env var to a MSSQL connection string:

    # SQL Server / Azure SQL via pyodbc
    DATABASE_URL=mssql+pyodbc://user:pass@server/db?driver=ODBC+Driver+18+for+SQL+Server

    # SQL Server via pymssql
    DATABASE_URL=mssql+pymssql://user:pass@server/db

The engine is created once at module import; call init_db() at startup to
ensure all tables exist.
"""
from __future__ import annotations

import logging
import os

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, declarative_base

logger = logging.getLogger(__name__)

DATABASE_URL: str = os.environ.get(
    "DATABASE_URL",
    "sqlite:///./synapse_trace.db",
)

_is_sqlite = DATABASE_URL.startswith("sqlite")
_is_mssql  = "mssql" in DATABASE_URL

logger.info("Database URL scheme: %s", DATABASE_URL.split("://")[0])

# ── Engine creation ───────────────────────────────────────────────────────────

if _is_sqlite:
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=False,
    )
    # Enable WAL mode for better concurrent read performance
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_conn, _rec):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

elif _is_mssql:
    engine = create_engine(
        DATABASE_URL,
        fast_executemany=True,   # pyodbc bulk-insert optimisation
        echo=False,
        pool_pre_ping=True,      # detect stale connections
        pool_size=10,
        max_overflow=20,
        pool_timeout=30,
        pool_recycle=1800,       # recycle connections every 30 min
    )
else:
    # Generic (PostgreSQL, MySQL, etc.)
    engine = create_engine(
        DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ── Session dependency (FastAPI) ──────────────────────────────────────────────

def get_db():
    """Yield a SQLAlchemy session; ensures close on exit."""
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# ── Startup ───────────────────────────────────────────────────────────────────

def init_db() -> None:
    """Create all tables if they do not exist.

    Called once at application startup.  Safe to call multiple times.
    """
    logger.info("init_db: creating tables if missing (engine=%s)", DATABASE_URL.split("://")[0])
    Base.metadata.create_all(bind=engine)
    # Verify connectivity
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    logger.info("init_db: database ready")
