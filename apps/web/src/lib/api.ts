// Typed API client for the H.O.M AI Studio backend (FastAPI).
//
// All requests attach the JWT stored in localStorage (key "hom_token") as a
// Bearer token, except the login call itself. A 401 response clears the
// stored token and redirects to /login.
//
// Every exported function returns a Promise that resolves with the parsed
// response, or throws an `ApiError`. Callers (hooks) are expected to catch
// this and surface a friendly inline error instead of crashing the page.

import type {
  AuditLogEntry,
  BaseModelOut,
  CreateBaseModelInput,
  CreateDeploymentInput,
  CreateEvaluationInput,
  CreateTrainingJobInput,
  DatasetOut,
  DatasetPreview,
  DatasetType,
  DeploymentOut,
  EvaluationCompareOut,
  EvaluationOut,
  LoginResponse,
  ModelAliasOut,
  ModelVersionOut,
  ModelVersionStatus,
  OverviewOut,
  RegisterModelVersionInput,
  SetModelAliasInput,
  TrainingJobOut,
  TrainingLogEntry,
  User,
  WorkerOut,
} from "@/lib/types";

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export const TOKEN_STORAGE_KEY = "hom_token";

export class ApiError extends Error {
  status: number;
  body: unknown;

  constructor(message: string, status: number, body?: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.body = body;
  }
}

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  try {
    return window.localStorage.getItem(TOKEN_STORAGE_KEY);
  } catch {
    return null;
  }
}

export function setToken(token: string) {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(TOKEN_STORAGE_KEY, token);
  } catch {
    // ignore (e.g. storage disabled)
  }
}

export function clearToken() {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.removeItem(TOKEN_STORAGE_KEY);
  } catch {
    // ignore
  }
}

function redirectToLogin() {
  if (typeof window === "undefined") return;
  if (window.location.pathname === "/login") return;
  // Full reload (this module lives outside the React tree, so no router is
  // available) so any in-memory app state is discarded on session expiry.
  // eslint-disable-next-line @next/next/no-location-assign-relative-destination
  window.location.href = "/login";
}

async function extractErrorMessage(res: Response): Promise<string> {
  try {
    const data = await res.clone().json();
    if (typeof data?.detail === "string") return data.detail;
    if (Array.isArray(data?.detail)) {
      return data.detail
        .map((d: { msg?: string }) => d.msg)
        .filter(Boolean)
        .join(", ");
    }
    if (typeof data?.message === "string") return data.message;
  } catch {
    // not JSON, fall through
  }
  return res.statusText || `Request failed with status ${res.status}`;
}

interface RequestOptions {
  method?: string;
  body?: unknown;
  isForm?: boolean;
  skipAuth?: boolean;
  query?: Record<string, string | number | boolean | undefined | null>;
}

function buildUrl(
  path: string,
  query?: RequestOptions["query"],
): string {
  const url = new URL(
    path.startsWith("http") ? path : `${API_BASE_URL}${path}`,
  );
  if (query) {
    for (const [key, value] of Object.entries(query)) {
      if (value === undefined || value === null || value === "") continue;
      url.searchParams.set(key, String(value));
    }
  }
  return url.toString();
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = "GET", body, isForm, skipAuth, query } = options;

  const headers: Record<string, string> = {};
  if (!isForm && body !== undefined) {
    headers["Content-Type"] = "application/json";
  }

  if (!skipAuth) {
    const token = getToken();
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
  }

  let res: Response;
  try {
    res = await fetch(buildUrl(path, query), {
      method,
      headers,
      body: body === undefined ? undefined : isForm ? (body as FormData) : JSON.stringify(body),
    });
  } catch {
    throw new ApiError(
      `Could not reach the H.O.M AI Studio API at ${API_BASE_URL}. Is the backend running?`,
      0,
    );
  }

  if (res.status === 401 && !skipAuth) {
    clearToken();
    redirectToLogin();
    throw new ApiError("Session expired. Please sign in again.", 401);
  }

  if (res.status === 204) {
    return undefined as T;
  }

  if (!res.ok) {
    const message = await extractErrorMessage(res);
    throw new ApiError(message, res.status);
  }

  const text = await res.text();
  if (!text) return undefined as T;
  return JSON.parse(text) as T;
}

// ---------------------------------------------------------------------------
// Auth
// ---------------------------------------------------------------------------

export async function login(email: string, password: string): Promise<LoginResponse> {
  return request<LoginResponse>("/api/auth/login", {
    method: "POST",
    body: { email, password },
    skipAuth: true,
  });
}

export async function getCurrentUser(): Promise<User> {
  return request<User>("/api/auth/me");
}

// ---------------------------------------------------------------------------
// Overview
// ---------------------------------------------------------------------------

export async function getOverview(): Promise<OverviewOut> {
  return request<OverviewOut>("/api/overview");
}

// ---------------------------------------------------------------------------
// Datasets
// ---------------------------------------------------------------------------

export async function listDatasets(): Promise<DatasetOut[]> {
  return request<DatasetOut[]>("/api/datasets");
}

export async function getDataset(id: string): Promise<DatasetOut> {
  return request<DatasetOut>(`/api/datasets/${id}`);
}

export async function getDatasetPreview(
  id: string,
  limit = 20,
): Promise<DatasetPreview> {
  return request<DatasetPreview>(`/api/datasets/${id}/preview`, {
    query: { limit },
  });
}

export interface UploadDatasetInput {
  name: string;
  description?: string;
  type: DatasetType;
  file: File;
}

