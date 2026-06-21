/** @type {import('next').NextConfig} */
const nextConfig = {
  // Emit a minimal standalone server for a slim production image.
  output: "standalone",
  reactStrictMode: true,
};

export default nextConfig;
