package handlers

import (
	"crypto/sha256"
	"encoding/hex"
	"os"
	"strings"

	"github.com/gofiber/fiber/v3"
	"github.com/supabase-community/supabase-go"
)

type WhitelistEntry struct {
	ID             string `json:"id"`
	EmailHash      string `json:"email_hash"`
	EmailEncrypted string `json:"email_encrypted"`
	AddedBy        string `json:"added_by"`
	AddedAt        string `json:"added_at"`
	IsActive       bool   `json:"is_active"`
	Notes          string `json:"notes"`
	CreatedAt      string `json:"created_at"`
	UpdatedAt      string `json:"updated_at"`
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

var supabaseClient *supabase.Client

func initSupabaseClient() error {
	if supabaseClient != nil {
		return nil
	}

	supabaseURL := os.Getenv("VITE_SUPABASE_URL")
	supabaseKey := os.Getenv("VITE_SUPABASE_SUPABASE_ANON_KEY")

	if supabaseURL == "" || supabaseKey == "" {
		return fiber.NewError(fiber.StatusInternalServerError, "Supabase configuration not found")
	}

	var err error
	supabaseClient, err = supabase.NewClient(supabaseURL, supabaseKey, &supabase.ClientOptions{})
	if err != nil {
		return err
	}

	return nil
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

	if err := initSupabaseClient(); err != nil {
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

	data := map[string]interface{}{
		"email_hash":      emailHash,
		"email_encrypted": req.Email,
		"added_by":        req.AddedBy,
		"notes":           req.Notes,
		"is_active":       true,
	}

	var result []WhitelistEntry
	err := supabaseClient.DB.From("email_whitelist").Insert(data).Execute(&result)
	if err != nil {
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error": "Failed to add email to whitelist: " + err.Error(),
		})
	}

	return c.Status(fiber.StatusCreated).JSON(fiber.Map{
		"success": true,
		"message": "Email added to whitelist successfully",
		"data":    result,
	})
}

func GetWhitelistEmails(c fiber.Ctx) error {
	if err := checkLocalhost(c); err != nil {
		return err
	}

	if err := initSupabaseClient(); err != nil {
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error": "Failed to initialize database connection",
		})
	}

	var result []WhitelistEntry
	err := supabaseClient.DB.From("email_whitelist").
		Select("*").
		Order("created_at", &supabase.OrderOpts{Ascending: false}).
		Execute(&result)

	if err != nil {
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error": "Failed to fetch whitelist: " + err.Error(),
		})
	}

	return c.JSON(fiber.Map{
		"success": true,
		"data":    result,
	})
}

func CheckEmailWhitelisted(c fiber.Ctx) error {
	if err := initSupabaseClient(); err != nil {
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

	var result []WhitelistEntry
	err := supabaseClient.DB.From("email_whitelist").
		Select("*").
		Eq("email_hash", emailHash).
		Eq("is_active", "true").
		Execute(&result)

	if err != nil {
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error": "Failed to check whitelist: " + err.Error(),
		})
	}

	whitelisted := len(result) > 0

	return c.JSON(fiber.Map{
		"success":     true,
		"whitelisted": whitelisted,
	})
}

func RemoveEmailFromWhitelist(c fiber.Ctx) error {
	if err := checkLocalhost(c); err != nil {
		return err
	}

	if err := initSupabaseClient(); err != nil {
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

	var result []WhitelistEntry
	err := supabaseClient.DB.From("email_whitelist").
		Delete().
		Eq("id", id).
		Execute(&result)

	if err != nil {
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error": "Failed to remove email from whitelist: " + err.Error(),
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

	if err := initSupabaseClient(); err != nil {
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

	data := map[string]interface{}{
		"is_active": req.IsActive,
		"notes":     req.Notes,
	}

	var result []WhitelistEntry
	err := supabaseClient.DB.From("email_whitelist").
		Update(data).
		Eq("id", id).
		Execute(&result)

	if err != nil {
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error": "Failed to update whitelist entry: " + err.Error(),
		})
	}

	return c.JSON(fiber.Map{
		"success": true,
		"message": "Whitelist entry updated successfully",
		"data":    result,
	})
}
