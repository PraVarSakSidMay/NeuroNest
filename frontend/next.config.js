/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  serverExternalPackages: ['@vladmandic/face-api'],
  webpack: (config) => {
    // Suppress face-api critical dependency warnings
    config.ignoreWarnings = config.ignoreWarnings || [];
    config.ignoreWarnings.push(
      { module: /@vladmandic\/face-api/ },
      { message: /Critical dependency: require function is used/ }
    );

    // SVG handling
    config.module.rules.push({
      test: /\.svg$/i,
      issuer: /\.[jt]sx?$/,
      use: ['@svgr/webpack'],
    });

    return config;
  },
};

export default nextConfig;