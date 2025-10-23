package handlers

import (
	"fmt"
	"net/http"
	"net/url"
	"os"
	"strings"
	"time"

	"github.com/gofiber/fiber/v3"
	"github.com/gofiber/fiber/v3/middleware/adaptor"
	"github.com/golang-jwt/jwt/v5"
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
		secretKey = os.Getenv("JWT_SECRET_KEY")
	}
	if secretKey == "" {
		secretKey = "default-development-secret-key-change-in-production"
	}

	store := sessions.NewCookieStore([]byte(secretKey))
	store.MaxAge(24 * 60 * 60) // 24 hours in seconds
	store.Options.Path = "/"
	store.Options.HttpOnly = true
	store.Options.Secure = false        // Set false for HTTP in development
	store.Options.MaxAge = 24 * 60 * 60 // 24 hours
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

	// Check if email is whitelisted
	whitelisted, err := CheckEmailWhitelistedInternal(user.Email)
	if err != nil {
		fmt.Printf("Failed to check whitelist: %v\n", err)
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error": "Failed to verify user access",
		})
	}

	if !whitelisted {
		fmt.Printf("User email %s is not whitelisted\n", user.Email)
		return c.Status(fiber.StatusForbidden).JSON(fiber.Map{
			"error":   "Access denied",
			"message": "Your email is not authorized to access this system. Please contact the administrator.",
		})
	}

	fmt.Printf("User email %s is whitelisted\n", user.Email)

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
	sessionName := fmt.Sprintf("%s_%s", gothic.SessionName, provider)
	fmt.Printf("Creating session with name: %s\n", sessionName)

	// Try to get existing session first, create new if it fails
	session, err := gothic.Store.Get(httpReq2, sessionName)
	if err != nil {
		fmt.Printf("Failed to get existing session, creating new one: %v\n", err)
		// Clear any corrupted cookies first
		c.Cookie(&fiber.Cookie{
			Name:     sessionName,
			Value:    "",
			MaxAge:   -1,
			Path:     "/",
			HTTPOnly: true,
			Secure:   false,
		})

		// Create a completely new session
		session = sessions.NewSession(gothic.Store, sessionName)
		session.IsNew = true
	}

	// Ensure proper session options
	session.Options = &sessions.Options{
		Path:     "/",
		MaxAge:   24 * 60 * 60, // 24 hours
		HttpOnly: true,
		Secure:   false, // HTTP in development
		SameSite: http.SameSiteLaxMode,
	}

	// Clear any existing values first to avoid corruption
	session.Values = make(map[interface{}]interface{})

	// Store user data as separate fields (gob-compatible)
	session.Values["user_id"] = user.UserID
	session.Values["email"] = user.Email
	session.Values["name"] = user.Name
	session.Values["picture"] = user.AvatarURL
	session.Values["provider"] = user.Provider
	session.Values["access_token"] = user.AccessToken
	session.Values["authenticated"] = true

	// Save session
	fmt.Printf("Attempting to save session with values: %+v\n", session.Values)
	if err := session.Save(httpReq2, w); err != nil {
		fmt.Printf("Failed to save session: %v\n", err)
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error":   "Failed to save session",
			"details": err.Error(),
		})
	}

	fmt.Printf("Session saved successfully!\n")
	fmt.Printf("Response headers: %v\n", w.headers)

	// Copy session cookies to Fiber response (for API server authentication)
	if cookies := w.headers["Set-Cookie"]; len(cookies) > 0 {
		for _, cookie := range cookies {
			fmt.Printf("Setting cookie: %s\n", cookie)
			c.Append("Set-Cookie", cookie)
		}
	} else {
		fmt.Printf("WARNING: No Set-Cookie headers found!\n")
	}

	// Generate JWT token for cross-service authentication (for AI server)
	jwtToken, err := generateJWTToken(user.UserID, user.Email, user.Name)
	if err != nil {
		fmt.Printf("Failed to generate JWT token: %v\n", err)
	} else {
		// Set JWT token as an additional cookie for AI server
		c.Cookie(&fiber.Cookie{
			Name:     "auth_token",
			Value:    jwtToken,
			Path:     "/",
			MaxAge:   24 * 60 * 60,
			HTTPOnly: true,
			Secure:   false,
			SameSite: "Lax",
		})
		fmt.Printf("JWT token cookie set successfully\n")
	}

	// Encode user data as URL parameters to pass to frontend
	userData := url.Values{}
	userData.Set("id", user.UserID)
	userData.Set("email", user.Email)
	userData.Set("name", user.Name)
	userData.Set("picture", user.AvatarURL)
	userData.Set("provider", user.Provider)

	// Add JWT token to URL params for frontend to store
	if jwtToken != "" {
		userData.Set("token", jwtToken)
	}

	// Redirect to frontend with user data and token
	redirectURL := fmt.Sprintf("http://localhost:5173/auth/callback?%s", userData.Encode())

	fmt.Printf("Redirecting to: %s\n", redirectURL)

	return c.Redirect().To(redirectURL)
}

