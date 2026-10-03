/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: false,
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'https://bidverify-backend-7frs.onrender.com/api/:path*',
      },
    ];
  },
};

module.exports = nextConfig;
