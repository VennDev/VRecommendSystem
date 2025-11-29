import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// https://vitejs.dev/config/
export default defineConfig({
    plugins: [react()],
    optimizeDeps: {
        exclude: ["lucide-react"],
    },
    server: {
        // Allow access from LAN devices
        host: "0.0.0.0",
        port: 5173,
        // Allow all origins for development
        cors: true,
        // Watch for file changes
        watch: {
            usePolling: true,
        },
    },
    preview: {
        // Also allow LAN access in preview mode
        host: "0.0.0.0",
        port: 5173,
    },
});
