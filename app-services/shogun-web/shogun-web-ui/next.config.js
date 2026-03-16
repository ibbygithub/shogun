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
  // Allow Windy embed iframe (used by WindyRadar component)
  async headers() {
    return [
      {
        source: "/(.*)",
        headers: [
          {
            key: "Content-Security-Policy",
            value: "frame-src 'self' https://embed.windy.com;",
          },
        ],
      },
    ];
  },
};

module.exports = nextConfig;
