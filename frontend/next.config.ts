/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  webpack: (config: any) => {
    // Fix for 'canvas' module in React Three Fiber
    config.externals = config.externals || {};
    config.externals['canvas'] = 'commonjs canvas';
    return config;
  },
};

export default nextConfig;
