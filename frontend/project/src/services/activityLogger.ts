import { createClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

const supabase = supabaseUrl && supabaseKey
  ? createClient(supabaseUrl, supabaseKey)
  : null;

interface ActivityLogData {
  action: string;
  resourceType?: string;
  resourceId?: string;
  details?: Record<string, any>;
}

export const activityLogger = {
  async log(userId: string, userEmail: string, data: ActivityLogData) {
    if (!supabase) {
      console.warn('Supabase not configured, skipping activity log');
      return;
    }

    try {
      const { error } = await supabase.from('activity_logs').insert({
        user_id: userId,
        user_email: userEmail,
        action: data.action,
        resource_type: data.resourceType,
        resource_id: data.resourceId,
        details: data.details || {},
        ip_address: null, // Could be populated from server-side
        user_agent: navigator.userAgent,
      });

      if (error) {
        console.error('Failed to log activity:', error);
      }
    } catch (error) {
      console.error('Activity logger error:', error);
    }
  },

  async getRecentLogs(userId: string, limit: number = 50) {
    if (!supabase) {
      return [];
    }

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

  async getLogsByResource(resourceType: string, resourceId: string, limit: number = 20) {
    if (!supabase) {
      return [];
    }

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
};
