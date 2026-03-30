"""GET/PUT /config endpoints."""
from __future__ import annotations
import os
import yaml
from typing import Any, Dict
from fastapi import APIRouter, HTTPException

router = APIRouter()

_TRACE_RULES = "configs/trace_rules.yaml"


@router.get("/", summary="Get current trace configuration")
def get_config() -> Dict[str, Any]:
    if not os.path.isfile(_TRACE_RULES):
        raise HTTPException(status_code=404, detail="Trace config file not found")
    with open(_TRACE_RULES) as f:
        return yaml.safe_load(f) or {}


@router.put("/", summary="Update trace configuration")
def update_config(updates: Dict[str, Any]) -> Dict[str, Any]:
    if not os.path.isfile(_TRACE_RULES):
        raise HTTPException(status_code=404, detail="Trace config file not found")
    with open(_TRACE_RULES) as f:
        cfg = yaml.safe_load(f) or {}
    # Deep merge updates
    def _merge(base: dict, patch: dict) -> dict:
        for k, v in patch.items():
            if isinstance(v, dict) and isinstance(base.get(k), dict):
                base[k] = _merge(base[k], v)
            else:
                base[k] = v
        return base
    cfg = _merge(cfg, updates)
    with open(_TRACE_RULES, "w") as f:
        yaml.dump(cfg, f, default_flow_style=False)
    return cfg
