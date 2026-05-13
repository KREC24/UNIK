import axios from "axios";
import type {
  ParseResult,
  BatchPreview,
  Project,
  Client,
  OgzCalculationRequest,
  OgzCalculationResponse,
  SettingsResponse,
  AppSettings,
  AiProviderConfig,
  AdminSettings,
  DashboardStats,
  SearchResults,
  IncomingRequest,
  Employee,
  TaskAssignment,
  TaskStats,
} from "../types";

const api = axios.create({
  baseURL: "http://localhost:8000/api/v1",
  timeout: 60000,
  headers: { "Content-Type": "application/json" },
});

export async function uploadPdf(
  file: File,
  parserType?: string,
  onProgress?: (pct: number) => void
): Promise<ParseResult & { batch_id: string }> {
  const form = new FormData();
  form.append("file", file);
  const url = parserType
    ? `/parse/upload?parser_type=${parserType}`
    : "/parse/upload";
  const { data } = await api.post(url, form, {
    headers: { "Content-Type": "multipart/form-data" },
    onUploadProgress: (e) => {
      if (e.total && onProgress) {
        onProgress(Math.round((e.loaded * 100) / e.total));
      }
    },
  });
  return data;
}

export async function getBatchPreview(batchId: string): Promise<BatchPreview> {
  const { data } = await api.get(`/parse/batches/${batchId}/preview`);
  return data;
}

export async function getBatchStatus(batchId: string): Promise<ParseResult> {
  const { data } = await api.get(`/parse/batches/${batchId}`);
  return data;
}

export function getExportUrl(batchId: string, format: "json" | "csv" | "xlsx"): string {
  return `${api.defaults.baseURL}/parse/batches/${batchId}/export/${format}`;
}

export async function getProjects(): Promise<Project[]> {
  const { data } = await api.get("/projects");
  return data;
}

export async function createProject(body: Partial<Project>): Promise<Project> {
  const { data } = await api.post("/projects", body);
  return data;
}

export async function getProjectDetails(projectId: string): Promise<{
  project: Project;
  batches: { batch_id: string; source_file: string; total_items: number; success_rate: number }[];
}> {
  const { data } = await api.get(`/projects/${projectId}`);
  return data;
}

export async function getClients(): Promise<Client[]> {
  const { data } = await api.get("/clients");
  return data;
}

export async function createClient(body: Partial<Client>): Promise<Client> {
  const { data } = await api.post("/clients", body);
  return data;
}

export async function calculateOgz(
  request: OgzCalculationRequest
): Promise<OgzCalculationResponse> {
  const { data } = await api.post("/ogz/calculate", request);
  return data;
}

// ---------- Settings ----------

export async function getSettings(): Promise<SettingsResponse> {
  const { data } = await api.get("/settings");
  return data;
}

export async function updateSettings(body: Partial<AppSettings>): Promise<SettingsResponse> {
  const { data } = await api.put("/settings", body);
  return data;
}

export async function resetSettings(): Promise<SettingsResponse> {
  const { data } = await api.post("/settings/reset");
  return data;
}

export async function getAiProviderConfig(provider: string): Promise<AiProviderConfig> {
  const { data } = await api.get(`/settings/ai/${provider}`);
  return data;
}

export async function updateAiProviderConfig(
  provider: string,
  config: AiProviderConfig
): Promise<AiProviderConfig> {
  const { data } = await api.put(`/settings/ai/${provider}`, config);
  return data;
}

export async function getAdminSettings(): Promise<AdminSettings> {
  const { data } = await api.get("/settings/admin");
  return data;
}

export async function updateAdminSettings(body: AdminSettings): Promise<AdminSettings> {
  const { data } = await api.put("/settings/admin", body);
  return data;
}

export async function getDashboard(): Promise<DashboardStats> {
  const { data } = await api.get("/dashboard");
  return data;
}

export async function searchAll(query: string): Promise<SearchResults> {
  const { data } = await api.get("/search", { params: { q: query } });
  return data;
}

export async function getIncomingEmail(): Promise<{ email: string }> {
  const { data } = await api.get("/incoming/email");
  return data;
}

export async function getIncomingRequests(): Promise<IncomingRequest[]> {
  const { data } = await api.get("/incoming");
  return data;
}

export async function matchIncomingClient(requestId: string, clientId: string): Promise<IncomingRequest> {
  const { data } = await api.post(`/incoming/${requestId}/match`, null, { params: { client_id: clientId } });
  return data;
}

export async function processIncomingRequest(requestId: string): Promise<IncomingRequest> {
  const { data } = await api.post(`/incoming/${requestId}/process`);
  return data;
}

export async function getEmployees(): Promise<Employee[]> {
  const { data } = await api.get("/employees");
  return data;
}

export async function createEmployee(body: Partial<Employee>): Promise<Employee> {
  const { data } = await api.post("/employees", body);
  return data;
}

export async function updateEmployee(id: string, body: Partial<Employee>): Promise<Employee> {
  const { data } = await api.put(`/employees/${id}`, body);
  return data;
}

export async function deleteEmployee(id: string): Promise<void> {
  await api.delete(`/employees/${id}`);
}

export async function getTasks(status?: string): Promise<TaskAssignment[]> {
  const { data } = await api.get("/tasks", { params: status ? { status } : {} });
  return data;
}

export async function getTaskStats(): Promise<TaskStats> {
  const { data } = await api.get("/tasks/stats");
  return data;
}

export async function assignTask(body: Record<string, unknown>): Promise<TaskAssignment> {
  const { data } = await api.post("/tasks/assign", body);
  return data;
}
