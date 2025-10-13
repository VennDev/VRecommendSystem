package handlers

import (
	"crypto/sha256"
	"database/sql"
	"encoding/hex"
	"fmt"
	"strings"
	"time"

	"github.com/gofiber/fiber/v3"
	_ "github.com/go-sql-driver/mysql"
	_ "github.com/lib/pq"
	"github.com/venndev/vrecommendation/global"
)

type WhitelistEntry struct {
	ID             string    `json:"id"`
	EmailHash      string    `json:"email_hash"`
	EmailEncrypted string    `json:"email_encrypted"`
	AddedBy        string    `json:"added_by"`
	AddedAt        time.Time `json:"added_at"`
	IsActive       bool      `json:"is_active"`
	Notes          string    `json:"notes"`
	CreatedAt      time.Time `json:"created_at"`
	UpdatedAt      time.Time `json:"updated_at"`
}

type AddEmailRequest struct {
	Email   string `json:"email"`
	AddedBy string `json:"added_by"`
	Notes   string `json:"notes"`
}

type CheckEmailRequest struct {
	Email string `json:"email"`
}

type UpdateEmailRequest struct {
	IsActive bool   `json:"is_active"`
	Notes    string `json:"notes"`
}

var whitelistDB *sql.DB
var dbType string

func InitWhitelistDB() error {
	if whitelistDB != nil {
		return nil
	}

	cfg := global.Config
	dbType = strings.ToLower(cfg.Database.Type)

	var connStr string
	var driverName string

	switch dbType {
	case "mysql":
		driverName = "mysql"
		sslParam := ""
		if cfg.Database.SSL {
			sslParam = "?tls=true"
		}
		connStr = fmt.Sprintf("%s:%s@tcp(%s:%d)/%s%s",
			cfg.Database.User,
			cfg.Database.Password,
			cfg.Database.Host,
			cfg.Database.Port,
			cfg.Database.DB,
			sslParam,
		)
	case "postgresql", "postgres":
		driverName = "postgres"
		sslMode := "disable"
		if cfg.Database.SSL {
			sslMode = "require"
		}
		connStr = fmt.Sprintf("host=%s port=%d user=%s password=%s dbname=%s sslmode=%s",
			cfg.Database.Host,
			cfg.Database.Port,
			cfg.Database.User,
			cfg.Database.Password,
			cfg.Database.DB,
			sslMode,
		)
	default:
		return fmt.Errorf("unsupported database type: %s (supported: mysql, postgresql)", dbType)
	}

	var err error
	whitelistDB, err = sql.Open(driverName, connStr)
	if err != nil {
		return fmt.Errorf("failed to connect to database: %w", err)
	}

	if err = whitelistDB.Ping(); err != nil {
		return fmt.Errorf("failed to ping database: %w", err)
	}

	whitelistDB.SetMaxOpenConns(cfg.Database.MaxOpenConns)
	whitelistDB.SetMaxIdleConns(cfg.Database.MaxIdleConns)
	whitelistDB.SetConnMaxLifetime(time.Duration(cfg.Database.ConnMaxLifetime) * time.Second)

	if err := createWhitelistTable(); err != nil {
		return fmt.Errorf("failed to create whitelist table: %w", err)
	}

	return nil
}

func createWhitelistTable() error {
	var query string

	switch dbType {
	case "mysql":
		query = `
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
		`
	case "postgresql", "postgres":
		query = `
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

		CREATE INDEX IF NOT EXISTS idx_email_whitelist_hash ON email_whitelist(email_hash);
		CREATE INDEX IF NOT EXISTS idx_email_whitelist_active ON email_whitelist(is_active) WHERE is_active = true;
		`
	}

	_, err := whitelistDB.Exec(query)
	return err
}

func hashEmail(email string) string {
	email = strings.ToLower(strings.TrimSpace(email))
	hash := sha256.Sum256([]byte(email))
	return hex.EncodeToString(hash[:])
}

func checkLocalhost(c fiber.Ctx) error {
	host := c.Get("Host")
	if !strings.HasPrefix(host, "localhost") && !strings.HasPrefix(host, "127.0.0.1") {
		return c.Status(fiber.StatusForbidden).JSON(fiber.Map{
			"error": "Access denied. This endpoint is only available on localhost.",
		})
	}
	return nil
}

