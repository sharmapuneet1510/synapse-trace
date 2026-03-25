"""Loads and validates jurisdiction.json."""
from __future__ import annotations

import json
from pathlib import Path

from ..schemas.jurisdiction import JurisdictionConfig, JurisdictionFile


_jurisdictions: dict[str, JurisdictionConfig] = {}


def load_config(path: Path) -> list[JurisdictionConfig]:
    """Load jurisdiction.json and return validated configs."""
    global _jurisdictions
    with open(path) as f:
        data = json.load(f)
    parsed = JurisdictionFile(**data)
    _jurisdictions = {j.id: j for j in parsed.jurisdictions}
    return parsed.jurisdictions


def get_all() -> list[JurisdictionConfig]:
    return list(_jurisdictions.values())


def get_by_id(jurisdiction_id: str) -> JurisdictionConfig | None:
    return _jurisdictions.get(jurisdiction_id)


def get_config_type(jurisdiction_id: str, config_type: str):
    j = _jurisdictions.get(jurisdiction_id)
    if not j:
        return None
    return j.configs.get(config_type)


def get_field(jurisdiction_id: str, field_name: str):
    """Find a field across all config types for a jurisdiction."""
    j = _jurisdictions.get(jurisdiction_id)
    if not j:
        return None, None
    for config_type, config in j.configs.items():
        for field in config.fields:
            if field.field_name == field_name:
                return field, config_type
    return None, None
