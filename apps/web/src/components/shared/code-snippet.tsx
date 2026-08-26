"use client";

import * as React from "react";
import { Check, Copy } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface CodeSnippetProps {
  code: string;
  className?: string;
}

export function CodeSnippet({ code, className }: CodeSnippetProps) {
  const [copied, setCopied] = React.useState(false);

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 1600);
    } catch {
      // clipboard API unavailable; ignore silently
    }
  }

  return (
    <div className={cn("group relative rounded-lg border bg-muted/40", className)}>
      <pre className="overflow-x-auto p-4 text-xs leading-relaxed">
        <code>{code}</code>
      </pre>
      <Button
        variant="outline"
        size="icon"
        className="absolute top-2 right-2 size-7 bg-background/80 backdrop-blur-sm"
        onClick={handleCopy}
        aria-label="Copy to clipboard"
      >
        {copied ? <Check className="size-3.5" /> : <Copy className="size-3.5" />}
      </Button>
    </div>
  );
}
