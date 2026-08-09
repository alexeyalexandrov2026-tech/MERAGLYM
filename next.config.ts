import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: 'standalone',
  // Next traces pg-cloudflare under Node conditions, which resolve to dist/empty.js.
  // The Workers bundle is built with the "workerd" condition and needs the real entrypoints.
  outputFileTracingIncludes: {
    '**/*': [
      './node_modules/pg-cloudflare/dist/**',
      './node_modules/pg-cloudflare/esm/**',
    ],
  },
};

export default nextConfig;
