import path from "path";
import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  build: {
    assetsDir: "static",
    rollupOptions: {
      output: {
        entryFileNames: "static/[name].js",
        chunkFileNames: "static/[name].js",
        assetFileNames: "static/[name].[ext]",
      },
    },
  },
});
