export interface Project {
  id: string;
  external_code?: string;
  name?: string;
  stage?: string;
  created_at: string;
}

export interface LineItem {
  position?: number;
  mark?: string;
  type_name?: string;
  quantity?: number;
  length_x?: number;
  width_y?: number;
  height_z?: number;
  unit_weight_kg?: number;
  total_weight_kg?: number;
  unit_area_m2?: number;
  total_area_m2?: number;
  ogz_notes?: string;
  profile_type?: string;
  steel_grade?: string;
  confidence: number;
  issues: string[];
}

export interface UnrecognizedRow {
  raw_text?: string;
  partial_data: Record<string, unknown>;
  issues: string[];
}

export interface Metadata {
  project_code?: string;
  object_name?: string;
  stage?: string;
}

export interface ParseResult {
  batch_id?: string;
  source_file: string;
  batch_type: string;
  metadata: Metadata;
  items: LineItem[];
  unrecognized_rows: UnrecognizedRow[];
  errors: string[];
  total_rows_parsed: number;
  total_rows_raw: number;
  success_rate: number;
}

export interface BatchPreview {
  batch_id: string;
  source_file: string;
  status: string;
  total_items: number;
  items: LineItem[];
  unrecognized_count: number;
}

export interface Client {
  id: string;
  name: string;
  inn?: string;
  contacts?: Record<string, unknown>;
  created_at: string;
}
