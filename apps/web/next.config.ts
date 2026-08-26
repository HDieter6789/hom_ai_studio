import type { NextConfig } from "next";
import path from "node:path";

const nextConfig: NextConfig = {
  // Pin the file-tracing root to this app directory. Without this, Next.js
  // walks up looking for a lockfile and can pick up an unrelated one outside
  // the repo (e.g. in the user's home directory on Windows), which just
  // produces a harmless but noisy warning during build.
  outputFileTracingRoot: path.join(__dirname),
};

export default nextConfig;
