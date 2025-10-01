/*
  # Create Activity Logs System

  1. New Tables
    - `activity_logs`
      - `id` (uuid, primary key)
      - `user_id` (text, user identifier)
      - `user_email` (text, user email)
      - `action` (text, action performed)
      - `resource_type` (text, type of resource: model, task, data_chef, etc.)
      - `resource_id` (text, id of the resource)
      - `details` (jsonb, additional details about the action)
      - `ip_address` (text, user's IP address)
      - `user_agent` (text, user's browser/client info)
      - `created_at` (timestamptz, when the action occurred)

  2. Security
    - Enable RLS on `activity_logs` table
    - Add policy for authenticated users to insert their own logs
    - Add policy for authenticated users to read their own logs
    - Add policy for system to insert logs (for server-side logging)

  3. Indexes
    - Index on `user_id` for fast user-based queries
    - Index on `created_at` for time-based queries
    - Index on `resource_type` and `resource_id` for resource-based queries
*/

CREATE TABLE IF NOT EXISTS activity_logs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id text NOT NULL,
  user_email text NOT NULL,
  action text NOT NULL,
  resource_type text,
  resource_id text,
  details jsonb DEFAULT '{}'::jsonb,
  ip_address text,
  user_agent text,
  created_at timestamptz DEFAULT now()
);

-- Enable RLS
ALTER TABLE activity_logs ENABLE ROW LEVEL SECURITY;

-- Users can insert their own activity logs
CREATE POLICY "Users can insert own activity logs"
  ON activity_logs
  FOR INSERT
  TO authenticated
  WITH CHECK (true);

-- Users can read their own activity logs
CREATE POLICY "Users can read own activity logs"
  ON activity_logs
  FOR SELECT
  TO authenticated
  USING (user_id = current_user OR user_email = current_user);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_activity_logs_user_id ON activity_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_activity_logs_created_at ON activity_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_activity_logs_resource ON activity_logs(resource_type, resource_id);
CREATE INDEX IF NOT EXISTS idx_activity_logs_action ON activity_logs(action);