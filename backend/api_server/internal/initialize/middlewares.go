package initialize

import (
	"fmt"
	"os"
	"strconv"
	"strings"

	"github.com/gofiber/fiber/v3"
	"github.com/gofiber/fiber/v3/middleware/cors"
	"github.com/gofiber/fiber/v3/middleware/logger"
	"github.com/venndev/vrecommendation/global"
)

func InitMiddlewares(app *fiber.App) {
	// Get configuration from config file or environment variables
	frontendUrl := global.Config.Server.FrontendUrl
	if envUrl := os.Getenv("FRONTEND_URL"); envUrl != "" {
		frontendUrl = envUrl
	}

	// Build API server URL from config
	apiHost := global.Config.Server.Host
	if envHost := os.Getenv("HOST_ADDRESS"); envHost != "" {
		apiHost = envHost
	}

	apiPort := global.Config.Server.Port
	if envPort := os.Getenv("HOST_PORT"); envPort != "" {
		if port, err := strconv.Atoi(envPort); err == nil {
			apiPort = port
		}
	}

	// Get HOST_IP from environment for LAN access
	hostIP := os.Getenv("HOST_IP")

	// Build allowed origins list
	allowedOrigins := []string{
		frontendUrl,                                   // Primary frontend URL from config
		"http://localhost:5173",                       // Frontend on localhost
		"http://127.0.0.1:5173",                       // Frontend on 127.0.0.1
		"http://localhost:3000",                       // Alternative frontend port
		fmt.Sprintf("http://localhost:%d", apiPort),   // API server on localhost
		fmt.Sprintf("http://127.0.0.1:%d", apiPort),   // API server on 127.0.0.1
		fmt.Sprintf("http://%s:%d", apiHost, apiPort), // API server with configured host
	}

	// Add LAN IP origins if HOST_IP is set
	if hostIP != "" && hostIP != "localhost" && hostIP != "127.0.0.1" {
		allowedOrigins = append(allowedOrigins,
			fmt.Sprintf("http://%s:5173", hostIP),        // Frontend on LAN IP
			fmt.Sprintf("http://%s:%d", hostIP, apiPort), // API on LAN IP
			fmt.Sprintf("http://%s:9999", hostIP),        // AI Server on LAN IP
		)
	}

	// Add common LAN IP patterns (192.168.x.x, 10.x.x.x, 172.16-31.x.x)
	// This allows any device on common private networks
	allowedOrigins = append(allowedOrigins,
		"http://192.168.*:5173",
		"http://192.168.*:2030",
		"http://192.168.*:9999",
		"http://10.*:5173",
		"http://10.*:2030",
		"http://10.*:9999",
	)

	// Add custom allowed origins from environment variable
	// Format: ALLOWED_ORIGINS=http://example.com:5173,https://app.example.com
	if customOrigins := os.Getenv("ALLOWED_ORIGINS"); customOrigins != "" {
		for _, origin := range strings.Split(customOrigins, ",") {
			origin = strings.TrimSpace(origin)
			if origin != "" {
				allowedOrigins = append(allowedOrigins, origin)
			}
		}
	}

	global.Logger.Info(fmt.Sprintf("CORS Allowed Origins: %v", allowedOrigins))

	// Configure CORS with dynamic origin validation
	app.Use(cors.New(cors.Config{
		AllowOriginsFunc: func(origin string) bool {
			// Allow all localhost variations
			if strings.HasPrefix(origin, "http://localhost") ||
				strings.HasPrefix(origin, "http://127.0.0.1") ||
				strings.HasPrefix(origin, "https://localhost") ||
				strings.HasPrefix(origin, "https://127.0.0.1") {
				return true
			}

			// Allow private network IPs (LAN)
			// 192.168.x.x
			if strings.HasPrefix(origin, "http://192.168.") ||
				strings.HasPrefix(origin, "https://192.168.") {
				return true
			}

			// 10.x.x.x
			if strings.HasPrefix(origin, "http://10.") ||
				strings.HasPrefix(origin, "https://10.") {
				return true
			}

			// 172.16.x.x - 172.31.x.x
			if strings.HasPrefix(origin, "http://172.") ||
				strings.HasPrefix(origin, "https://172.") {
				// Extract the second octet
				parts := strings.Split(strings.TrimPrefix(strings.TrimPrefix(origin, "https://"), "http://"), ".")
				if len(parts) >= 2 {
					if secondOctet, err := strconv.Atoi(parts[1]); err == nil {
						if secondOctet >= 16 && secondOctet <= 31 {
							return true
						}
					}
				}
			}

			// Check against static allowed origins (exact match)
			for _, allowed := range allowedOrigins {
				if origin == allowed {
					return true
				}
			}

			// Check if origin matches any custom domain patterns
			// This allows for DDNS domains like vennv.ddns.net
			if customOrigins := os.Getenv("ALLOWED_ORIGINS"); customOrigins != "" {
				for _, allowed := range strings.Split(customOrigins, ",") {
					allowed = strings.TrimSpace(allowed)
					if allowed != "" {
						// Extract domain from allowed origin (remove protocol and port)
						allowedDomain := strings.Split(strings.TrimPrefix(strings.TrimPrefix(allowed, "https://"), "http://"), ":")[0]
						// Extract domain from request origin
						originDomain := strings.Split(strings.TrimPrefix(strings.TrimPrefix(origin, "https://"), "http://"), ":")[0]

						if allowedDomain == originDomain {
							return true
						}
					}
				}
			}

			// Log rejected origins for debugging
			global.Logger.Warn(fmt.Sprintf("CORS rejected origin: %s", origin))
			return false
		},
		AllowMethods: []string{
			"GET",
			"POST",
			"PUT",
			"DELETE",
			"OPTIONS",
			"PATCH",
			"HEAD",
		},
		AllowHeaders: []string{
			"Origin",
			"Content-Type",
			"Accept",
			"Authorization",
			"X-Requested-With",
			"Access-Control-Request-Method",
			"Access-Control-Request-Headers",
		},
		ExposeHeaders: []string{
			"Content-Length",
			"Content-Type",
			"Authorization",
		},
		AllowCredentials: true,
		MaxAge:           86400, // 24 hours
	}))

	app.Use(logger.New())
}
