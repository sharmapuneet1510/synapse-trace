from __future__ import annotations

from pydantic import BaseModel


class FieldConfig(BaseModel):
    header: str
    field_name: str
    asset_classes: list[str] = []


class ConfigType(BaseModel):
    fields: list[FieldConfig]


class JurisdictionConfig(BaseModel):
    id: str
    name: str
    display_name: str
    git_path: str
    lib_path: str
    absolute_download_path: str
    module_type: str  # "exception-service" | "dtcc/iso" | "reporting-service"
    configs: dict[str, ConfigType]


class JurisdictionFile(BaseModel):
    jurisdictions: list[JurisdictionConfig]


# --- Response models ---

class JurisdictionSummary(BaseModel):
    id: str
    name: str
    display_name: str
    module_type: str
    config_types: list[str]
    field_count: int


class ConfigTypeResponse(BaseModel):
    config_type: str
    jurisdiction_id: str
    fields: list[FieldConfig]
