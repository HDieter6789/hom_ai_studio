// Shared enum -> visual mapping utilities. Keeps status colors/labels
// consistent across the app instead of duplicating switch statements in
// every component.

export type StatusTone =
  | "blue" // running / in-progress
  | "green" // completed / healthy / production / online
  | "red" // failed / error / unhealthy
  | "gray" // queued / pending / stopped / archived
  | "amber" // warning-ish intermediate states
  | "purple"; // staging / testing

export interface StatusVisual {
  label: string;
  tone: StatusTone;
}

export const toneClassNames: Record<StatusTone, string> = {
  blue: "bg-blue-500/10 text-blue-600 dark:text-blue-400 border-blue-500/20",
  green:
    "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20",
  red: "bg-red-500/10 text-red-600 dark:text-red-400 border-red-500/20",
  gray: "bg-muted text-muted-foreground border-border",
  amber:
    "bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/20",
  purple:
    "bg-violet-500/10 text-violet-600 dark:text-violet-400 border-violet-500/20",
};

export const toneDotClassNames: Record<StatusTone, string> = {
  blue: "bg-blue-500",
  green: "bg-emerald-500",
  red: "bg-red-500",
  gray: "bg-muted-foreground/50",
  amber: "bg-amber-500",
  purple: "bg-violet-500",
};

function titleCase(value: string): string {
  return value
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

const STATUS_MAP: Record<string, StatusVisual> = {
  // Training job / generic run statuses
  queued: { label: "Queued", tone: "gray" },
  preparing: { label: "Preparing", tone: "amber" },
  running: { label: "Running", tone: "blue" },
  evaluating: { label: "Evaluating", tone: "blue" },
  completed: { label: "Completed", tone: "green" },
  failed: { label: "Failed", tone: "red" },
  cancelled: { label: "Cancelled", tone: "gray" },

  // Dataset statuses
  uploading: { label: "Uploading", tone: "amber" },
  validating: { label: "Validating", tone: "amber" },
  ready: { label: "Ready", tone: "green" },
  invalid: { label: "Invalid", tone: "red" },

  // Base model statuses
  available: { label: "Available", tone: "green" },
  downloading: { label: "Downloading", tone: "amber" },
  unavailable: { label: "Unavailable", tone: "gray" },
  error: { label: "Error", tone: "red" },

  // Model version (registry) statuses
  experimental: { label: "Experimental", tone: "gray" },
  testing: { label: "Testing", tone: "purple" },
  staging: { label: "Staging", tone: "purple" },
  production: { label: "Production", tone: "green" },
  archived: { label: "Archived", tone: "gray" },

  // Deployment statuses
  pending: { label: "Pending", tone: "gray" },
  starting: { label: "Starting", tone: "amber" },
  healthy: { label: "Healthy", tone: "green" },
  unhealthy: { label: "Unhealthy", tone: "amber" },
  stopped: { label: "Stopped", tone: "gray" },

  // Worker statuses
  online: { label: "Online", tone: "green" },
  offline: { label: "Offline", tone: "gray" },
  busy: { label: "Busy", tone: "blue" },
};

export function getStatusVisual(status: string | null | undefined): StatusVisual {
  if (!status) return { label: "Unknown", tone: "gray" };
  return STATUS_MAP[status] ?? { label: titleCase(status), tone: "gray" };
}

const ACTIVE_TRAINING_STATUSES = new Set([
  "queued",
  "preparing",
  "running",
  "evaluating",
]);

export function isActiveTrainingStatus(status: string): boolean {
  return ACTIVE_TRAINING_STATUSES.has(status);
}

// Role labels for Settings / user display.
export const ROLE_LABELS: Record<string, string> = {
  admin: "Admin",
  ml_engineer: "ML Engineer",
  developer: "Developer",
  viewer: "Viewer",
};

export function getRoleLabel(role: string | null | undefined): string {
  if (!role) return "Unknown";
  return ROLE_LABELS[role] ?? titleCase(role);
}

// Provider labels
export const PROVIDER_LABELS: Record<string, string> = {
  qwen: "Qwen",
  mistral: "Mistral",
  llama: "Llama",
  gemma: "Gemma",
  other: "Other",
  local: "Local",
  remote: "Remote",
};

export function getProviderLabel(provider: string | null | undefined): string {
  if (!provider) return "Unknown";
  return PROVIDER_LABELS[provider] ?? titleCase(provider);
}

// Dataset type labels
export const DATASET_TYPE_LABELS: Record<string, string> = {
  instruction: "Instruction",
  conversation: "Conversation",
  tool_calling: "Tool Calling",
  preference: "Preference",
  agent_trajectory: "Agent Trajectory",
  evaluation: "Evaluation",
};

export function getDatasetTypeLabel(type: string | null | undefined): string {
  if (!type) return "Unknown";
  return DATASET_TYPE_LABELS[type] ?? titleCase(type);
}

// Training type labels
export const TRAINING_TYPE_LABELS: Record<string, string> = {
  lora: "LoRA",
  qlora: "QLoRA",
  full_fine_tuning: "Full Fine-tuning",
  sft: "SFT",
  dpo: "DPO",
};

export function getTrainingTypeLabel(type: string | null | undefined): string {
  if (!type) return "Unknown";
  return TRAINING_TYPE_LABELS[type] ?? titleCase(type);
}

export const TRAINING_PRESET_LABELS: Record<string, string> = {
  fast: "Fast",
  balanced: "Balanced",
  high_quality: "High Quality",
  custom: "Custom",
};

export function getTrainingPresetLabel(preset: string | null | undefined): string {
  if (!preset) return "Unknown";
  return TRAINING_PRESET_LABELS[preset] ?? titleCase(preset);
}
