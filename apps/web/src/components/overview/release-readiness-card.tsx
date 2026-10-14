import Link from "next/link";
import {
  ArrowRight,
  CalendarDays,
  CheckCircle2,
  ClipboardCheck,
  Database,
  FlaskConical,
  Rocket,
  ShieldCheck,
} from "lucide-react";

import {
  Card,
  CardAction,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

const releaseChecks = [
  {
    label: "Dataset package",
    detail: "Conversation JSONL accepted and ready for training.",
    icon: Database,
  },
  {
    label: "Training queue",
    detail: "Jobs can be created; GPU execution remains infrastructure gated.",
    icon: FlaskConical,
  },
  {
    label: "Production smoke",
    detail: "Overview marker confirms the deployed frontend revision.",
    icon: Rocket,
  },
];

export function ReleaseReadinessCard() {
  return (
    <Card className="border-emerald-500/25 bg-gradient-to-br from-emerald-500/10 via-card to-sky-500/10">
      <CardHeader className="gap-2">
        <div className="flex flex-wrap items-center gap-2">
          <Badge className="bg-emerald-600 text-white hover:bg-emerald-600">
            <CheckCircle2 data-icon="inline-start" />
            Ready for founder smoke
          </Badge>
          <Badge variant="outline" className="bg-background/70">
            <CalendarDays data-icon="inline-start" />
            AI Studio Daily 2026-10-14
          </Badge>
        </div>
        <CardTitle className="text-lg">Release readiness</CardTitle>
        <CardDescription>
          Current H.O.M AI Studio handoff path from dataset intake through training queue and
          production verification.
        </CardDescription>
        <CardAction>
          <ShieldCheck className="size-5 text-emerald-600" aria-hidden="true" />
        </CardAction>
      </CardHeader>

      <CardContent className="grid gap-5 lg:grid-cols-[1fr_auto] lg:items-end">
        <div className="grid gap-3">
          <div className="flex items-center justify-between gap-3 rounded-lg border border-emerald-500/20 bg-emerald-500/5 px-3 py-2">
            <div>
              <p className="text-xs font-medium uppercase tracking-wide text-emerald-700 dark:text-emerald-300">
                Today&apos;s release lane
              </p>
              <p className="text-sm text-muted-foreground">
                Dataset, training, registry, and deployment checks are ready for review.
              </p>
            </div>
            <CheckCircle2 className="size-5 shrink-0 text-emerald-600" aria-hidden="true" />
          </div>

          <div className="grid gap-3 sm:grid-cols-3">
            {releaseChecks.map((check) => {
              const Icon = check.icon;
              return (
                <div key={check.label} className="rounded-lg border bg-background/75 p-3">
                  <div className="flex items-center gap-2 text-sm font-medium">
                    <Icon className="size-4 text-emerald-600" aria-hidden="true" />
                    {check.label}
                  </div>
                  <p className="mt-2 text-xs leading-5 text-muted-foreground">{check.detail}</p>
                </div>
              );
            })}
          </div>
        </div>

        <Button asChild variant="outline" className="w-full bg-background/80 sm:w-auto">
          <Link href="/datasets">
            <ClipboardCheck data-icon="inline-start" />
            Review datasets
            <ArrowRight data-icon="inline-end" />
          </Link>
        </Button>
      </CardContent>
    </Card>
  );
}
