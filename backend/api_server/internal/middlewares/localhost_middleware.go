package middlewares

import (
	"strings"

	"github.com/gofiber/fiber/v3"
	"github.com/venndev/vrecommendation/global"
)

// LocalhostOnlyMiddleware restricts access to localhost only
func LocalhostOnlyMiddleware(c fiber.Ctx) error {
	clientIP := c.IP()

	// Log the access attempt
	global.Logger.Info("Localhost-only endpoint accessed from IP: " + clientIP)

	// Check if IP is localhost
	isLocalhost := isLocalhostIP(clientIP)

	if !isLocalhost {
		global.Logger.Warn("Unauthorized access attempt from non-localhost IP: " + clientIP)
		return c.Status(fiber.StatusForbidden).JSON(fiber.Map{
			"error":   "Access denied",
			"message": "This endpoint is only accessible from localhost",
			"code":    "LOCALHOST_ONLY",
		})
	}

	return c.Next()
}

// isLocalhostIP checks if the given IP is a localhost address
func isLocalhostIP(ip string) bool {
	// Remove port if present
	if strings.Contains(ip, ":") {
		ip = strings.Split(ip, ":")[0]
	}

	// Check common localhost addresses
	localhostAddresses := []string{
		"127.0.0.1",
		"::1",
		"localhost",
		"0.0.0.0",
	}

	for _, localAddr := range localhostAddresses {
		if ip == localAddr {
			return true
		}
	}

	// Check if IP starts with 127. (entire 127.0.0.0/8 range)
	if strings.HasPrefix(ip, "127.") {
		return true
	}

	return false
}

// // DevelopmentOnlyMiddleware restricts access to development environment only
// func DevelopmentOnlyMiddleware(c fiber.Ctx) error {
// 	// Check environment variable
// 	env := global.Config.Environment // Assuming you have this in config
//
// 	if env != "development" && env != "local" {
// 		global.Logger.Warn("Development endpoint accessed in non-dev environment")
// 		return c.Status(fiber.StatusForbidden).JSON(fiber.Map{
// 			"error":   "Access denied",
// 			"message": "This endpoint is only available in development environment",
// 			"code":    "DEVELOPMENT_ONLY",
// 		})
// 	}
//
// 	return c.Next()
// }
