package handlers

import (
	"fmt"
	"net/http"
	"net/url"
	"os"
	"strconv"
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
	"github.com/venndev/vrecommendation/global"
)

var (
	googleClientID     string
	googleClientSecret string
	callbackURLLocal   string
	callbackURLPublic  string
)

func NewAuth() {
	// Load .env file
	err := godotenv.Load()
	if err != nil {
		fmt.Println("Warning: .env file not found, using environment variables from system/docker")
	}

	googleClientID = os.Getenv("GOOGLE_CLIENT_ID")
	googleClientSecret = os.Getenv("GOOGLE_CLIENT_SECRET")

	fmt.Printf("OAuth Debug - GOOGLE_CLIENT_ID set: %v, GOOGLE_CLIENT_SECRET set: %v\n",
		googleClientID != "", googleClientSecret != "")

	if googleClientID == "" || googleClientSecret == "" {
		fmt.Println("Warning: Google OAuth credentials are not set. OAuth login will be disabled.")
		return
	}

	// Get callback URLs from environment
	callbackURLLocal = os.Getenv("GOOGLE_CALLBACK_URL")
	if callbackURLLocal == "" {
		callbackURLLocal = "http://localhost:2030/api/v1/auth/google/callback"
	}

	callbackURLPublic = os.Getenv("GOOGLE_CALLBACK_URL_PUBLIC")

	fmt.Println("OAuth Callback URLs:")
	fmt.Printf("  - Local:  %s\n", callbackURLLocal)
	if callbackURLPublic != "" {
		fmt.Printf("  - Public: %s\n", callbackURLPublic)
	} else {
		fmt.Println("  - Public: (not set)")
	}

	// Setup session store
	secretKey := os.Getenv("SESSION_SECRET")
	if secretKey == "" {
		secretKey = os.Getenv("JWT_SECRET_KEY")
	}
	if secretKey == "" {
		secretKey = "default-development-secret-key-change-in-production"
	}

	store := sessions.NewCookieStore([]byte(secretKey))
	store.MaxAge(24 * 60 * 60)
	store.Options.Path = "/"
	store.Options.HttpOnly = true
	store.Options.Secure = false
	store.Options.MaxAge = 24 * 60 * 60
	store.Options.SameSite = http.SameSiteLaxMode
	store.Options.Domain = ""

	gothic.Store = store

	// Initialize default provider
	goth.UseProviders(
		google.New(
			googleClientID,
			googleClientSecret,
			callbackURLLocal,
			"email",
			"profile",
		),
	)
}

// getCallbackURL returns the appropriate callback URL based on request
func getCallbackURL(c fiber.Ctx) string {
	// If no public URL configured, always use local
	if callbackURLPublic == "" {
		return callbackURLLocal
	}

	// Check if request is from localhost
	host := c.Get("Host")
	origin := c.Get("Origin")
	referer := c.Get("Referer")

	// Check Host header
	if strings.HasPrefix(host, "localhost") || strings.HasPrefix(host, "127.0.0.1") {
		return callbackURLLocal
	}

	// Check Origin header
	if origin != "" {
		if strings.Contains(origin, "localhost") || strings.Contains(origin, "127.0.0.1") {
			return callbackURLLocal
		}
	}

	// Check Referer header
	if referer != "" {
		if strings.Contains(referer, "localhost") || strings.Contains(referer, "127.0.0.1") {
			return callbackURLLocal
		}
	}

	// Default to public URL for non-localhost requests
	return callbackURLPublic
}

func BeginAuthHandler(c fiber.Ctx) error {
	provider := c.Params("provider")
	if provider == "" {
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{
			"error": "Provider is required",
		})
	}

	if googleClientID == "" || googleClientSecret == "" {
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error": "OAuth not configured",
		})
	}

	// Get appropriate callback URL
	callbackURL := getCallbackURL(c)
	fmt.Printf("[OAuth] BeginAuth - Using callback: %s\n", callbackURL)

	// Create provider with selected callback URL
	googleProvider := google.New(
		googleClientID,
		googleClientSecret,
		callbackURL,
		"email",
		"profile",
	)

	// Get auth URL directly from provider
	sess, err := googleProvider.BeginAuth("")
	if err != nil {
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error":   "Failed to begin auth",
			"details": err.Error(),
		})
	}

	authURL, err := sess.GetAuthURL()
	if err != nil {
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error":   "Failed to get auth URL",
			"details": err.Error(),
		})
	}

	fmt.Printf("[OAuth] Redirecting to: %s\n", authURL)
	return c.Redirect().To(authURL)
}

