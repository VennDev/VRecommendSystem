import { API_CONFIG } from "../config/api";

export interface ServerHealth {
    name: string;
    status: "healthy" | "unhealthy" | "unknown";
    responseTime?: number;
    lastChecked: Date;
    error?: string;
}

export const healthCheckService = {
    async checkAiServer(): Promise<ServerHealth> {
        const startTime = Date.now();
        try {
            const token = localStorage.getItem("auth_token");
            const headers: HeadersInit = { Accept: "application/json" };

            if (token) {
                headers["Authorization"] = `Bearer ${token}`;
            }

            const response = await fetch(
                `${API_CONFIG.AI_SERVER_URL}/api/v1/health`,
                {
                    method: "GET",
                    headers,
                },
            );

            const responseTime = Date.now() - startTime;

            if (response.status === 401) {
                console.warn("Health check received 401, token expired");
                localStorage.removeItem("auth_token");
                localStorage.removeItem("user");
                window.location.href = "/login";
            }

            if (response.ok) {
                return {
                    name: "AI Server",
                    status: "healthy",
                    responseTime,
                    lastChecked: new Date(),
                };
            } else {
                return {
                    name: "AI Server",
                    status: "unhealthy",
                    responseTime,
                    lastChecked: new Date(),
                    error: `HTTP ${response.status}`,
                };
            }
        } catch (error) {
            return {
                name: "AI Server",
                status: "unhealthy",
                responseTime: Date.now() - startTime,
                lastChecked: new Date(),
                error:
                    error instanceof Error
                        ? error.message
                        : "Connection failed",
            };
        }
    },

    async checkApiServer(): Promise<ServerHealth> {
        const startTime = Date.now();
        try {
            const response = await fetch(
                `${API_CONFIG.AUTH_SERVER_URL}/api/v1/ping`,
                {
                    method: "GET",
                    headers: { Accept: "application/json" },
                },
            );

            const responseTime = Date.now() - startTime;

            if (response.ok) {
                return {
                    name: "API Server",
                    status: "healthy",
                    responseTime,
                    lastChecked: new Date(),
                };
            } else {
                return {
                    name: "API Server",
                    status: "unhealthy",
                    responseTime,
                    lastChecked: new Date(),
                    error: `HTTP ${response.status}`,
                };
            }
        } catch (error) {
            return {
                name: "API Server",
                status: "unhealthy",
                responseTime: Date.now() - startTime,
                lastChecked: new Date(),
                error:
                    error instanceof Error
                        ? error.message
                        : "Connection failed",
            };
        }
    },

    async checkAllServers(): Promise<ServerHealth[]> {
        const [aiServer, apiServer] = await Promise.all([
            this.checkAiServer(),
            this.checkApiServer(),
        ]);

        return [aiServer, apiServer];
    },
};
