import axios from "axios";
import type { ParseResult, BatchPreview, Project, Client, LineItem } from "../types";

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
