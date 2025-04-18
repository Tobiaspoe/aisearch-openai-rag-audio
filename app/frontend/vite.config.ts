import { fileURLToPath } from "url";
import path from "path";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// Fix __dirname for ESM
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

export default defineConfig({
    plugins: [react()],
    build: {
        outDir: "../backend/static",
        emptyOutDir: true,
        sourcemap: true
    },
    resolve: {
        preserveSymlinks: true,
        alias: {
            "@": path.resolve(__dirname, "./src")
        }
    },
    server: {
        proxy: {
            "/realtime": {
                target: "ws://localhost:8765",
                ws: true,
                rewriteWsOrigin: true
            },
            "/chat": {
                target: "http://localhost:8000",
                changeOrigin: true,
                secure: false
            }
        }
    }
});
