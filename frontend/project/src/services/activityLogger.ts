import { supabase, ActivityLog } from '../lib/supabase';

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

export const activityLogger = {
  async log(userId: string, userEmail: string, data: ActivityLogData) {
    try {
      const logEntry: Omit<ActivityLog, 'id' | 'created_at'> = {
        user_id: userId,
        user_email: userEmail,
        action: data.action,
        resource_type: data.resourceType,
        resource_id: data.resourceId,
        details: data.details || {},
        user_agent: navigator.userAgent,
      };

      const { error } = await supabase
        .from('activity_logs')
        .insert([logEntry]);

      if (error) {
        console.error('Failed to insert activity log:', error);
      }
    } catch (error) {
      console.error('Activity logger error:', error);
    }
  },

  async getRecentLogs(userId: string, limit: number = 50): Promise<ActivityLog[]> {
    try {
      const { data, error } = await supabase
        .from('activity_logs')
        .select('*')
        .eq('user_id', userId)
        .order('created_at', { ascending: false })
        .limit(limit);

      if (error) {
        console.error('Failed to fetch activity logs:', error);
        return [];
      }

      return data || [];
    } catch (error) {
      console.error('Failed to fetch activity logs:', error);
      return [];
    }
  },

  async getAllRecentLogs(limit: number = 50): Promise<ActivityLog[]> {
    try {
      const { data, error } = await supabase
        .from('activity_logs')
        .select('*')
        .order('created_at', { ascending: false })
        .limit(limit);

      if (error) {
        console.error('Failed to fetch all activity logs:', error);
        return [];
      }

      return data || [];
    } catch (error) {
      console.error('Failed to fetch all activity logs:', error);
      return [];
    }
  },

  async getLogsByResource(resourceType: string, resourceId: string, limit: number = 20): Promise<ActivityLog[]> {
    try {
      const { data, error } = await supabase
        .from('activity_logs')
        .select('*')
        .eq('resource_type', resourceType)
        .eq('resource_id', resourceId)
        .order('created_at', { ascending: false })
        .limit(limit);

      if (error) {
        console.error('Failed to fetch resource logs:', error);
        return [];
      }

      return data || [];
    } catch (error) {
      console.error('Failed to fetch resource logs:', error);
      return [];
    }
  },

  async exportLogsAsJson(userId?: string): Promise<string> {
    try {
      let query = supabase
        .from('activity_logs')
        .select('*')
        .order('created_at', { ascending: false });

      if (userId) {
        query = query.eq('user_id', userId);
      }

      const { data, error } = await query;

      if (error) {
        console.error('Failed to export logs:', error);
        return '{}';
      }

      return JSON.stringify(data || [], null, 2);
    } catch (error) {
      console.error('Failed to export logs:', error);
      return '{}';
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

  async clearOldLogs(daysToKeep: number = 30) {
    try {
      const cutoffDate = new Date();
      cutoffDate.setDate(cutoffDate.getDate() - daysToKeep);

      const { error } = await supabase
        .from('activity_logs')
        .delete()
        .lt('created_at', cutoffDate.toISOString());

      if (error) {
        console.error('Failed to clear old logs:', error);
      }
    } catch (error) {
      console.error('Failed to clear old logs:', error);
    }
  },
};
