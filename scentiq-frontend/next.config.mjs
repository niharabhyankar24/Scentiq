/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "https://scentiq-production.up.railway.app/api/:path*"
      }
    ]
  }
}

export default nextConfig

