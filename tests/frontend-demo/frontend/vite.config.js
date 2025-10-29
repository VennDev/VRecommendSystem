import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

// https://vitejs.dev/config/
export default defineConfig({
    plugins: [
        react({
            include: "**/*.{jsx,js}",
        }),
    ],
    esbuild: {
        loader: "jsx",
        include: /src\/.*\.(js|jsx)$/,
        exclude: [],
    },
    resolve: {
        alias: {
            "@": path.resolve(__dirname, "./src"),
            "@components": path.resolve(__dirname, "./src/components"),
            "@pages": path.resolve(__dirname, "./src/pages"),
            "@services": path.resolve(__dirname, "./src/services"),
            "@utils": path.resolve(__dirname, "./src/utils"),
            "@assets": path.resolve(__dirname, "./src/assets"),
        },
    },
    server: {
        port: 5173,
        host: true,
        cors: true,
        proxy: {
            "/api": {
                target: "http://localhost:3001",
                changeOrigin: true,
                secure: false,
            },
        },
    },
    build: {
        outDir: "dist",
        sourcemap: true,
        rollupOptions: {
            output: {
                manualChunks: {
                    vendor: ["react", "react-dom"],
                    router: ["react-router-dom"],
                    ui: ["framer-motion", "@headlessui/react", "lucide-react"],
                    utils: ["axios", "js-cookie", "clsx"],
                },
            },
        },
    },
    optimizeDeps: {
        include: ["react", "react-dom", "react-router-dom", "axios"],
    },
});
