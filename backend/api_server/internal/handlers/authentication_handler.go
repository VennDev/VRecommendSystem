package handlers

import (
	"fmt"
	"net/http"
	"net/url"
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
	store.Options.Secure = false // Set false for HTTP in development
	store.Options.SameSite = http.SameSiteLaxMode
	store.Options.Domain = "" // Empty means current domain only

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

	// Convert Fiber request to HTTP request
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

	// Copy ALL headers including Set-Cookie
	for key, values := range w.headers {
		for _, value := range values {
			if key == "Set-Cookie" {
				c.Append(key, value)
			} else {
				c.Set(key, value)
			}
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

	// Debug: Print incoming cookies
	fmt.Printf("Incoming cookies: %s\n", c.Get("Cookie"))
	fmt.Printf("Query params: %s\n", c.Request().URI().QueryString())

	// Get the provider from goth
	gothProvider, err := goth.GetProvider(provider)
	if err != nil {
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{
			"error":   "Invalid provider",
			"details": err.Error(),
		})
	}

	// Get code and state from query params
	code := c.Query("code")
	state := c.Query("state")

	if code == "" {
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{
			"error": "Authorization code not provided",
		})
	}

	// Create a new session for this callback (not relying on cookies from BeginAuth)
	sess, err := gothProvider.BeginAuth(state)
	if err != nil {
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error":   "Failed to begin auth",
			"details": err.Error(),
		})
	}

	// Exchange code for access token using url.Values which implements goth.Params
	queryParams := url.Values{}
	queryParams.Set("code", code)
	queryParams.Set("state", state)

	_, err = sess.Authorize(gothProvider, queryParams)
	if err != nil {
		fmt.Printf("Authorization error: %v\n", err)
		return c.Status(fiber.StatusUnauthorized).JSON(fiber.Map{
			"error":   "Authentication failed",
			"details": err.Error(),
		})
	}

	// Get user info from provider
	user, err := gothProvider.FetchUser(sess)
	if err != nil {
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error":   "Failed to fetch user",
			"details": err.Error(),
		})
	}

	fmt.Printf("User authenticated successfully: %s (%s)\n", user.Email, user.Provider)

	// Convert Fiber request to HTTP request for session handling
	httpReq2, err := adaptor.ConvertRequest(c, false)
	if err != nil {
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error": "Failed to convert request for session",
		})
	}

	// Create response writer for session
	w := &fiberResponseWriter{ctx: c, headers: make(http.Header)}

	// Save user to session manually using gorilla sessions
	session, err := gothic.Store.Get(httpReq2, fmt.Sprintf("%s_%s", gothic.SessionName, provider))
	if err != nil {
		fmt.Printf("Failed to get session: %v\n", err)
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error":   "Failed to create session",
			"details": err.Error(),
		})
	}

	// Store the complete user object in session
	session.Values["user"] = map[string]interface{}{
		"user_id":      user.UserID,
		"email":        user.Email,
		"name":         user.Name,
		"picture":      user.AvatarURL,
		"provider":     user.Provider,
		"access_token": user.AccessToken,
	}

	// Save session
	if err := session.Save(httpReq2, w); err != nil {
		fmt.Printf("Failed to save session: %v\n", err)
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error":   "Failed to save session",
			"details": err.Error(),
		})
	}

	// Copy session cookies to Fiber response
	if cookies := w.headers["Set-Cookie"]; len(cookies) > 0 {
		for _, cookie := range cookies {
			fmt.Printf("Setting cookie: %s\n", cookie)
			c.Append("Set-Cookie", cookie)
		}
	}

	// Redirect to frontend callback page
	return c.Redirect().To("http://localhost:5173/auth/callback")
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
	provider := c.Query("provider", "google")

	// Convert Fiber request to HTTP request
	httpReq, err := adaptor.ConvertRequest(c, false)
	if err != nil {
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error": "Failed to convert request",
		})
	}

	// Get session
	session, err := gothic.Store.Get(httpReq, fmt.Sprintf("%s_%s", gothic.SessionName, provider))
	if err != nil {
		fmt.Printf("Failed to get session: %v\n", err)
		return c.Status(fiber.StatusUnauthorized).JSON(fiber.Map{
			"error": "Not authenticated - session error",
		})
	}

	// Get user from session
	userDataRaw, ok := session.Values["user"]
	if !ok {
		return c.Status(fiber.StatusUnauthorized).JSON(fiber.Map{
			"error": "Not authenticated - no user in session",
		})
	}

	// Convert to map
	userData, ok := userDataRaw.(map[string]interface{})
	if !ok {
		return c.Status(fiber.StatusUnauthorized).JSON(fiber.Map{
			"error": "Not authenticated - invalid session data",
		})
	}

	return c.JSON(fiber.Map{
		"user": fiber.Map{
			"id":       userData["user_id"],
			"name":     userData["name"],
			"email":    userData["email"],
			"provider": userData["provider"],
			"picture":  userData["picture"],
		},
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
