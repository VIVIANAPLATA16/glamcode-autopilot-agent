/** @type {import('next').NextConfig} */
const backendUrl = (
  process.env.BACKEND_URL || "http://47.251.39.38:5000"
).replace(/\/$/, "")

const nextConfig = {
  typescript: {
    ignoreBuildErrors: true,
  },
  images: {
    unoptimized: true,
  },
  // Proxy /api/* through Next (HTTPS same-origin) → Flask backend.
  // Avoids browser mixed-content blocks (HTTPS page → HTTP API).
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${backendUrl}/api/:path*`,
      },
    ]
  },
}

export default nextConfig
