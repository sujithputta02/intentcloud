import type { NextConfig } from "next";

const backendUrl = process.env.API_PROXY_URL || "http://localhost:8000";

const nextConfig: NextConfig = {
  // Legacy rewrites removed in favor of robust app/api/[...path]/route.ts proxy
};

export default nextConfig;
