export interface FieldConfig {
  header: string;
  field_name: string;
  asset_classes: string[];
}

export interface JurisdictionSummary {
  id: string;
  name: string;
  display_name: string;
  module_type: string;
  config_types: string[];
  field_count: number;
}

export interface ConfigTypeResponse {
  config_type: string;
  jurisdiction_id: string;
  fields: FieldConfig[];
}