func AddEmailToWhitelist(c fiber.Ctx) error {
	if err := checkLocalhost(c); err != nil {
		return err
	}

	if err := InitWhitelistDB(); err != nil {
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error": "Failed to initialize database connection: " + err.Error(),
		})
	}

	var req AddEmailRequest
	if err := c.Bind().JSON(&req); err != nil {
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{
			"error": "Invalid request body",
		})
	}

	if req.Email == "" {
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{
			"error": "Email is required",
		})
	}

	emailHash := hashEmail(req.Email)

	var query string
	switch dbType {
	case "mysql":
		query = `
			INSERT INTO email_whitelist (email_hash, email_encrypted, added_by, notes, is_active)
			VALUES (?, ?, ?, ?, true)
		`
	case "postgresql", "postgres":
		query = `
			INSERT INTO email_whitelist (email_hash, email_encrypted, added_by, notes, is_active)
			VALUES ($1, $2, $3, $4, true)
			RETURNING id, email_hash, email_encrypted, added_by, added_at, is_active, notes, created_at, updated_at
		`
	}

	if dbType == "mysql" {
		result, err := whitelistDB.Exec(query, emailHash, req.Email, req.AddedBy, req.Notes)
		if err != nil {
			if strings.Contains(err.Error(), "Duplicate entry") || strings.Contains(err.Error(), "duplicate key") {
				return c.Status(fiber.StatusConflict).JSON(fiber.Map{
					"error": "Email already exists in whitelist",
				})
			}
			return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
				"error": "Failed to add email to whitelist: " + err.Error(),
			})
		}

		id, _ := result.LastInsertId()
		entry := WhitelistEntry{
			ID:             fmt.Sprintf("%d", id),
			EmailHash:      emailHash,
			EmailEncrypted: req.Email,
			AddedBy:        req.AddedBy,
			IsActive:       true,
			Notes:          req.Notes,
		}

		return c.Status(fiber.StatusCreated).JSON(fiber.Map{
			"success": true,
			"message": "Email added to whitelist successfully",
			"data":    entry,
		})
	}

	var entry WhitelistEntry
	err := whitelistDB.QueryRow(query, emailHash, req.Email, req.AddedBy, req.Notes).Scan(
		&entry.ID, &entry.EmailHash, &entry.EmailEncrypted, &entry.AddedBy,
		&entry.AddedAt, &entry.IsActive, &entry.Notes, &entry.CreatedAt, &entry.UpdatedAt,
	)

	if err != nil {
		if strings.Contains(err.Error(), "duplicate key") {
			return c.Status(fiber.StatusConflict).JSON(fiber.Map{
				"error": "Email already exists in whitelist",
			})
		}
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error": "Failed to add email to whitelist: " + err.Error(),
		})
	}

	return c.Status(fiber.StatusCreated).JSON(fiber.Map{
		"success": true,
		"message": "Email added to whitelist successfully",
		"data":    entry,
	})
}

func GetWhitelistEmails(c fiber.Ctx) error {
	if err := checkLocalhost(c); err != nil {
		return err
	}

	if err := InitWhitelistDB(); err != nil {
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error": "Failed to initialize database connection",
		})
	}

	query := `
		SELECT id, email_hash, email_encrypted, added_by, added_at, is_active, notes, created_at, updated_at
		FROM email_whitelist
		ORDER BY created_at DESC
	`

	rows, err := whitelistDB.Query(query)
	if err != nil {
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error": "Failed to fetch whitelist: " + err.Error(),
		})
	}
	defer rows.Close()

	var entries []WhitelistEntry
	for rows.Next() {
		var entry WhitelistEntry
		err := rows.Scan(
			&entry.ID, &entry.EmailHash, &entry.EmailEncrypted, &entry.AddedBy,
			&entry.AddedAt, &entry.IsActive, &entry.Notes, &entry.CreatedAt, &entry.UpdatedAt,
		)
		if err != nil {
			continue
		}
		entries = append(entries, entry)
	}

	if entries == nil {
		entries = []WhitelistEntry{}
	}

	return c.JSON(fiber.Map{
		"success": true,
		"data":    entries,
	})
}

func CheckEmailWhitelisted(c fiber.Ctx) error {
	if err := InitWhitelistDB(); err != nil {
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error": "Failed to initialize database connection",
		})
	}

	var req CheckEmailRequest
	if err := c.Bind().JSON(&req); err != nil {
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{
			"error": "Invalid request body",
		})
	}

	if req.Email == "" {
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{
			"error": "Email is required",
		})
	}

	emailHash := hashEmail(req.Email)

	var query string
	switch dbType {
	case "mysql":
		query = `SELECT COUNT(*) FROM email_whitelist WHERE email_hash = ? AND is_active = true`
	case "postgresql", "postgres":
		query = `SELECT COUNT(*) FROM email_whitelist WHERE email_hash = $1 AND is_active = true`
	}

	var count int
	var err error

	if dbType == "mysql" {
		err = whitelistDB.QueryRow(query, emailHash).Scan(&count)
	} else {
		err = whitelistDB.QueryRow(query, emailHash).Scan(&count)
	}

	if err != nil {
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error": "Failed to check whitelist: " + err.Error(),
		})
	}

	return c.JSON(fiber.Map{
		"success":     true,
		"whitelisted": count > 0,
	})
}

