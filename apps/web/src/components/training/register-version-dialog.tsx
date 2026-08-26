"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { Loader2, Library } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ApiError, registerModelVersion } from "@/lib/api";

interface RegisterVersionDialogProps {
  trainingJobId: string;
}

export function RegisterVersionDialog({ trainingJobId }: RegisterVersionDialogProps) {
  const router = useRouter();
  const [open, setOpen] = React.useState(false);
  const [modelName, setModelName] = React.useState("HOM-CRM");
  const [submitting, setSubmitting] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const version = await registerModelVersion({
        training_job_id: trainingJobId,
        model_name: modelName,
      });
      toast.success(`Registered as ${version.display_name}`);
      setOpen(false);
      router.push(`/registry?model_name=${encodeURIComponent(version.model_name)}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to register version.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button size="sm">
          <Library className="size-4" />
          Register to Model Registry
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-sm">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>Register model version</DialogTitle>
            <DialogDescription>
              Creates a new version under this model name in the registry.
            </DialogDescription>
          </DialogHeader>
          <div className="mt-4 flex flex-col gap-1.5">
            <Label htmlFor="register-model-name">Model name</Label>
            <Input
              id="register-model-name"
              value={modelName}
              onChange={(e) => setModelName(e.target.value)}
              required
            />
          </div>
          {error ? (
            <p className="mt-3 rounded-md bg-red-500/10 px-3 py-2 text-sm text-red-600 dark:text-red-400">
              {error}
            </p>
          ) : null}
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => setOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={submitting}>
              {submitting ? <Loader2 className="size-4 animate-spin" /> : null}
              Register
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
