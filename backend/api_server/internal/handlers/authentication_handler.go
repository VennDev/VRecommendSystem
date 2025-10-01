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

	var authURL string
	var authErr error

	handler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		q := r.URL.Query()
		q.Add("provider", provider)
		r.URL.RawQuery = q.Encode()

		authURL, authErr = gothic.GetAuthURL(w, r)
	})

	// Convert HTTP handler sang Fiber handler và execute
	httpReq, err := adaptor.ConvertRequest(c, false)
	if err != nil {
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error": "Failed to convert request",
		})
	}

	w := &fiberResponseWriter{
		ctx:     c,
		headers: make(http.Header),
	}

	// Execute handler
	handler.ServeHTTP(w, httpReq)

	for key, values := range w.headers {
		for _, value := range values {
			c.Set(key, value)
		}
	}

	if cookies := w.headers["Set-Cookie"]; len(cookies) > 0 {
		for _, cookie := range cookies {
			c.Append("Set-Cookie", cookie)
		}
	}

	if authErr != nil {
		fmt.Println("GetAuthURL error:", authErr)
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error":   "Failed to get auth URL",
			"details": authErr.Error(),
		})
	}

	if authURL == "" {
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error": "Auth URL is empty",
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
	var authErr error

	handler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Set provider in request context for gothic
		q := r.URL.Query()
		q.Add("provider", provider)
		r.URL.RawQuery = q.Encode()

		user, authErr = gothic.CompleteUserAuth(w, r)
	})

	// Convert HTTP handler sang Fiber handler
	httpReq, err := adaptor.ConvertRequest(c, false)
	if err != nil {
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error": "Failed to convert request",
		})
	}

	w := &fiberResponseWriter{
		ctx:     c,
		headers: make(http.Header),
	}

	// Execute handler
	handler.ServeHTTP(w, httpReq)

	for key, values := range w.headers {
		for _, value := range values {
			c.Set(key, value)
		}
	}

	if authErr != nil {
		fmt.Printf("Authentication error for provider %s: %v\n", provider, authErr)

		if authErr.Error() == "user has not completed auth flow" {
			return BeginAuthHandler(c)
		}

		return c.Status(fiber.StatusUnauthorized).JSON(fiber.Map{
			"error":   "Authentication failed",
			"details": authErr.Error(),
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
			"picture":  user.AvatarURL,
		},
	})

	// Option 2: Redirect to frontend callback page
	// return c.Redirect().To("http://localhost:5173/auth/callback")
}

func LogoutHandler(c fiber.Ctx) error {
	provider := c.Query("provider", "google")

	var logoutErr error
	handler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		q := r.URL.Query()
		q.Add("provider", provider)
		r.URL.RawQuery = q.Encode()

		logoutErr = gothic.Logout(w, r)
	})

	httpReq, err := adaptor.ConvertRequest(c, false)
	if err != nil {
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error": "Failed to convert request",
		})
	}

	w := &fiberResponseWriter{
		ctx:     c,
		headers: make(http.Header),
	}

	// Execute handler
	handler.ServeHTTP(w, httpReq)

	if logoutErr != nil {
		fmt.Println("Logout error:", logoutErr)
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

type fiberResponseWriter struct {
	ctx        fiber.Ctx
	statusCode int
	headers    http.Header
	body       []byte
}

func (w *fiberResponseWriter) Header() http.Header {
	return w.headers
}

func (w *fiberResponseWriter) Write(b []byte) (int, error) {
	w.body = append(w.body, b...)
	return len(b), nil
}

func (w *fiberResponseWriter) WriteHeader(statusCode int) {
	w.statusCode = statusCode
}