func CallbackHandler(c fiber.Ctx) error {
	provider := c.Params("provider")
	if provider == "" {
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{
			"error": "Provider is required",
		})
	}

	fmt.Printf("[OAuth] Callback received\n")

	// Get code and state from query params
	code := c.Query("code")
	state := c.Query("state")

	if code == "" {
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{
			"error": "Authorization code not provided",
		})
	}

	// Get appropriate callback URL
	callbackURL := getCallbackURL(c)
	fmt.Printf("[OAuth] Callback - Using callback: %s\n", callbackURL)

	// Create provider with matching callback URL
	googleProvider := google.New(
		googleClientID,
		googleClientSecret,
		callbackURL,
		"email",
		"profile",
	)

	// Begin auth session
	sess, err := googleProvider.BeginAuth(state)
	if err != nil {
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error":   "Failed to begin auth",
			"details": err.Error(),
		})
	}

	// Exchange code for token
	queryParams := url.Values{}
	queryParams.Set("code", code)
	queryParams.Set("state", state)

	_, err = sess.Authorize(googleProvider, queryParams)
	if err != nil {
		fmt.Printf("Authorization error: %v\n", err)
		return c.Status(fiber.StatusUnauthorized).JSON(fiber.Map{
			"error":   "Authentication failed",
			"details": err.Error(),
		})
	}

	// Get user info
	user, err := googleProvider.FetchUser(sess)
	if err != nil {
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error":   "Failed to fetch user",
			"details": err.Error(),
		})
	}

	fmt.Printf("User authenticated: %s (%s)\n", user.Email, user.Provider)

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

	// Save session
	httpReq, err := adaptor.ConvertRequest(c, false)
	if err != nil {
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error": "Failed to convert request",
		})
	}

	w := &fiberResponseWriter{ctx: c, headers: make(http.Header)}
	sessionName := fmt.Sprintf("%s_%s", gothic.SessionName, provider)

	session, err := gothic.Store.Get(httpReq, sessionName)
	if err != nil {
		c.Cookie(&fiber.Cookie{
			Name:     sessionName,
			Value:    "",
			MaxAge:   -1,
			Path:     "/",
			HTTPOnly: true,
			Secure:   false,
		})
		session = sessions.NewSession(gothic.Store, sessionName)
		session.IsNew = true
	}

	session.Options = &sessions.Options{
		Path:     "/",
		MaxAge:   24 * 60 * 60,
		HttpOnly: true,
		Secure:   false,
		SameSite: http.SameSiteLaxMode,
	}

	session.Values = make(map[interface{}]interface{})
	session.Values["user_id"] = user.UserID
	session.Values["email"] = user.Email
	session.Values["name"] = user.Name
	session.Values["picture"] = user.AvatarURL
	session.Values["provider"] = user.Provider
	session.Values["access_token"] = user.AccessToken
	session.Values["authenticated"] = true

	if err := session.Save(httpReq, w); err != nil {
		fmt.Printf("Failed to save session: %v\n", err)
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error":   "Failed to save session",
			"details": err.Error(),
		})
	}

	// Copy session cookies
	if cookies := w.headers["Set-Cookie"]; len(cookies) > 0 {
		for _, cookie := range cookies {
			c.Append("Set-Cookie", cookie)
		}
	}

	// Generate JWT token
	timeExpire, err := strconv.Atoi(os.Getenv("AUTH_TOKEN_MAX_AGE_SECONDS"))
	if err != nil || timeExpire <= 0 {
		timeExpire = 24 * 60 * 60 // Default to 1 day
		fmt.Printf("AUTH_TOKEN_MAX_AGE_SECONDS not set or invalid, defaulting to %d seconds\n", timeExpire)
	}

	jwtToken, err := generateJWTToken(user.UserID, user.Email, user.Name, timeExpire)
	if err != nil {
		fmt.Printf("Failed to generate JWT token: %v\n", err)
	} else {
		c.Cookie(&fiber.Cookie{
			Name:     "auth_token",
			Value:    jwtToken,
			Path:     "/",
			MaxAge:   timeExpire,
			HTTPOnly: true,
			Secure:   false,
			SameSite: "Lax",
		})
	}

	// Prepare user data for frontend
	userData := url.Values{}
	userData.Set("id", user.UserID)
	userData.Set("email", user.Email)
	userData.Set("name", user.Name)
	userData.Set("picture", user.AvatarURL)
	userData.Set("provider", user.Provider)
	if jwtToken != "" {
		userData.Set("token", jwtToken)
	}

	// Get frontend URL
	frontendUrl := global.Config.Server.FrontendUrl
	if envUrl := os.Getenv("FRONTEND_URL"); envUrl != "" {
		frontendUrl = envUrl
	}
	if frontendUrl == "" {
		frontendUrl = "http://localhost:5173"
	}

	redirectURL := fmt.Sprintf("%s/auth/callback?%s", frontendUrl, userData.Encode())
	fmt.Printf("Redirecting to frontend: %s\n", redirectURL)

	return c.Redirect().To(redirectURL)
}