func LogoutHandler(c fiber.Ctx) error {
	provider := c.Query("provider", "google")

	// Convert request
	httpReq, err := adaptor.ConvertRequest(c, false)
	if err != nil {
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error": "Failed to convert request",
		})
	}

	// Create response writer
	w := &fiberResponseWriter{
		ctx:     c,
		headers: make(http.Header),
	}

	// Get and clear session
	session, err := gothic.Store.Get(httpReq, fmt.Sprintf("%s_%s", gothic.SessionName, provider))
	if err != nil {
		fmt.Printf("Failed to get session for logout: %v\n", err)
		// Continue anyway to clear client-side
	} else {
		// Clear all session values
		session.Values = make(map[interface{}]interface{})
		session.Options.MaxAge = -1 // Delete cookie

		// Save cleared session
		if err := session.Save(httpReq, w); err != nil {
			fmt.Printf("Failed to clear session: %v\n", err)
		}

		// Copy cleared cookie to response
		if cookies := w.headers["Set-Cookie"]; len(cookies) > 0 {
			for _, cookie := range cookies {
				c.Append("Set-Cookie", cookie)
			}
		}
	}

	return c.JSON(fiber.Map{
		"success": true,
		"message": "Logged out successfully",
	})
}

func GetUserHandler(c fiber.Ctx) error {
	provider := c.Query("provider", "google")

	// Check for JWT token first
	authHeader := c.Get("Authorization")
	if authHeader != "" && strings.HasPrefix(authHeader, "Bearer ") {
		token := authHeader[7:] // Remove "Bearer " prefix
		fmt.Printf("GetUserHandler - Found JWT token\n")

		// Verify JWT token
		secretKey := os.Getenv("JWT_SECRET_KEY")
		if secretKey == "" {
			secretKey = os.Getenv("SESSION_SECRET")
		}
		if secretKey == "" {
			secretKey = "default-development-secret-key-change-in-production"
		}

		parsedToken, err := jwt.Parse(token, func(token *jwt.Token) (interface{}, error) {
			if _, ok := token.Method.(*jwt.SigningMethodHMAC); !ok {
				return nil, fmt.Errorf("unexpected signing method: %v", token.Header["alg"])
			}
			return []byte(secretKey), nil
		})

		if err == nil && parsedToken.Valid {
			if claims, ok := parsedToken.Claims.(jwt.MapClaims); ok {
				userId, _ := claims["user_id"].(string)
				email, _ := claims["email"].(string)
				name, _ := claims["name"].(string)

				fmt.Printf("GetUserHandler - JWT token valid for user: %s\n", email)

				return c.JSON(fiber.Map{
					"user": fiber.Map{
						"id":       userId,
						"name":     name,
						"email":    email,
						"provider": "google", // Default since JWT doesn't store provider
						"picture":  "",       // JWT doesn't store picture URL
					},
				})
			}
		}

		fmt.Printf("GetUserHandler - Invalid JWT token: %v\n", err)
		// JWT token is invalid, continue to session check
	}

	// Fallback to session-based authentication
	fmt.Printf("GetUserHandler - Checking session authentication\n")

	// Debug: Print cookie header
	cookieHeader := c.Get("Cookie")
	fmt.Printf("GetUserHandler - Cookie header: %s\n", cookieHeader)

	sessionName := fmt.Sprintf("%s_%s", gothic.SessionName, provider)
	fmt.Printf("GetUserHandler - Looking for session cookie: %s\n", sessionName)

	// Convert Fiber request to HTTP request
	httpReq, err := adaptor.ConvertRequest(c, false)
	if err != nil {
		fmt.Printf("Failed to convert request: %v\n", err)
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error": "Failed to convert request",
		})
	}

	// Get session
	fmt.Printf("Attempting to get session: %s\n", sessionName)

	session, err := gothic.Store.Get(httpReq, sessionName)
	if err != nil {
		fmt.Printf("Failed to get session: %v\n", err)
		// Clear corrupted cookie and return error
		c.Cookie(&fiber.Cookie{
			Name:     sessionName,
			Value:    "",
			MaxAge:   -1,
			Path:     "/",
			HTTPOnly: true,
			Secure:   false,
		})
		return c.Status(fiber.StatusUnauthorized).JSON(fiber.Map{
			"error":   "Not authenticated - session error. Please login again.",
			"details": err.Error(),
		})
	}

	fmt.Printf("Session values: %+v\n", session.Values)

	// Check if authenticated
	authenticated, ok := session.Values["authenticated"].(bool)
	if !ok || !authenticated {
		return c.Status(fiber.StatusUnauthorized).JSON(fiber.Map{
			"error": "Not authenticated",
		})
	}

	// Get user data from session
	userId, _ := session.Values["user_id"].(string)
	email, _ := session.Values["email"].(string)
	name, _ := session.Values["name"].(string)
	picture, _ := session.Values["picture"].(string)
	providerV, _ := session.Values["provider"].(string)

	if userId == "" || email == "" {
		return c.Status(fiber.StatusUnauthorized).JSON(fiber.Map{
			"error": "Invalid session data",
		})
	}

	return c.JSON(fiber.Map{
		"user": fiber.Map{
			"id":       userId,
			"name":     name,
			"email":    email,
			"provider": providerV,
			"picture":  picture,
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

// generateJWTToken creates a JWT token for cross-service authentication
func generateJWTToken(userID, email, name string) (string, error) {
	secretKey := os.Getenv("JWT_SECRET_KEY")
	if secretKey == "" {
		secretKey = os.Getenv("SESSION_SECRET")
	}

	claims := jwt.MapClaims{
		"user_id": userID,
		"email":   email,
		"name":    name,
		"exp":     time.Now().Add(24 * time.Hour).Unix(),
		"iat":     time.Now().Unix(),
	}

	token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
	tokenString, err := token.SignedString([]byte(secretKey))
	if err != nil {
		return "", fmt.Errorf("failed to sign JWT token: %w", err)
	}

	return tokenString, nil
}

// ClearSessionsHandler clears all session cookies for debugging
func ClearSessionsHandler(c fiber.Ctx) error {
	// Clear common session cookie names
	sessionNames := []string{
		"_gothic_session",
		"_gothic_session_google",
		"_gothic_session_github",
		"auth_token",
	}

	for _, sessionName := range sessionNames {
		c.Cookie(&fiber.Cookie{
			Name:     sessionName,
			Value:    "",
			MaxAge:   -1,
			Path:     "/",
			HTTPOnly: true,
			Secure:   false,
		})
	}

	return c.JSON(fiber.Map{
		"message": "All sessions cleared successfully",
		"cleared": sessionNames,
	})
}
