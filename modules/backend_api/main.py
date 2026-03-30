"""Data Lineage Platform – FastAPI application entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from modules.backend_api.routes import trace, graph, config, logs

app = FastAPI(
    title="Data Lineage Platform API",
    version="1.0.0",
    description="Field-level data lineage tracing for XSLT and Java codebases.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(trace.router, prefix="/trace", tags=["Trace"])
app.include_router(graph.router, prefix="/graph", tags=["Graph"])
app.include_router(config.router, prefix="/config", tags=["Config"])
app.include_router(logs.router, prefix="/logs", tags=["Logs"])


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok", "service": "Data Lineage Platform API"}


@app.get("/", tags=["Health"])
def root():
    return {"message": "Data Lineage Platform API – see /docs for OpenAPI"}
