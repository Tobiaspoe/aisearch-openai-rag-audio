import path from "path";
import { fileURLToPath } from "url";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// Only needed in ESM environments (e.g., if "type": "module" is set in package.json)
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

export default defineConfig({
  plugins: [react()],
  build: {
    outDir: "../backend/static",
    emptyOutDir: true,
    sourcemap: true,
  },
  resolve: {
    preserveSymlinks: true,
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    proxy: {
      "/realtime": {
        target: "ws://localhost:8765",
        ws: true,
        rewriteWsOrigin: true,
      },
      "/chat": {
        target: "http://localhost:8765",
        changeOrigin: true,
        secure: false,
      },
      "/realtime/transcribe": {
        target: "http://localhost:8765",
        changeOrigin: true,
        secure: false,
      },
    },
  },
});
