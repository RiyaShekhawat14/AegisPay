/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Minimal production image for Docker (backend/ai-runtime already containerized).
  output: "standalone",
};
export default nextConfig;
