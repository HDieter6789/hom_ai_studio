"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { getToken } from "@/lib/api";

/**
 * Client-side guard for the authenticated app shell. If there is no JWT in
 * localStorage at all we redirect straight to /login (an expired/invalid
 * token is instead handled by the API client's global 401 handler, since
 * only the backend can tell us that).
 */
export function AuthGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [checked, setChecked] = React.useState(false);

  React.useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    // Deliberately deferred to after mount: both the server render and the
    // very first client render must return `null` so hydration has nothing
    // to reconcile (reading localStorage on the server is impossible, so
    // rendering `children` synchronously here would mismatch the SSR
    // output). The extra render this causes is the intended trade-off.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setChecked(true);
  }, [router]);

  if (!checked) {
    return null;
  }

  return <>{children}</>;
}
