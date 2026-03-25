export interface XPathEntry {
  name: string;
  source: string;
  xpath: string;
  template?: string;
  output_element?: string;
  line?: number;
}

export interface DependencyRef {
  field_name: string;
  relationship: string;
  source_type: string;
  file_path?: string;
  line_number?: number;
}

export interface JavaReference {
  class_name: string;
  method_name?: string;
  finding_type: string;
  code_snippet?: string;
  file_path?: string;
  line_number?: number;
}

export interface FieldDetail {
  jurisdiction_id: string;
  field_name: string;
  header: string;
  asset_classes: string[];
  config_type: string;
  xslt_logic?: string;
  xslt_file?: string;
  xslt_line?: number;
  input_xpaths: XPathEntry[];
  dependencies: DependencyRef[];
  java_references: JavaReference[];
}
