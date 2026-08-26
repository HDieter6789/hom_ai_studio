// Shared domain types matching the FastAPI backend response shapes.
// Keep these in sync with apps/api response models.

export type UserRole = "admin" | "ml_engineer" | "developer" | "viewer";

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
}

// ---------------------------------------------------------------------------
// Overview
// ---------------------------------------------------------------------------

export interface OverviewStats {
  models_total: number;
  production_models: number;
  active_training_jobs: number;
  training_jobs_last_30_days: number;
  datasets_total: number;
  training_samples_total: number;
  gpu_workers_online: number;
  gpu_workers_total: number;
  avg_gpu_utilization_pct: number | null;
  active_deployments: number;
}

export interface OverviewOut {
  stats: OverviewStats;
  recent_training_runs: TrainingJobOut[];
  production_models: ModelVersionOut[];
}

// ---------------------------------------------------------------------------
// Datasets
// ---------------------------------------------------------------------------

export type DatasetType =
  | "instruction"
  | "conversation"
  | "tool_calling"
  | "preference"
  | "agent_trajectory"
  | "evaluation";

export type DatasetFormat = "json" | "jsonl" | "csv";

export type DatasetStatus = "uploading" | "validating" | "ready" | "invalid";

export interface DatasetSchemaInfo {
  detected_format: string | null;
  fields: string[];
  has_messages: boolean;
  has_tool_calls: boolean;
  has_trajectory_fields: boolean;
  sample_preview: unknown[];
}

export interface DatasetStats {
  sample_count: number;
  valid_count: number;
  invalid_count: number;
  avg_tokens: number | null;
  min_tokens: number | null;
  max_tokens: number | null;
  possible_duplicates: number;
}

export interface DatasetOut {
  id: string;
  name: string;
  description: string | null;
  version: number;
  type: DatasetType;
  format: DatasetFormat;
  source: string | null;
  status: DatasetStatus;
  sample_count: number;
  file_size_bytes: number;
  schema_info: DatasetSchemaInfo | null;
  stats: DatasetStats | null;
  validation_errors: string[];
  created_at: string;
  updated_at: string;
  created_by: string | null;
}

export interface DatasetPreview {
  samples: Record<string, unknown>[];
}

// ---------------------------------------------------------------------------
// Base models
// ---------------------------------------------------------------------------

export type ModelProvider = "qwen" | "mistral" | "llama" | "gemma" | "other";

export type BaseModelStatus =
  | "available"
  | "downloading"
  | "unavailable"
  | "error";

export interface BaseModelOut {
  id: string;
  name: string;
  provider: ModelProvider;
  huggingface_id: string | null;
  architecture: string | null;
  parameter_count: number | null;
  context_length: number | null;
  license: string | null;
  quantization: string | null;
  local_path: string | null;
  status: BaseModelStatus;
  created_at: string;
}

export interface CreateBaseModelInput {
  name: string;
  provider: ModelProvider;
  huggingface_id?: string;
  architecture?: string;
  parameter_count?: number;
  context_length?: number;
  license?: string;
  quantization?: string;
  local_path?: string;
  status?: BaseModelStatus;
}

// ---------------------------------------------------------------------------
// Training
// ---------------------------------------------------------------------------

export type TrainingPreset = "fast" | "balanced" | "high_quality" | "custom";

export type TrainingType = "lora" | "qlora" | "full_fine_tuning" | "sft" | "dpo";

export type TrainingJobStatus =
  | "queued"
  | "preparing"
  | "running"
  | "evaluating"
  | "completed"
  | "failed"
  | "cancelled";

export interface TrainingHyperparameters {
  epochs: number | null;
  learning_rate: number | null;
  batch_size: number | null;
  gradient_accumulation_steps: number | null;
  context_length: number | null;
  warmup_ratio: number | null;
  weight_decay: number | null;
  lora_rank: number | null;
  lora_alpha: number | null;
  lora_dropout: number | null;
  bf16: boolean | null;
  fp16: boolean | null;
  gradient_checkpointing: boolean | null;
}

export interface TrainingJobOut {
  id: string;
  name: string;
  base_model_id: string;
  dataset_id: string;
  training_type: TrainingType;
  preset: TrainingPreset;
  hyperparameters: Partial<TrainingHyperparameters>;
  status: TrainingJobStatus;
  provider: string | null;
  worker_id: string | null;
  current_epoch: number | null;
  current_step: number | null;
  total_steps: number | null;
  loss: number | null;
  learning_rate: number | null;
  gpu_memory_used_gb: number | null;
  gpu_utilization_pct: number | null;
  samples_per_sec: number | null;
  tokens_per_sec: number | null;
  progress_pct: number | null;
  error_code: string | null;
  error_message: string | null;
  failed_step: string | null;
  suggested_actions: string[];
  output_dir: string | null;
  artifacts: Record<string, unknown> | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
}

