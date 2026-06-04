import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Emit a self-contained server bundle (.next/standalone) so the Docker runtime
  // image needs no node_modules and no install step.
  output: "standalone",
};

export default nextConfig;