func LogoutHandler(c fiber.Ctx) error {
	provider := c.Query("provider", "google")

	httpReq, err := adaptor.ConvertRequest(c, false)
	if err != nil {
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error": "Failed to convert request",
		})
	}

	w := &fiberResponseWriter{ctx: c, headers: make(http.Header)}

	session, err := gothic.Store.Get(httpReq, fmt.Sprintf("%s_%s", gothic.SessionName, provider))
	if err == nil {
		session.Values = make(map[interface{}]interface{})
		session.Options.MaxAge = -1
		session.Save(httpReq, w)

		if cookies := w.headers["Set-Cookie"]; len(cookies) > 0 {
			for _, cookie := range cookies {
				c.Append("Set-Cookie", cookie)
			}
		}
	}

	// Clear auth_token cookie
	c.Cookie(&fiber.Cookie{
		Name:     "auth_token",
		Value:    "",
		MaxAge:   -1,
		Path:     "/",
		HTTPOnly: true,
		Secure:   false,
	})

	return c.JSON(fiber.Map{
		"success": true,
		"message": "Logged out successfully",
	})
}

func GetUserHandler(c fiber.Ctx) error {
	provider := c.Query("provider", "google")

	// Check JWT token first
	authHeader := c.Get("Authorization")
	if authHeader != "" && strings.HasPrefix(authHeader, "Bearer ") {
		token := authHeader[7:]

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

				return c.JSON(fiber.Map{
					"user": fiber.Map{
						"id":       userId,
						"name":     name,
						"email":    email,
						"provider": "google",
						"picture":  "",
					},
				})
			}
		}
	}

	// Fallback to session
	sessionName := fmt.Sprintf("%s_%s", gothic.SessionName, provider)

	httpReq, err := adaptor.ConvertRequest(c, false)
	if err != nil {
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error": "Failed to convert request",
		})
	}

	session, err := gothic.Store.Get(httpReq, sessionName)
	if err != nil {
		c.Cookie(&fiber.Cookie{
			Name:     sessionName,
			Value:    "",
			MaxAge:   -1,
			Path:     "/",
			HTTPOnly: true,
			Secure:   false,
		})
		return c.Status(fiber.StatusUnauthorized).JSON(fiber.Map{
			"error": "Not authenticated - session error",
		})
	}

	authenticated, ok := session.Values["authenticated"].(bool)
	if !ok || !authenticated {
		return c.Status(fiber.StatusUnauthorized).JSON(fiber.Map{
			"error": "Not authenticated",
		})
	}

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

// Response writer adapter
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

func generateJWTToken(userID, email, name string, expiresInSeconds int) (string, error) {
	secretKey := os.Getenv("JWT_SECRET_KEY")
	if secretKey == "" {
		secretKey = os.Getenv("SESSION_SECRET")
	}
	if secretKey == "" {
		secretKey = "default-development-secret-key-change-in-production"
	}

	// Use the provided expiration time in seconds
	expirationTime := time.Now().Add(time.Duration(expiresInSeconds) * time.Second)

	claims := jwt.MapClaims{
		"user_id": userID,
		"email":   email,
		"name":    name,
		"exp":     expirationTime.Unix(),
		"iat":     time.Now().Unix(),
	}

	token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
	return token.SignedString([]byte(secretKey))
}

func ClearSessionsHandler(c fiber.Ctx) error {
	sessionNames := []string{
		"_gothic_session",
		"_gothic_session_google",
		"auth_token",
	}

	for _, name := range sessionNames {
		c.Cookie(&fiber.Cookie{
			Name:     name,
			Value:    "",
			MaxAge:   -1,
			Path:     "/",
			HTTPOnly: true,
			Secure:   false,
		})
	}

	return c.JSON(fiber.Map{
		"message": "Sessions cleared",
		"cleared": sessionNames,
	})
}

func GetOAuthConfigHandler(c fiber.Ctx) error {
	return c.JSON(fiber.Map{
		"callback_url_local":  callbackURLLocal,
		"callback_url_public": callbackURLPublic,
		"selected_callback":   getCallbackURL(c),
		"client_id_set":       googleClientID != "",
	})
}
