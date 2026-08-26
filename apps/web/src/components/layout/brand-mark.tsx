import Link from "next/link";
import { cn } from "@/lib/utils";

export function BrandMark({ className }: { className?: string }) {
  return (
    <Link href="/" className={cn("flex items-center gap-2.5", className)}>
      <span className="flex size-7 shrink-0 items-center justify-center rounded-md bg-foreground text-background text-sm font-bold">
        H
      </span>
      <span className="flex flex-col leading-none">
        <span className="text-sm font-semibold tracking-tight">H.O.M AI Studio</span>
        <span className="text-[11px] text-muted-foreground">CRM Model Platform</span>
      </span>
    </Link>
  );
}