func RemoveEmailFromWhitelist(c fiber.Ctx) error {
	if err := checkLocalhost(c); err != nil {
		return err
	}

	if err := InitWhitelistDB(); err != nil {
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error": "Failed to initialize database connection",
		})
	}

	id := c.Params("id")
	if id == "" {
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{
			"error": "ID is required",
		})
	}

	var query string
	switch dbType {
	case "mysql":
		query = `DELETE FROM email_whitelist WHERE id = ?`
	case "postgresql", "postgres":
		query = `DELETE FROM email_whitelist WHERE id = $1`
	}

	result, err := whitelistDB.Exec(query, id)
	if err != nil {
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error": "Failed to remove email from whitelist: " + err.Error(),
		})
	}

	rowsAffected, _ := result.RowsAffected()
	if rowsAffected == 0 {
		return c.Status(fiber.StatusNotFound).JSON(fiber.Map{
			"error": "Email not found in whitelist",
		})
	}

	return c.JSON(fiber.Map{
		"success": true,
		"message": "Email removed from whitelist successfully",
	})
}

func UpdateWhitelistEmail(c fiber.Ctx) error {
	if err := checkLocalhost(c); err != nil {
		return err
	}

	if err := InitWhitelistDB(); err != nil {
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error": "Failed to initialize database connection",
		})
	}

	id := c.Params("id")
	if id == "" {
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{
			"error": "ID is required",
		})
	}

	var req UpdateEmailRequest
	if err := c.Bind().JSON(&req); err != nil {
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{
			"error": "Invalid request body",
		})
	}

	var query string
	switch dbType {
	case "mysql":
		query = `
			UPDATE email_whitelist
			SET is_active = ?, notes = ?, updated_at = NOW()
			WHERE id = ?
		`
		result, err := whitelistDB.Exec(query, req.IsActive, req.Notes, id)
		if err != nil {
			return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
				"error": "Failed to update whitelist entry: " + err.Error(),
			})
		}

		rowsAffected, _ := result.RowsAffected()
		if rowsAffected == 0 {
			return c.Status(fiber.StatusNotFound).JSON(fiber.Map{
				"error": "Email not found in whitelist",
			})
		}

		return c.JSON(fiber.Map{
			"success": true,
			"message": "Whitelist entry updated successfully",
		})

	case "postgresql", "postgres":
		query = `
			UPDATE email_whitelist
			SET is_active = $1, notes = $2, updated_at = NOW()
			WHERE id = $3
			RETURNING id, email_hash, email_encrypted, added_by, added_at, is_active, notes, created_at, updated_at
		`

		var entry WhitelistEntry
		err := whitelistDB.QueryRow(query, req.IsActive, req.Notes, id).Scan(
			&entry.ID, &entry.EmailHash, &entry.EmailEncrypted, &entry.AddedBy,
			&entry.AddedAt, &entry.IsActive, &entry.Notes, &entry.CreatedAt, &entry.UpdatedAt,
		)

		if err != nil {
			if err == sql.ErrNoRows {
				return c.Status(fiber.StatusNotFound).JSON(fiber.Map{
					"error": "Email not found in whitelist",
				})
			}
			return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
				"error": "Failed to update whitelist entry: " + err.Error(),
			})
		}

		return c.JSON(fiber.Map{
			"success": true,
			"message": "Whitelist entry updated successfully",
			"data":    entry,
		})
	}

	return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
		"error": "Unsupported database type",
	})
}

func CheckEmailWhitelistedInternal(email string) (bool, error) {
	if err := InitWhitelistDB(); err != nil {
		return false, err
	}

	emailHash := hashEmail(email)

	var query string
	switch dbType {
	case "mysql":
		query = `SELECT COUNT(*) FROM email_whitelist WHERE email_hash = ? AND is_active = true`
	case "postgresql", "postgres":
		query = `SELECT COUNT(*) FROM email_whitelist WHERE email_hash = $1 AND is_active = true`
	}

	var count int
	err := whitelistDB.QueryRow(query, emailHash).Scan(&count)
	if err != nil {
		return false, err
	}

	return count > 0, nil
}
