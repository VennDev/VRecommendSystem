const LOGS_STORAGE_KEY = 'vrecom_activity_logs';

interface ActivityLogData {
  action: string;
  resourceType?: string;
  resourceId?: string;
  details?: Record<string, any>;
}

interface ActivityLog {
  id: string;
  user_id: string;
  user_email: string;
  action: string;
  resource_type?: string;
  resource_id?: string;
  details: Record<string, any>;
  user_agent: string;
  created_at: string;
}

interface LogsByDate {
  [date: string]: ActivityLog[];
}

const getTodayDateKey = () => {
  const today = new Date();
  return today.toISOString().split('T')[0];
};

const loadLogsFromStorage = (): LogsByDate => {
  try {
    const stored = localStorage.getItem(LOGS_STORAGE_KEY);
    return stored ? JSON.parse(stored) : {};
  } catch (error) {
    console.error('Failed to load logs from storage:', error);
    return {};
  }
};

const saveLogsToStorage = (logs: LogsByDate) => {
  try {
    localStorage.setItem(LOGS_STORAGE_KEY, JSON.stringify(logs));
  } catch (error) {
    console.error('Failed to save logs to storage:', error);
  }
};

export const activityLogger = {
  async log(userId: string, userEmail: string, data: ActivityLogData) {
    try {
      const dateKey = getTodayDateKey();
      const allLogs = loadLogsFromStorage();

      if (!allLogs[dateKey]) {
        allLogs[dateKey] = [];
      }

      const logEntry: ActivityLog = {
        id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        user_id: userId,
        user_email: userEmail,
        action: data.action,
        resource_type: data.resourceType,
        resource_id: data.resourceId,
        details: data.details || {},
        user_agent: navigator.userAgent,
        created_at: new Date().toISOString(),
      };

      allLogs[dateKey].push(logEntry);
      saveLogsToStorage(allLogs);
    } catch (error) {
      console.error('Activity logger error:', error);
    }
  },

  async getRecentLogs(userId: string, limit: number = 50): Promise<ActivityLog[]> {
    try {
      const allLogs = loadLogsFromStorage();
      const allLogEntries: ActivityLog[] = [];

      // Get all logs sorted by date (newest first)
      const sortedDates = Object.keys(allLogs).sort().reverse();

      for (const date of sortedDates) {
        const dayLogs = allLogs[date].filter(log => log.user_id === userId);
        allLogEntries.push(...dayLogs);
      }

      // Sort by created_at descending and limit
      return allLogEntries
        .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
        .slice(0, limit);
    } catch (error) {
      console.error('Failed to fetch activity logs:', error);
      return [];
    }
  },

  async getLogsByResource(resourceType: string, resourceId: string, limit: number = 20): Promise<ActivityLog[]> {
    try {
      const allLogs = loadLogsFromStorage();
      const allLogEntries: ActivityLog[] = [];

      const sortedDates = Object.keys(allLogs).sort().reverse();

      for (const date of sortedDates) {
        const dayLogs = allLogs[date].filter(
          log => log.resource_type === resourceType && log.resource_id === resourceId
        );
        allLogEntries.push(...dayLogs);
      }

      return allLogEntries
        .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
        .slice(0, limit);
    } catch (error) {
      console.error('Failed to fetch resource logs:', error);
      return [];
    }
  },

  async exportLogsAsJson(): Promise<string> {
    const allLogs = loadLogsFromStorage();
    return JSON.stringify(allLogs, null, 2);
  },

  downloadLogsAsFile() {
    const allLogs = loadLogsFromStorage();
    const json = JSON.stringify(allLogs, null, 2);
    const blob = new Blob([json], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `activity-logs-${getTodayDateKey()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  },

  async clearOldLogs(daysToKeep: number = 30) {
    try {
      const allLogs = loadLogsFromStorage();
      const cutoffDate = new Date();
      cutoffDate.setDate(cutoffDate.getDate() - daysToKeep);
      const cutoffDateKey = cutoffDate.toISOString().split('T')[0];

      const filteredLogs: LogsByDate = {};
      for (const [date, logs] of Object.entries(allLogs)) {
        if (date >= cutoffDateKey) {
          filteredLogs[date] = logs;
        }
      }

      saveLogsToStorage(filteredLogs);
    } catch (error) {
      console.error('Failed to clear old logs:', error);
    }
  },
};
