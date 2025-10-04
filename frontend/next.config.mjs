/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  reactStrictMode: true,
  env: {
    API_BASE_URL: process.env.API_BASE_URL || 'http://localhost:8001',
    OLAP_API_URL: process.env.OLAP_API_URL || 'http://localhost:8004',
    GRAFANA_URL: process.env.GRAFANA_URL || 'http://localhost:3000',
  },
};

export default nextConfig;
