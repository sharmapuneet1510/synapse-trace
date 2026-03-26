"""Loads and validates jurisdiction.json."""
from __future__ import annotations

import json
import logging
from pathlib import Path

from ..schemas.jurisdiction import JurisdictionConfig, JurisdictionFile

logger = logging.getLogger(__name__)

_jurisdictions: dict[str, JurisdictionConfig] = {}


def load_config(path: Path) -> list[JurisdictionConfig]:
    """Load jurisdiction.json and return validated configs."""
    global _jurisdictions
    logger.info("Loading jurisdiction config from %s", path)
    with open(path) as f:
        data = json.load(f)
    parsed = JurisdictionFile(**data)
    _jurisdictions = {j.id: j for j in parsed.jurisdictions}
    for j in parsed.jurisdictions:
        field_count = sum(len(c.fields) for c in j.configs.values())
        logger.debug(
            "  Jurisdiction '%s' (%s): %d config type(s), %d field(s)",
            j.id, j.display_name, len(j.configs), field_count,
        )
    return parsed.jurisdictions


def get_all() -> list[JurisdictionConfig]:
    return list(_jurisdictions.values())


def get_by_id(jurisdiction_id: str) -> JurisdictionConfig | None:
    result = _jurisdictions.get(jurisdiction_id)
    if result is None:
        logger.debug("get_by_id: jurisdiction '%s' not found", jurisdiction_id)
    return result


def get_config_type(jurisdiction_id: str, config_type: str):
    j = _jurisdictions.get(jurisdiction_id)
    if not j:
        logger.debug(
            "get_config_type: jurisdiction '%s' not found", jurisdiction_id
        )
        return None
    ct = j.configs.get(config_type)
    if ct is None:
        logger.debug(
            "get_config_type: config type '%s' not found in '%s'",
            config_type, jurisdiction_id,
        )
    return ct


def get_field(jurisdiction_id: str, field_name: str):
    """Find a field across all config types for a jurisdiction."""
    j = _jurisdictions.get(jurisdiction_id)
    if not j:
        logger.debug("get_field: jurisdiction '%s' not found", jurisdiction_id)
        return None, None
    for config_type, config in j.configs.items():
        for field in config.fields:
            if field.field_name == field_name:
                logger.debug(
                    "get_field: found '%s' in '%s/%s'",
                    field_name, jurisdiction_id, config_type,
                )
                return field, config_type
    logger.debug(
        "get_field: '%s' not found in jurisdiction '%s'", field_name, jurisdiction_id
    )
    return None, None
