/*
  # Email Whitelist System

  1. New Tables
    - `email_whitelist`
      - `id` (uuid, primary key)
      - `email_hash` (text, unique) - SHA-256 hash of email for privacy
      - `email_encrypted` (text) - Encrypted email for admin viewing
      - `added_by` (text) - Who added this email
      - `added_at` (timestamptz) - When it was added
      - `is_active` (boolean) - Whether this email is active
      - `notes` (text) - Optional notes about this whitelist entry

  2. Security
    - Enable RLS on `email_whitelist` table
    - Add policy for service role only (super admin via API)
    - No public access to this table
*/

-- Create email whitelist table
CREATE TABLE IF NOT EXISTS email_whitelist (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  email_hash text UNIQUE NOT NULL,
  email_encrypted text NOT NULL,
  added_by text DEFAULT 'system',
  added_at timestamptz DEFAULT now(),
  is_active boolean DEFAULT true,
  notes text,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- Enable RLS
ALTER TABLE email_whitelist ENABLE ROW LEVEL SECURITY;

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_email_whitelist_hash ON email_whitelist(email_hash);
CREATE INDEX IF NOT EXISTS idx_email_whitelist_active ON email_whitelist(is_active) WHERE is_active = true;

-- Policy: Only service role can access (no regular users)
CREATE POLICY "Service role full access"
  ON email_whitelist
  FOR ALL
  TO service_role
  USING (true)
  WITH CHECK (true);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_email_whitelist_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-update updated_at
CREATE TRIGGER update_email_whitelist_timestamp
  BEFORE UPDATE ON email_whitelist
  FOR EACH ROW
  EXECUTE FUNCTION update_email_whitelist_updated_at();

-- Add some helpful comments
COMMENT ON TABLE email_whitelist IS 'Stores whitelisted emails for system access control';
COMMENT ON COLUMN email_whitelist.email_hash IS 'SHA-256 hash of email for lookup without exposing actual email';
COMMENT ON COLUMN email_whitelist.email_encrypted IS 'Encrypted email address for admin viewing';
