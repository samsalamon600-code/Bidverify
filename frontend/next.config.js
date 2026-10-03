/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: false,
  async rewrites() {
    return {
      beforeFiles: [
        {
          source: '/:path*',
          destination: 'https://bidverify-backend-7frs.onrender.com/:path*',
        },
      ],
    };
  },
};

module.exports = nextConfig;
