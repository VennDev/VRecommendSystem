import { API_CONFIG, API_ENDPOINTS, buildAuthUrl } from '../config/api';

export interface ActivityLog {
  id?: string;
  user_id: string;
  user_email: string;
  action: string;
  resource_type?: string;
  resource_id?: string;
  details: Record<string, any>;
  user_agent: string;
  ip_address?: string;
  created_at?: string;
}

interface ActivityLogData {
  action: string;
  resourceType?: string;
  resourceId?: string;
  details?: Record<string, any>;
}

const getTodayDateKey = () => {
  const today = new Date();
  return today.toISOString().split('T')[0];
};

const fetchWithTimeout = async (url: string, options: RequestInit = {}) => {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), API_CONFIG.REQUEST_TIMEOUT);

  try {
    const response = await fetch(url, {
      ...options,
      ...API_CONFIG.REQUEST_OPTIONS,
      signal: controller.signal,
    });
    clearTimeout(timeout);
    return response;
  } catch (error) {
    clearTimeout(timeout);
    throw error;
  }
};

export const activityLogger = {
  async log(userId: string, userEmail: string, data: ActivityLogData) {
    try {
      const logEntry = {
        user_id: userId,
        user_email: userEmail,
        action: data.action,
        resource_type: data.resourceType,
        resource_id: data.resourceId,
        details: data.details || {},
        user_agent: navigator.userAgent,
      };

      const response = await fetchWithTimeout(
        buildAuthUrl(API_ENDPOINTS.ACTIVITY_LOGS.CREATE),
        {
          method: 'POST',
          headers: API_CONFIG.DEFAULT_HEADERS,
          body: JSON.stringify(logEntry),
        }
      );

      if (!response.ok) {
        console.error('Failed to create activity log:', response.statusText);
      }
    } catch (error) {
      console.error('Activity logger error:', error);
    }
  },

  async getRecentLogs(userId: string, limit: number = 50): Promise<ActivityLog[]> {
    try {
      const url = `${buildAuthUrl(API_ENDPOINTS.ACTIVITY_LOGS.GET_USER_LOGS)}?user_id=${userId}&limit=${limit}`;
      const response = await fetchWithTimeout(url);

      if (!response.ok) {
        console.error('Failed to fetch activity logs:', response.statusText);
        return [];
      }

      const result = await response.json();
      return result.data || [];
    } catch (error) {
      console.error('Failed to fetch activity logs:', error);
      return [];
    }
  },

  async getAllRecentLogs(limit: number = 50): Promise<ActivityLog[]> {
    try {
      const url = `${buildAuthUrl(API_ENDPOINTS.ACTIVITY_LOGS.GET_ALL_RECENT)}?limit=${limit}`;
      const response = await fetchWithTimeout(url);

      if (!response.ok) {
        console.error('Failed to fetch all activity logs:', response.statusText);
        return [];
      }

      const result = await response.json();
      return result.data || [];
    } catch (error) {
      console.error('Failed to fetch all activity logs:', error);
      return [];
    }
  },

  async getLogsByResource(resourceType: string, resourceId: string, limit: number = 20): Promise<ActivityLog[]> {
    try {
      const url = `${buildAuthUrl(API_ENDPOINTS.ACTIVITY_LOGS.GET_BY_RESOURCE)}?resource_type=${resourceType}&resource_id=${resourceId}&limit=${limit}`;
      const response = await fetchWithTimeout(url);

      if (!response.ok) {
        console.error('Failed to fetch resource logs:', response.statusText);
        return [];
      }

      const result = await response.json();
      return result.data || [];
    } catch (error) {
      console.error('Failed to fetch resource logs:', error);
      return [];
    }
  },

  async exportLogsAsJson(userId?: string): Promise<string> {
    try {
      const url = userId
        ? `${buildAuthUrl(API_ENDPOINTS.ACTIVITY_LOGS.EXPORT)}?user_id=${userId}`
        : buildAuthUrl(API_ENDPOINTS.ACTIVITY_LOGS.EXPORT);

      const response = await fetchWithTimeout(url);

      if (!response.ok) {
        console.error('Failed to export logs:', response.statusText);
        return '[]';
      }

      const data = await response.json();
      return JSON.stringify(data, null, 2);
    } catch (error) {
      console.error('Failed to export logs:', error);
      return '[]';
    }
  },

  async downloadLogsAsFile(userId?: string) {
    try {
      const json = await this.exportLogsAsJson(userId);
      const blob = new Blob([json], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `activity-logs-${getTodayDateKey()}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Failed to download logs:', error);
    }
  },
};