export async function uploadDataset(input: UploadDatasetInput): Promise<DatasetOut> {
  const form = new FormData();
  form.set("name", input.name);
  if (input.description) form.set("description", input.description);
  form.set("type", input.type);
  form.set("file", input.file);
  return request<DatasetOut>("/api/datasets", {
    method: "POST",
    body: form,
    isForm: true,
  });
}

export async function deleteDataset(id: string): Promise<void> {
  return request<void>(`/api/datasets/${id}`, { method: "DELETE" });
}

// ---------------------------------------------------------------------------
// Base models
// ---------------------------------------------------------------------------

export async function listBaseModels(): Promise<BaseModelOut[]> {
  return request<BaseModelOut[]>("/api/models");
}

export async function getBaseModel(id: string): Promise<BaseModelOut> {
  return request<BaseModelOut>(`/api/models/${id}`);
}

export async function createBaseModel(
  input: CreateBaseModelInput,
): Promise<BaseModelOut> {
  return request<BaseModelOut>("/api/models", {
    method: "POST",
    body: input,
  });
}

// ---------------------------------------------------------------------------
// Training
// ---------------------------------------------------------------------------

export async function listTrainingJobs(): Promise<TrainingJobOut[]> {
  return request<TrainingJobOut[]>("/api/training/jobs");
}

export async function getTrainingJob(id: string): Promise<TrainingJobOut> {
  return request<TrainingJobOut>(`/api/training/jobs/${id}`);
}

export async function getTrainingJobLogs(
  id: string,
  limit = 500,
): Promise<TrainingLogEntry[]> {
  return request<TrainingLogEntry[]>(`/api/training/jobs/${id}/logs`, {
    query: { limit },
  });
}

export async function createTrainingJob(
  input: CreateTrainingJobInput,
): Promise<TrainingJobOut> {
  return request<TrainingJobOut>("/api/training/jobs", {
    method: "POST",
    body: input,
  });
}

export async function cancelTrainingJob(id: string): Promise<TrainingJobOut> {
  return request<TrainingJobOut>(`/api/training/jobs/${id}/cancel`, {
    method: "POST",
  });
}

// ---------------------------------------------------------------------------
// Evaluations
// ---------------------------------------------------------------------------

export async function listEvaluations(
  modelVersionId?: string,
): Promise<EvaluationOut[]> {
  return request<EvaluationOut[]>("/api/evaluations", {
    query: { model_version_id: modelVersionId },
  });
}

export async function createEvaluation(
  input: CreateEvaluationInput,
): Promise<EvaluationOut> {
  return request<EvaluationOut>("/api/evaluations", {
    method: "POST",
    body: input,
  });
}

export async function compareEvaluations(
  versionIdA: string,
  versionIdB: string,
): Promise<EvaluationCompareOut> {
  return request<EvaluationCompareOut>("/api/evaluations/compare", {
    method: "POST",
    body: { version_id_a: versionIdA, version_id_b: versionIdB },
  });
}

// ---------------------------------------------------------------------------
// Registry
// ---------------------------------------------------------------------------

export async function listRegistryVersions(
  modelName?: string,
): Promise<ModelVersionOut[]> {
  return request<ModelVersionOut[]>("/api/registry", {
    query: { model_name: modelName },
  });
}

export async function registerModelVersion(
  input: RegisterModelVersionInput,
): Promise<ModelVersionOut> {
  return request<ModelVersionOut>("/api/registry", {
    method: "POST",
    body: input,
  });
}

export async function listModelAliases(): Promise<ModelAliasOut[]> {
  return request<ModelAliasOut[]>("/api/registry/aliases");
}

export async function setModelAlias(
  input: SetModelAliasInput,
): Promise<ModelAliasOut> {
  return request<ModelAliasOut>("/api/registry/aliases", {
    method: "PUT",
    body: input,
  });
}

export async function getModelVersionByAlias(
  alias: string,
): Promise<ModelVersionOut> {
  return request<ModelVersionOut>(`/api/registry/aliases/${alias}`);
}

export async function getModelVersionsByName(
  modelName: string,
): Promise<ModelVersionOut[]> {
  return request<ModelVersionOut[]>(`/api/registry/${modelName}`);
}

export async function setModelVersionStatus(
  versionId: string,
  status: ModelVersionStatus,
): Promise<ModelVersionOut> {
  return request<ModelVersionOut>(`/api/registry/versions/${versionId}/status`, {
    method: "PATCH",
    body: { status },
  });
}

// ---------------------------------------------------------------------------
// Deployments
// ---------------------------------------------------------------------------

export async function listDeployments(): Promise<DeploymentOut[]> {
  return request<DeploymentOut[]>("/api/deployments");
}

export async function getDeployment(id: string): Promise<DeploymentOut> {
  return request<DeploymentOut>(`/api/deployments/${id}`);
}

export async function createDeployment(
  input: CreateDeploymentInput,
): Promise<DeploymentOut> {
  return request<DeploymentOut>("/api/deployments", {
    method: "POST",
    body: input,
  });
}

export async function stopDeployment(id: string): Promise<DeploymentOut> {
  return request<DeploymentOut>(`/api/deployments/${id}`, {
    method: "DELETE",
  });
}

// ---------------------------------------------------------------------------
// Infrastructure
// ---------------------------------------------------------------------------

export async function listWorkers(): Promise<WorkerOut[]> {
  return request<WorkerOut[]>("/api/workers");
}

// ---------------------------------------------------------------------------
// Audit log
// ---------------------------------------------------------------------------

export async function listAuditLog(limit = 100): Promise<AuditLogEntry[]> {
  return request<AuditLogEntry[]>("/api/audit", { query: { limit } });
}
