import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Configuración para producción
  output: "standalone", // Mejor para despliegue en Vercel
  eslint: {
    // Solo ejecutar ESLint en producción si es necesario
    ignoreDuringBuilds: true,
  },
  typescript: {
    // Ignorar errores de TypeScript durante el build
    ignoreBuildErrors: true,
  },
  // Configuración de imágenes si es necesario
  images: {
    unoptimized: true, // Para simplificar el despliegue
  },
};

export default nextConfig;
