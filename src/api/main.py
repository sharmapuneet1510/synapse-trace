"""Synapse Trace API — FastAPI application."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import CORS_ORIGINS, JURISDICTION_JSON
from .database import init_db
from .routers import chat, dashboard, fields, jurisdictions, llm, parse, translation, xpath
from .services import jurisdiction_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialise database tables
    init_db()
    print("Database initialised")
    # Startup: load jurisdiction config
    jurisdiction_service.load_config(JURISDICTION_JSON)
    print(f"Loaded {len(jurisdiction_service.get_all())} jurisdictions from {JURISDICTION_JSON}")
    yield
    # Shutdown
    print("Synapse Trace API shutting down")


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


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "synapse-trace"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
