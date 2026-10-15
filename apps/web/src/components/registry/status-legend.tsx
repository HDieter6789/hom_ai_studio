import { StatusBadge } from "@/components/shared/status-badge";
import type { ModelVersionStatus } from "@/lib/types";

const REGISTRY_STATUSES: Array<{
  status: ModelVersionStatus;
  description: string;
}> = [
  { status: "experimental", description: "In fachlicher Bearbeitung" },
  { status: "testing", description: "Wird gegen Tests geprueft" },
  { status: "staging", description: "Fuer Vorabpruefungen eingeordnet" },
  { status: "production", description: "Als Produktionsstatus zugewiesen" },
  { status: "archived", description: "Nicht mehr zur Auswahl vorgesehen" },
];

const KNOWN_REGISTRY_STATUSES = new Set<ModelVersionStatus>(
  REGISTRY_STATUSES.map(({ status }) => status),
);

export function RegistryStatusBadge({ status }: { status: string | null | undefined }) {
  if (!status || !KNOWN_REGISTRY_STATUSES.has(status as ModelVersionStatus)) {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full border border-border bg-muted px-2 py-0.5 text-xs font-medium whitespace-nowrap text-muted-foreground">
        <span className="size-1.5 rounded-full bg-muted-foreground/50" />
        Status nicht verfuegbar
      </span>
    );
  }

  return <StatusBadge status={status} />;
}

export function RegistryStatusLegend() {
  return (
    <section
      aria-labelledby="registry-status-legend-title"
      className="rounded-xl border bg-card p-4 shadow-sm"
      data-registry-status-legend
    >
      <div className="flex flex-col gap-1 sm:flex-row sm:items-start sm:justify-between sm:gap-4">
        <div>
          <h2 id="registry-status-legend-title" className="text-sm font-semibold">
            Statuslegende fuer Modellversionen
          </h2>
          <p className="mt-1 max-w-2xl text-sm text-muted-foreground">
            Die Zustaende ordnen Registry-Versionen ein. Sie sind keine Aussage ueber
            Modellqualitaet, Freigabe oder Empfehlung.
          </p>
        </div>
        <span
          className="mt-2 text-xs font-medium whitespace-nowrap text-muted-foreground sm:mt-0"
          data-daily-marker="AI Studio Daily 2026-10-15"
        >
          AI Studio Daily 2026-10-15
        </span>
      </div>

      <ul className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
        {REGISTRY_STATUSES.map(({ status, description }) => (
          <li
            key={status}
            className="flex min-w-0 items-start gap-2 rounded-lg border bg-muted/25 p-3"
            data-legend-item={status}
          >
            <StatusBadge status={status} className="shrink-0" />
            <span className="text-xs leading-5 text-muted-foreground">{description}</span>
          </li>
        ))}
        <li
          className="flex min-w-0 items-start gap-2 rounded-lg border bg-muted/25 p-3"
          data-legend-item="unknown"
        >
          <RegistryStatusBadge status={null} />
          <span className="text-xs leading-5 text-muted-foreground">
            Kein bekannter Registry-Zustand
          </span>
        </li>
      </ul>
    </section>
  );
}
