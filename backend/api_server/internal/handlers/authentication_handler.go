package handlers

import (
	"fmt"
	"net/http"
	"os"

	"github.com/gofiber/fiber/v3"
	"github.com/gofiber/fiber/v3/middleware/adaptor"
	"github.com/gorilla/sessions"
	"github.com/joho/godotenv"
	"github.com/markbates/goth"
	"github.com/markbates/goth/gothic"
	"github.com/markbates/goth/providers/google"
)

func NewAuth() {
	err := godotenv.Load()
	if err != nil {
		panic("Error loading .env file")
	}

	googleClientId := os.Getenv("GOOGLE_CLIENT_ID")
	googleClientSecret := os.Getenv("GOOGLE_CLIENT_SECRET")
	if googleClientId == "" || googleClientSecret == "" {
		panic("Google OAuth credentials are not set in environment variables")
	}

	secretKey := os.Getenv("SESSION_SECRET")
	if secretKey == "" {
		secretKey = googleClientSecret // fallback
	}

	store := sessions.NewCookieStore([]byte(secretKey))
	store.MaxAge(24 * 60 * 60) // 24 hours in seconds
	store.Options.Path = "/"
	store.Options.HttpOnly = true
	store.Options.Secure = false // Set true for HTTPS in production
	//store.Options.SameSite = http.SameSiteLaxMode

	gothic.Store = store

	goth.UseProviders(
		google.New(
			googleClientId,
			googleClientSecret,
			os.Getenv("GOOGLE_CALLBACK_URL"),
			"email",
			"profile",
		),
	)
}

func BeginAuthHandler(c fiber.Ctx) error {
	provider := c.Params("provider")
	if provider == "" {
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{
			"error": "Provider is required",
		})
	}

	// Redirect to OAuth provider
	var authURL string
	var err error

	handler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Set provider in request context for gothic
		r = r.WithContext(r.Context())
		q := r.URL.Query()
		q.Add("provider", provider)
		r.URL.RawQuery = q.Encode()

		authURL, err = gothic.GetAuthURL(w, r)
		if err != nil {
			return
		}
	})

	if adaptErr := adaptor.HTTPHandler(handler)(c); adaptErr != nil {
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error": "Failed to initialize authentication",
		})
	}

	if err != nil {
		fmt.Println("GetAuthURL error:", err)
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error": "Failed to get auth URL",
		})
	}

	// Redirect user to OAuth provider
	return c.Redirect().To(authURL)
}

func CallbackHandler(c fiber.Ctx) error {
	provider := c.Params("provider")
	if provider == "" {
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{
			"error": "Provider is required",
		})
	}

	var user goth.User
	var err error

	handler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Set provider in request context for gothic
		q := r.URL.Query()
		q.Add("provider", provider)
		r.URL.RawQuery = q.Encode()

		user, err = gothic.CompleteUserAuth(w, r)
	})

	if adaptErr := adaptor.HTTPHandler(handler)(c); adaptErr != nil {
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error": "Failed to process authentication",
		})
	}

	if err != nil {
		fmt.Printf("Authentication error for provider %s: %v\n", provider, err)

		if err.Error() == "user has not completed auth flow" {
			return BeginAuthHandler(c)
		}

		return c.Status(fiber.StatusUnauthorized).JSON(fiber.Map{
			"error":   "Authentication failed",
			"details": err.Error(),
		})
	}

	fmt.Printf("User authenticated successfully: %s (%s)\n", user.Email, user.Provider)

	c.Locals("user", user)

	return c.JSON(fiber.Map{
		"success": true,
		"message": "Authentication successful",
		"user": fiber.Map{
			"id":       user.UserID,
			"name":     user.Name,
			"email":    user.Email,
			"provider": user.Provider,
			"avatar":   user.AvatarURL,
		},
	})

	// Option 2: Redirect to frontend (uncomment if needed)
	// return c.Redirect().To("http://localhost:5173?auth=success")
}

func LogoutHandler(c fiber.Ctx) error {
	provider := c.Query("provider", "google")

	var err error
	handler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		q := r.URL.Query()
		q.Add("provider", provider)
		r.URL.RawQuery = q.Encode()

		err = gothic.Logout(w, r)
	})

	if adaptErr := adaptor.HTTPHandler(handler)(c); adaptErr != nil {
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error": "Failed to logout",
		})
	}

	if err != nil {
		fmt.Println("Logout error:", err)
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error": "Logout failed",
		})
	}

	return c.JSON(fiber.Map{
		"success": true,
		"message": "Logged out successfully",
	})
}

func GetUserHandler(c fiber.Ctx) error {
	user := c.Locals("user")
	if user == nil {
		return c.Status(fiber.StatusUnauthorized).JSON(fiber.Map{
			"error": "Not authenticated",
		})
	}

	return c.JSON(fiber.Map{
		"user": user,
	})
}
