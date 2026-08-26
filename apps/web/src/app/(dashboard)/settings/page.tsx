"use client";

import { LogOut } from "lucide-react";
import { PageHeader } from "@/components/shared/page-header";
import { InlineError } from "@/components/shared/inline-error";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { AuditLogTable } from "@/components/settings/audit-log-table";
import { useAuth } from "@/hooks/use-auth";
import { useAuditLog } from "@/hooks/use-audit-log";
import { getRoleLabel } from "@/lib/status";

export default function SettingsPage() {
  const { user, loading, error, refetch, logout } = useAuth();
  const isAdmin = user?.role === "admin";
  const audit = useAuditLog(100, isAdmin);

  return (
    <div className="flex flex-col gap-8">
      <PageHeader title="Settings" description="Your account and platform activity." />

      <section>
        <h2 className="mb-3 text-sm font-semibold">Account</h2>
        {error ? (
          <InlineError message={error} onRetry={refetch} />
        ) : loading || !user ? (
          <Skeleton className="h-40 rounded-xl" />
        ) : (
          <Card>
            <CardHeader>
              <CardTitle className="text-base">{user.full_name || user.email}</CardTitle>
            </CardHeader>
            <CardContent className="flex flex-col gap-4">
              <div className="grid grid-cols-2 gap-4 text-sm sm:grid-cols-3">
                <div>
                  <div className="text-xs text-muted-foreground">Email</div>
                  <div className="mt-0.5 font-medium">{user.email}</div>
                </div>
                <div>
                  <div className="text-xs text-muted-foreground">Role</div>
                  <div className="mt-0.5">
                    <Badge variant="secondary" className="font-normal">
                      {getRoleLabel(user.role)}
                    </Badge>
                  </div>
                </div>
                <div>
                  <div className="text-xs text-muted-foreground">Status</div>
                  <div className="mt-0.5 font-medium">
                    {user.is_active ? "Active" : "Inactive"}
                  </div>
                </div>
              </div>
              <div>
                <Button variant="outline" size="sm" onClick={logout}>
                  <LogOut className="size-4" />
                  Sign out
                </Button>
              </div>
            </CardContent>
          </Card>
        )}
      </section>

      {isAdmin ? (
        <section>
          <h2 className="mb-3 text-sm font-semibold">Audit log</h2>
          <AuditLogTable
            entries={audit.data}
            loading={audit.initialLoading}
            error={audit.error}
            onRetry={audit.refetch}
          />
        </section>
      ) : null}
    </div>
  );
}
