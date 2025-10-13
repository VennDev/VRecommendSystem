# Email Whitelist Setup Guide

## Overview
The email whitelist system controls who can login to the application. Only emails added to the whitelist can successfully authenticate.

## Database Configuration

### Step 1: Choose Your Database
The system supports both **MySQL** and **PostgreSQL**. Choose one and install it on your machine.

### Step 2: Configure Database Connection
Edit `backend/api_server/config/local.yml`:

```yaml
# Database configuration for email whitelist
database:
  # Database type: "mysql" or "postgresql"
  type: "postgresql"  # Change to "mysql" if using MySQL
  host: "localhost"
  port: 5432          # Use 3306 for MySQL
  user: "postgres"    # Your database user
  password: "postgres" # Your database password
  db: "vrecommendation" # Database name
  ssl: false
  max_idle_conns: 5
  max_open_conns: 25
  conn_max_lifetime: 300 # seconds
```

### Step 3: Create Database
Create the database in your database server:

**PostgreSQL:**
```sql
CREATE DATABASE vrecommendation;
```

**MySQL:**
```sql
CREATE DATABASE vrecommendation CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

**Note:** The `email_whitelist` table will be created automatically when you start the API server.

## Installation

### Step 1: Install Go Dependencies
```bash
cd backend/api_server
go get github.com/go-sql-driver/mysql  # Add MySQL driver
go mod tidy                             # Clean up dependencies
```

### Step 2: Build and Start API Server
```bash
# From backend/api_server directory
go run main.go

# Or build first
go build -o api_server
./api_server
```

The API server will:
- Connect to your configured database
- Automatically create the `email_whitelist` table if it doesn't exist
- Start listening on port 2030 (default)

## Managing Whitelist

### Access Super Admin Page
1. Make sure API server is running
2. Open browser and navigate to: `http://localhost:5173/super-admin`
3. **Important:** This page only works on localhost for security

### Add Emails to Whitelist
1. Click "Add Email" button
2. Enter email address
3. Optionally add notes (e.g., "Developer", "Admin", etc.)
4. Click "Add to Whitelist"

### Manage Existing Emails
- **Edit:** Click "Edit" button to change active status or notes
- **Deactivate:** Uncheck "Active Status" to prevent login without deleting
- **Remove:** Click trash icon to permanently delete from whitelist

## Security Features

### 1. Localhost Only Access
Super Admin page (`/super-admin`) checks if hostname is:
- `localhost` ✅
- `127.0.0.1` ✅
- Any other domain ❌ (shows "Access Denied")

### 2. Email Hashing
- Emails are stored as SHA-256 hash
- Original email is also stored for display
- Hash is used for fast lookup

### 3. Active Status
- Inactive emails remain in database but cannot login
- Useful for temporary access suspension

## API Endpoints

All whitelist endpoints require **localhost access only**:

### Add Email
```http
POST http://localhost:2030/api/v1/whitelist/add
Content-Type: application/json

{
  "email": "user@example.com",
  "added_by": "admin",
  "notes": "Developer access"
}
```

### List All Emails
```http
GET http://localhost:2030/api/v1/whitelist/list
```

### Check if Email is Whitelisted
```http
POST http://localhost:2030/api/v1/whitelist/check
Content-Type: application/json

{
  "email": "user@example.com"
}
```

### Update Email
```http
PUT http://localhost:2030/api/v1/whitelist/{id}
Content-Type: application/json

{
  "is_active": true,
  "notes": "Updated notes"
}
```

### Remove Email
```http
DELETE http://localhost:2030/api/v1/whitelist/{id}
```

## Database Schema

### PostgreSQL
```sql
CREATE TABLE IF NOT EXISTS email_whitelist (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email_hash TEXT UNIQUE NOT NULL,
    email_encrypted TEXT NOT NULL,
    added_by TEXT DEFAULT 'system',
    added_at TIMESTAMPTZ DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_email_whitelist_hash ON email_whitelist(email_hash);
CREATE INDEX idx_email_whitelist_active ON email_whitelist(is_active) WHERE is_active = true;
```

### MySQL
```sql
CREATE TABLE IF NOT EXISTS email_whitelist (
    id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
    email_hash VARCHAR(64) UNIQUE NOT NULL,
    email_encrypted TEXT NOT NULL,
    added_by VARCHAR(255) DEFAULT 'system',
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_email_whitelist_hash (email_hash),
    INDEX idx_email_whitelist_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

## Troubleshooting

### Cannot Connect to Database
1. Check database is running: `sudo systemctl status postgresql` (or `mysql`)
2. Verify credentials in `config/local.yml`
3. Check database exists: `psql -l` or `mysql -e "SHOW DATABASES;"`
4. Check firewall allows connection to database port

### "Access Denied" on Super Admin Page
- Make sure you're accessing via `localhost` or `127.0.0.1`
- Do NOT use `0.0.0.0` or IP addresses
- Do NOT use domain names

### API Returns 404
1. Check API server is running on port 2030
2. Check URL is correct: `http://localhost:2030/api/v1/whitelist/...`
3. Check routes in `backend/api_server/internal/routes/public_routes.go`

### User Cannot Login After Adding to Whitelist
1. Verify email is active: Check in Super Admin page
2. Verify email spelling matches exactly (case-insensitive)
3. Check API server logs for authentication errors
4. Try removing and re-adding the email

### Database Connection Errors
1. **PostgreSQL:**
   - Check connection string format
   - Verify `sslmode=disable` if not using SSL

2. **MySQL:**
   - Check connection string format: `user:password@tcp(host:port)/database`
   - Verify timezone settings if needed

## Example Workflow

### Initial Setup (First Time)
```bash
# 1. Install and start PostgreSQL (or MySQL)
sudo systemctl start postgresql

# 2. Create database
psql -U postgres -c "CREATE DATABASE vrecommendation;"

# 3. Configure database in config/local.yml
# Edit: backend/api_server/config/local.yml

# 4. Install Go dependencies
cd backend/api_server
go get github.com/go-sql-driver/mysql
go mod tidy

# 5. Start API server
go run main.go

# 6. Start frontend (in another terminal)
cd frontend/project
npm run dev

# 7. Access Super Admin page
# Browser: http://localhost:5173/super-admin

# 8. Add your email to whitelist
# Click "Add Email" and enter your email

# 9. Test login
# Go to: http://localhost:5173/login
# Login with Google using your whitelisted email
```

### Daily Usage
```bash
# Start API server
cd backend/api_server
./api_server  # or: go run main.go

# Start frontend (another terminal)
cd frontend/project
npm run dev

# Access application
# Browser: http://localhost:5173
```

## Notes

- **Database is NOT managed by Docker** - You manage your own database
- **Table is created automatically** - No manual SQL execution needed
- **Super Admin page works offline** - No authentication required on localhost
- **Email hashing is one-way** - Cannot decrypt hash back to email
- **Multiple databases supported** - Switch between MySQL/PostgreSQL easily
