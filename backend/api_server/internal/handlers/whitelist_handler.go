package handlers

import (
	"crypto/sha256"
	"database/sql"
	"encoding/hex"
	"fmt"
	"os"
	"strings"
	"time"

	"github.com/gofiber/fiber/v3"
	_ "github.com/lib/pq"
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

func InitWhitelistDB() error {
	if whitelistDB != nil {
		return nil
	}

	dbHost := os.Getenv("POSTGRES_HOST")
	if dbHost == "" {
		dbHost = "localhost"
	}
	dbPort := os.Getenv("POSTGRES_PORT")
	if dbPort == "" {
		dbPort = "5432"
	}
	dbUser := os.Getenv("POSTGRES_USER")
	if dbUser == "" {
		dbUser = "postgres"
	}
	dbPassword := os.Getenv("POSTGRES_PASSWORD")
	if dbPassword == "" {
		dbPassword = "postgres"
	}
	dbName := os.Getenv("POSTGRES_DB")
	if dbName == "" {
		dbName = "vrecommendation"
	}

	connStr := fmt.Sprintf("host=%s port=%s user=%s password=%s dbname=%s sslmode=disable",
		dbHost, dbPort, dbUser, dbPassword, dbName)

	var err error
	whitelistDB, err = sql.Open("postgres", connStr)
	if err != nil {
		return fmt.Errorf("failed to connect to database: %w", err)
	}

	if err = whitelistDB.Ping(); err != nil {
		return fmt.Errorf("failed to ping database: %w", err)
	}

	whitelistDB.SetMaxOpenConns(25)
	whitelistDB.SetMaxIdleConns(5)
	whitelistDB.SetConnMaxLifetime(5 * time.Minute)

	if err := createWhitelistTable(); err != nil {
		return fmt.Errorf("failed to create whitelist table: %w", err)
	}

	return nil
}

func createWhitelistTable() error {
	query := `
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
			"error": "Failed to initialize database connection",
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

	query := `
		INSERT INTO email_whitelist (email_hash, email_encrypted, added_by, notes, is_active)
		VALUES ($1, $2, $3, $4, true)
		RETURNING id, email_hash, email_encrypted, added_by, added_at, is_active, notes, created_at, updated_at
	`

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

	query := `
		SELECT COUNT(*) FROM email_whitelist
		WHERE email_hash = $1 AND is_active = true
	`

	var count int
	err := whitelistDB.QueryRow(query, emailHash).Scan(&count)
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

	query := `DELETE FROM email_whitelist WHERE id = $1`
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

	query := `
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

func CheckEmailWhitelistedInternal(email string) (bool, error) {
	if err := InitWhitelistDB(); err != nil {
		return false, err
	}

	emailHash := hashEmail(email)

	query := `
		SELECT COUNT(*) FROM email_whitelist
		WHERE email_hash = $1 AND is_active = true
	`

	var count int
	err := whitelistDB.QueryRow(query, emailHash).Scan(&count)
	if err != nil {
		return false, err
	}

	return count > 0, nil
}
