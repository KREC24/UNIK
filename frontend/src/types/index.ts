export interface Project {
  id: string;
  external_code?: string;
  name?: string;
  stage?: string;
  client_id?: string;
  created_at: string;
  updated_at?: string;
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
  ptm?: number;
  ogz_notes?: string;
  profile_type?: string;
  steel_grade?: string;
  gost_code?: string;
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

export interface OgzLineItemInput {
  mark?: string;
  type_name?: string;
  quantity: number;
  unit_weight_kg?: number;
  total_weight_kg?: number;
  unit_area_m2?: number;
  total_area_m2?: number;
  ptm?: number;
}

export interface OgzCalculationRequest {
  items: OgzLineItemInput[];
  rei: number;
  environment: string;
}

export interface OgzPositionResult {
  mark?: string;
  type_name?: string;
  quantity: number;
  unit_weight_kg: number;
  unit_area_m2: number;
  reduced_thickness_mm: number;
  matched_composition_name?: string;
  grunt_consumption_kg: number;
  kraska_consumption_kg: number;
  finish_consumption_kg: number;
  position_cost_rub: number;
  verification_warnings: string[];
}

export interface OgzCompositionInfo {
  rei_minutes: number;
  environment: string;
  grunt_name: string;
  grunt_rate_kgm2: number;
  grunt_price_per_kg: number;
  kraska_name: string;
  kraska_rate_kgm2mm: number;
  kraska_price_per_kg: number;
  finish_name: string;
  finish_rate_kgm2: number;
  finish_price_per_kg: number;
}

export interface OgzCalculationTotals {
  total_quantity: number;
  total_weight_kg: number;
  total_area_m2: number;
  grunt_consumption_kg: number;
  kraska_consumption_kg: number;
  finish_consumption_kg: number;
  total_material_cost_rub: number;
}

export interface OgzCalculationResponse {
  positions: OgzPositionResult[];
  totals: OgzCalculationTotals;
  composition?: OgzCompositionInfo;
  errors: string[];
}

// ---------- Settings ----------

export interface AiProviderModel {
  model_id: string;
  display_name: string;
  max_tokens: number;
}

export interface AiProviderConfig {
  enabled: boolean;
  api_key: string;
  api_base: string;
  model: string;
  temperature: number;
  max_tokens: number;
  available_models: AiProviderModel[];
}

export interface AiProvidersSettings {
  deepseek: AiProviderConfig;
  claude: AiProviderConfig;
}

export interface AdminSettings {
  app_name: string;
  company_name: string;
  max_upload_size_mb: number;
  default_currency: string;
  default_environment: string;
  auto_backup_enabled: boolean;
  backup_interval_hours: number;
  debug_mode: boolean;
  log_level: string;
  language: string;
}

export interface AppSettings {
  ai_providers: AiProvidersSettings;
  admin: AdminSettings;
}

export interface SettingsResponse {
  settings: AppSettings;
  last_modified?: string;
  version: number;
}

export interface RecentFile {
  batch_id: string;
  source_file: string;
  batch_type: string;
  status: string;
  total_items: number;
  created_at: string | null;
  project_name: string | null;
  project_id: string | null;
}

export interface DashboardStats {
  total_projects: number;
  total_weight_kg: number;
  total_area_m2: number;
  total_items: number;
  recent_files: RecentFile[];
}

export interface SearchProject {
  id: string;
  external_code?: string;
  name?: string;
  stage?: string;
}

export interface SearchClient {
  id: string;
  name: string;
  inn?: string;
}

export interface SearchBatch {
  batch_id: string;
  source_file: string;
  batch_type: string;
  project_id?: string;
}

export interface SearchResults {
  projects: SearchProject[];
  clients: SearchClient[];
  batches: SearchBatch[];
  total: number;
}

export interface IncomingClient {
  id: string;
  name: string;
  email?: string;
}

export interface IncomingProject {
  id: string;
  name?: string;
  external_code?: string;
}

export interface IncomingRequest {
  id: string;
  sender_email: string;
  sender_name?: string;
  subject?: string;
  body_preview?: string;
  attachments: string[];
  status: "pending" | "matched" | "processing" | "processed" | "failed";
  matched_by?: string;
  result_batch_id?: string;
  error_message?: string;
  received_at: string | null;
  processed_at?: string | null;
  client: IncomingClient | null;
  project: IncomingProject | null;
}

export interface Employee {
  id: string;
  full_name: string;
  telegram_id?: string;
  role: "chief_engineer" | "shop_master" | "worker" | "manager" | "supply";
  department?: string;
  is_active: boolean;
}

export interface TaskEmployee {
  id: string;
  full_name: string;
  role: string;
}

export interface TaskProject {
  id: string;
  name?: string;
  external_code?: string;
}

export interface TaskAssignment {
  id: string;
  project_id?: string;
  line_item_id?: string;
  assigned_to: string;
  assigned_by?: string;
  mark: string;
  quantity: number;
  total_weight_kg?: number;
  drawing_url?: string;
  status: "pending" | "accepted" | "in_work" | "done" | "question" | "rejected";
  deadline?: string;
  notes?: string;
  telegram_msg_id?: string;
  status_changed_at?: string;
  created_at?: string;
  employee: TaskEmployee | null;
  project: TaskProject | null;
  creator: { id: string; full_name: string } | null;
}

export interface TaskStats {
  active: number;
  pending: number;
}
