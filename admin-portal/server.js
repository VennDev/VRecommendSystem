/**
 * VRecommendation Admin Portal Server
 *
 * This server ONLY binds to 127.0.0.1 (localhost) for security.
 * It provides a web interface to manage SuperAdmin features like email whitelist.
 *
 * WARNING: This server is intentionally NOT accessible from LAN or external networks.
 */

const express = require("express");
const path = require("path");

const app = express();

// Configuration
const PORT = process.env.ADMIN_PORTAL_PORT || 3456;
const HOST = "127.0.0.1"; // ONLY localhost - DO NOT CHANGE THIS!

// List of possible API server URLs to try (in order of priority)
const API_SERVER_URLS = [
    process.env.API_SERVER_URL,
    "http://localhost:2030",
    "http://127.0.0.1:2030",
    "http://host.docker.internal:2030",
].filter(Boolean);

let activeApiUrl = API_SERVER_URLS[0];

// Dynamic import for node-fetch (ESM module)
let fetch;
(async () => {
    fetch = (await import("node-fetch")).default;
})();

// Middleware
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(express.static(path.join(__dirname, "public")));

// Security middleware - double check localhost only
app.use((req, res, next) => {
    const clientIP = req.ip || req.connection.remoteAddress;
    const isLocalhost =
        clientIP === "127.0.0.1" ||
        clientIP === "::1" ||
        clientIP === "::ffff:127.0.0.1";

    if (!isLocalhost) {
        console.warn(`[SECURITY] Blocked access attempt from: ${clientIP}`);
        return res.status(403).json({
            error: "Access denied. This portal is only accessible from localhost.",
        });
    }
    next();
});

// Logging middleware
app.use((req, res, next) => {
    console.log(`[${new Date().toISOString()}] ${req.method} ${req.path}`);
    next();
});

// Helper function to make API requests with fallback URLs
async function apiRequest(endpoint, options = {}) {
    const errors = [];

    for (const baseUrl of API_SERVER_URLS) {
        try {
            const url = `${baseUrl}${endpoint}`;
            const response = await fetch(url, {
                ...options,
                headers: {
                    Host: "localhost",
                    "Content-Type": "application/json",
                    ...options.headers,
                },
                timeout: 5000,
            });

            // If successful, update active URL
            if (response.ok || response.status < 500) {
                activeApiUrl = baseUrl;
                return response;
            }
        } catch (error) {
            errors.push({ url: baseUrl, error: error.message });
        }
    }

    throw new Error(
        `All API servers unreachable. Tried: ${errors.map((e) => `${e.url} (${e.error})`).join(", ")}`,
    );
}

// ============== API PROXY ROUTES ==============

// Proxy whitelist list request
app.get("/api/whitelist", async (req, res) => {
    try {
        const response = await apiRequest("/api/v1/local/whitelist/list");
        const data = await response.json();
        res.json(data);
    } catch (error) {
        console.error("Error fetching whitelist:", error.message);
        res.status(500).json({
            error: "Failed to fetch whitelist: " + error.message,
        });
    }
});

// Proxy add email request
app.post("/api/whitelist/add", async (req, res) => {
    try {
        const response = await apiRequest("/api/v1/local/whitelist/add", {
            method: "POST",
            body: JSON.stringify(req.body),
        });
        const data = await response.json();
        res.json(data);
    } catch (error) {
        console.error("Error adding email:", error.message);
        res.status(500).json({
            error: "Failed to add email: " + error.message,
        });
    }
});

// Proxy check email request
app.post("/api/whitelist/check", async (req, res) => {
    try {
        const response = await apiRequest("/api/v1/local/whitelist/check", {
            method: "POST",
            body: JSON.stringify(req.body),
        });
        const data = await response.json();
        res.json(data);
    } catch (error) {
        console.error("Error checking email:", error.message);
        res.status(500).json({
            error: "Failed to check email: " + error.message,
        });
    }
});

// Proxy update email request
app.put("/api/whitelist/:id", async (req, res) => {
    try {
        const response = await apiRequest(
            `/api/v1/local/whitelist/${req.params.id}`,
            {
                method: "PUT",
                body: JSON.stringify(req.body),
            },
        );
        const data = await response.json();
        res.json(data);
    } catch (error) {
        console.error("Error updating email:", error.message);
        res.status(500).json({
            error: "Failed to update email: " + error.message,
        });
    }
});

// Proxy delete email request
app.delete("/api/whitelist/:id", async (req, res) => {
    try {
        const response = await apiRequest(
            `/api/v1/local/whitelist/${req.params.id}`,
            {
                method: "DELETE",
            },
        );
        const data = await response.json();
        res.json(data);
    } catch (error) {
        console.error("Error deleting email:", error.message);
        res.status(500).json({
            error: "Failed to delete email: " + error.message,
        });
    }
});

// Health check endpoint
app.get("/api/health", (req, res) => {
    res.json({
        status: "ok",
        server: "Admin Portal",
        timestamp: new Date().toISOString(),
        activeApiUrl: activeApiUrl,
        availableUrls: API_SERVER_URLS,
    });
});

// Check API server connection - tries all URLs
app.get("/api/check-connection", async (req, res) => {
    const results = [];
    let connected = false;
    let successResponse = null;

    for (const baseUrl of API_SERVER_URLS) {
        try {
            const response = await fetch(`${baseUrl}/api/v1/ping`, {
                method: "GET",
                headers: { Host: "localhost" },
                timeout: 3000,
            });
            const data = await response.json();

            if (response.ok) {
                connected = true;
                activeApiUrl = baseUrl;
                successResponse = data;
                results.push({
                    url: baseUrl,
                    status: "connected",
                    response: data,
                });
                break; // Found a working server
            } else {
                results.push({
                    url: baseUrl,
                    status: "error",
                    code: response.status,
                });
            }
        } catch (error) {
            results.push({
                url: baseUrl,
                status: "unreachable",
                error: error.message,
            });
        }
    }

    res.json({
        connected,
        activeApiServer: connected ? activeApiUrl : null,
        response: successResponse,
        attempts: results,
    });
});

// Serve main page
app.get("/", (req, res) => {
    res.sendFile(path.join(__dirname, "public", "index.html"));
});

// Start server - ONLY on localhost!
app.listen(PORT, HOST, () => {
    console.log("");
    console.log("========================================================");
    console.log("   VRecommendation Admin Portal - LOCALHOST ONLY");
    console.log("========================================================");
    console.log("");
    console.log(`   Portal URL     : http://${HOST}:${PORT}`);
    console.log(`   API Server URLs: ${API_SERVER_URLS.join(", ")}`);
    console.log("");
    console.log("   Security Notice:");
    console.log("   - This portal is ONLY accessible from localhost");
    console.log("   - It cannot be accessed from LAN or external networks");
    console.log("");
    console.log("========================================================");
    console.log("");
});
