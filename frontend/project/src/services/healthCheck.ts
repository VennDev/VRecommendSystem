export interface ServerHealth {
  name: string;
  status: 'healthy' | 'unhealthy' | 'unknown';
  responseTime?: number;
  lastChecked: Date;
  error?: string;
}

const AI_SERVER_URL = 'http://localhost:9999';
const API_SERVER_URL = 'http://localhost:2030';

export const healthCheckService = {
  async checkAiServer(): Promise<ServerHealth> {
    const startTime = Date.now();
    try {
      const response = await fetch(`${AI_SERVER_URL}/health`, {
        method: 'GET',
        headers: { 'Accept': 'application/json' },
      });

      const responseTime = Date.now() - startTime;

      if (response.ok) {
        return {
          name: 'AI Server',
          status: 'healthy',
          responseTime,
          lastChecked: new Date(),
        };
      } else {
        return {
          name: 'AI Server',
          status: 'unhealthy',
          responseTime,
          lastChecked: new Date(),
          error: `HTTP ${response.status}`,
        };
      }
    } catch (error) {
      return {
        name: 'AI Server',
        status: 'unhealthy',
        responseTime: Date.now() - startTime,
        lastChecked: new Date(),
        error: error instanceof Error ? error.message : 'Connection failed',
      };
    }
  },

  async checkApiServer(): Promise<ServerHealth> {
    const startTime = Date.now();
    try {
      const response = await fetch(`${API_SERVER_URL}/api/v1/ping`, {
        method: 'GET',
        headers: { 'Accept': 'application/json' },
      });

      const responseTime = Date.now() - startTime;

      if (response.ok) {
        return {
          name: 'API Server',
          status: 'healthy',
          responseTime,
          lastChecked: new Date(),
        };
      } else {
        return {
          name: 'API Server',
          status: 'unhealthy',
          responseTime,
          lastChecked: new Date(),
          error: `HTTP ${response.status}`,
        };
      }
    } catch (error) {
      return {
        name: 'API Server',
        status: 'unhealthy',
        responseTime: Date.now() - startTime,
        lastChecked: new Date(),
        error: error instanceof Error ? error.message : 'Connection failed',
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
