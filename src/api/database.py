"""Synapse Trace — Database layer (SQLite, swappable to MSSQL)."""
from __future__ import annotations

import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

logger = logging.getLogger(__name__)

DATABASE_URL = "sqlite:///./synapse_trace.db"

logger.debug("Connecting to database: %s", DATABASE_URL)
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    logger.info("Running Base.metadata.create_all — ensuring tables exist")
    Base.metadata.create_all(bind=engine)
    logger.debug("Database schema ready")
