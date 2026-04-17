import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  images: {
    remotePatterns: [
      // WG-Gesucht images
      { protocol: "https", hostname: "www.wg-gesucht.de" },
      { protocol: "https", hostname: "img.wg-gesucht.de" },
      // ImmoScout24
      { protocol: "https", hostname: "static.immoscout24.de" },
      { protocol: "https", hostname: "**.immobilienscout24.de" },
      // Placeholder
      { protocol: "https", hostname: "placehold.co" },
    ],
  },
};

export default nextConfig;
