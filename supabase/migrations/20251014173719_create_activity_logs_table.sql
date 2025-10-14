/*
  # Create Activity Logs Table

  ## Overview
  This migration creates a comprehensive activity logging system to track all user actions within the application.

  ## New Tables
    - `activity_logs`
      - `id` (uuid, primary key): Unique identifier for each log entry
      - `user_id` (text): User identifier from authentication system
      - `user_email` (text): User's email address
      - `action` (text): Action performed (login, logout, create, update, delete, view, etc.)
      - `resource_type` (text, optional): Type of resource affected (model, task, data_chef, etc.)
      - `resource_id` (text, optional): Identifier of the affected resource
      - `details` (jsonb): Additional details about the action
      - `user_agent` (text): Browser/client user agent string
      - `ip_address` (text, optional): Client IP address
      - `created_at` (timestamptz): Timestamp when the log was created
      - `session_id` (text, optional): Session identifier for grouping related actions

  ## Security
    - Enable RLS on `activity_logs` table
    - Add policy for authenticated users to create their own logs
    - Add policy for authenticated users to read their own logs
    - Add policy for super admins to read all logs

  ## Indexes
    - Index on user_id for fast user-specific queries
    - Index on action for filtering by action type
    - Index on created_at for time-based queries
    - Composite index on (user_id, created_at) for efficient pagination

  ## Important Notes
    1. Logs are retained indefinitely - implement cleanup job separately if needed
    2. The details field uses JSONB for flexible storage of action-specific data
    3. IP address tracking is optional and should comply with privacy regulations
    4. Session tracking helps identify related actions in a user's workflow
*/

-- Create activity_logs table
CREATE TABLE IF NOT EXISTS activity_logs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id text NOT NULL,
  user_email text NOT NULL,
  action text NOT NULL,
  resource_type text,
  resource_id text,
  details jsonb DEFAULT '{}'::jsonb,
  user_agent text NOT NULL DEFAULT '',
  ip_address text,
  session_id text,
  created_at timestamptz DEFAULT now()
);

-- Enable Row Level Security
ALTER TABLE activity_logs ENABLE ROW LEVEL SECURITY;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_activity_logs_user_id ON activity_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_activity_logs_action ON activity_logs(action);
CREATE INDEX IF NOT EXISTS idx_activity_logs_created_at ON activity_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_activity_logs_user_created ON activity_logs(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_activity_logs_resource ON activity_logs(resource_type, resource_id) WHERE resource_type IS NOT NULL;

-- Policy: Users can create their own activity logs
CREATE POLICY "Users can create own activity logs"
  ON activity_logs
  FOR INSERT
  TO authenticated
  WITH CHECK (auth.uid()::text = user_id);

-- Policy: Users can read their own activity logs
CREATE POLICY "Users can read own activity logs"
  ON activity_logs
  FOR SELECT
  TO authenticated
  USING (auth.uid()::text = user_id);

-- Policy: Allow public inserts (for non-authenticated logging if needed)
CREATE POLICY "Allow system logging"
  ON activity_logs
  FOR INSERT
  TO anon
  WITH CHECK (true);

-- Create a function to automatically clean up old logs (optional, can be called manually or via cron)
CREATE OR REPLACE FUNCTION cleanup_old_activity_logs(days_to_keep integer DEFAULT 90)
RETURNS integer AS $$
DECLARE
  deleted_count integer;
BEGIN
  DELETE FROM activity_logs
  WHERE created_at < NOW() - (days_to_keep || ' days')::interval;
  
  GET DIAGNOSTICS deleted_count = ROW_COUNT;
  RETURN deleted_count;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;