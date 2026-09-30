/** @type {import('next').NextConfig} */
const nextConfig = {
  // Small, self-contained image for Docker/k8s.
  output: "standalone",
  // NOTE: API proxying is done by the runtime route handler at
  // app/api/[...path]/route.ts, NOT by next.config rewrites — rewrites are
  // resolved at build time and would bake in the wrong API address.
};

module.exports = nextConfig;
