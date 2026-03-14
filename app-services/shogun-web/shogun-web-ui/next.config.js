/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  // Forward /api/* to the shogun-web-api backend during dev
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${process.env.NEXT_PUBLIC_API_URL || "http://shogun-api.ibbytech.com"}/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;
