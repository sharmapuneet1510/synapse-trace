"""Synapse Trace API — FastAPI application."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import CORS_ORIGINS, JURISDICTION_JSON
from .database import init_db
from .logging_config import setup_logging
from .routers import chat, dashboard, fields, jurisdictions, lineage, llm, parse, trace, translation, xpath
from .services import jurisdiction_service

# Configure logging before anything else so all module-level loggers inherit it
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ──────────────────────────────────────────────────────────────
    logger.info("Synapse Trace API starting up")
    try:
        init_db()
        logger.info("Database initialised successfully")
    except Exception:
        logger.exception("Failed to initialise database — aborting startup")
        raise

    try:
        jur_list = jurisdiction_service.load_config(JURISDICTION_JSON)
        logger.info(
            "Loaded %d jurisdiction(s) from %s: %s",
            len(jur_list),
            JURISDICTION_JSON,
            [j.id for j in jur_list],
        )
    except Exception:
        logger.exception("Failed to load jurisdiction config from %s", JURISDICTION_JSON)
        raise

    yield

    # ── Shutdown ─────────────────────────────────────────────────────────────
    logger.info("Synapse Trace API shutting down")


app = FastAPI(
    title="Synapse Trace",
    description="Data lineage tracer for regulatory reporting",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(jurisdictions.router)
app.include_router(fields.router)
app.include_router(xpath.router)
app.include_router(translation.router)
app.include_router(parse.router)
app.include_router(dashboard.router)
app.include_router(chat.router)
app.include_router(llm.router)
app.include_router(trace.router)
app.include_router(lineage.router)


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "synapse-trace"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
