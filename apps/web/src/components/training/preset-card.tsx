import { Check } from "lucide-react";
import { cn } from "@/lib/utils";
import type { PresetInfo } from "@/config/training-presets";

interface PresetCardProps {
  preset: PresetInfo;
  selected: boolean;
  onSelect: () => void;
}

export function PresetCard({ preset, selected, onSelect }: PresetCardProps) {
  return (
    <button
      type="button"
      onClick={onSelect}
      className={cn(
        "relative flex flex-col items-start gap-1.5 rounded-lg border p-4 text-left transition-colors",
        selected
          ? "border-primary ring-1 ring-primary bg-accent/40"
          : "hover:bg-accent/30",
      )}
    >
      {selected ? (
        <span className="absolute top-3 right-3 flex size-4 items-center justify-center rounded-full bg-primary text-primary-foreground">
          <Check className="size-2.5" />
        </span>
      ) : null}
      <span className="text-xs font-medium text-muted-foreground">{preset.badge}</span>
      <span className="text-sm font-semibold">{preset.title}</span>
      <span className="text-xs text-muted-foreground">{preset.description}</span>
    </button>
  );
}
