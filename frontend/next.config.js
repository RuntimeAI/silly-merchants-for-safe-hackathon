/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    return [
      {
        source: '/merchants_1o1/:path*',
        destination: 'http://localhost:8000/merchants_1o1/:path*',
      },
    ];
  },
};

module.exports = nextConfig; 