export interface CreateTrainingJobInput {
  name: string;
  base_model_id: string;
  dataset_id: string;
  preset?: TrainingPreset;
  training_type?: TrainingType;
  hyperparameter_overrides?: Record<string, unknown>;
}

export interface TrainingLogEntry {
  timestamp: string;
  level: string;
  message: string;
}

// ---------------------------------------------------------------------------
// Evaluations
// ---------------------------------------------------------------------------

export interface EvaluationMetrics {
  crm_accuracy: number | null;
  tool_selection_accuracy: number | null;
  tool_argument_accuracy: number | null;
  structured_output_accuracy: number | null;
  hallucination_rate: number | null;
  workflow_selection_accuracy: number | null;
  instruction_following: number | null;
  response_quality: number | null;
  latency_ms: number | null;
  tokens_per_sec: number | null;
}

export interface EvaluationOut {
  id: string;
  model_version_id: string;
  dataset_id: string | null;
  metrics: Partial<EvaluationMetrics>;
  sample_count: number | null;
  notes: string | null;
  created_at: string;
}

export interface CreateEvaluationInput {
  model_version_id: string;
  dataset_id?: string;
  metrics: Partial<EvaluationMetrics>;
  sample_count?: number;
  notes?: string;
}

export interface EvaluationCompareSide {
  id: string;
  display_name: string;
}

export interface EvaluationMetricDelta {
  a: number | null;
  b: number | null;
  delta: number | null;
}

export interface EvaluationCompareOut {
  a: EvaluationCompareSide;
  b: EvaluationCompareSide;
  metrics: Record<string, EvaluationMetricDelta>;
}

// ---------------------------------------------------------------------------
// Registry
// ---------------------------------------------------------------------------

export type ModelVersionStatus =
  | "experimental"
  | "testing"
  | "staging"
  | "production"
  | "archived";

export interface ModelVersionOut {
  id: string;
  model_name: string;
  version: number;
  display_name: string;
  base_model_id: string | null;
  dataset_id: string | null;
  training_job_id: string | null;
  training_config: Record<string, unknown> | null;
  training_metrics: Record<string, unknown> | null;
  evaluation_metrics: Record<string, unknown> | null;
  artifact_location: string | null;
  status: ModelVersionStatus;
  deployment_status: string | null;
  created_at: string;
}

export interface RegisterModelVersionInput {
  training_job_id: string;
  model_name: string;
}

export interface ModelAliasOut {
  alias: string;
  model_version_id: string;
  updated_at?: string;
}

export interface SetModelAliasInput {
  alias: string;
  model_version_id: string;
}

// ---------------------------------------------------------------------------
// Deployments
// ---------------------------------------------------------------------------

export type DeploymentStatus =
  | "pending"
  | "starting"
  | "healthy"
  | "unhealthy"
  | "stopped"
  | "failed";

export interface DeploymentOut {
  id: string;
  model_version_id: string;
  served_model_name: string;
  endpoint_url: string | null;
  status: DeploymentStatus;
  worker_id: string | null;
  gpu_memory_utilization: number | null;
  max_model_len: number | null;
  started_at: string | null;
  stopped_at: string | null;
  last_health_check_at: string | null;
  last_health_detail: string | null;
  created_at: string;
}

export interface CreateDeploymentInput {
  model_version_id: string;
  served_model_name: string;
  gpu_memory_utilization?: number;
  max_model_len?: number;
}

// ---------------------------------------------------------------------------
// Infrastructure
// ---------------------------------------------------------------------------

export type WorkerStatus = "online" | "offline" | "busy" | "error";

export type ComputeProvider = "local" | "remote";

export interface WorkerGpu {
  index: number;
  name: string;
  vram_total_gb: number;
  vram_used_gb: number;
  utilization_pct: number;
  temperature_c: number | null;
}

export interface WorkerOut {
  id: string;
  worker_key: string;
  hostname: string;
  status: WorkerStatus;
  compute_provider: ComputeProvider;
  gpus: WorkerGpu[];
  running_job_id: string | null;
  last_heartbeat_at: string | null;
}

// ---------------------------------------------------------------------------
// Audit log
// ---------------------------------------------------------------------------

export interface AuditLogEntry {
  id: string;
  action: string;
  actor: string | null;
  target_type: string | null;
  target_id: string | null;
  event_metadata: Record<string, unknown> | null;
  timestamp: string;
}
