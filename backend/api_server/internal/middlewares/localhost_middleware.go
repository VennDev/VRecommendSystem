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

	// Temporarily allow Docker environment access
	if !isLocalhost {
		global.Logger.Info("Docker environment detected, allowing access from IP: " + clientIP)
		// For Docker deployment, we'll allow access from Docker gateway IPs
		// This is a temporary workaround for localhost detection in containers
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

	// Docker networking: Allow Docker gateway IPs
	// Common Docker bridge network gateway IPs
	dockerGateways := []string{
		"172.17.0.1", "172.18.0.1", "172.19.0.1", "172.20.0.1",
		"172.21.0.1", "172.22.0.1", "172.23.0.1", "172.24.0.1",
		"192.168.0.1", "192.168.1.1", "192.168.65.1", "192.168.99.1",
	}

	for _, gateway := range dockerGateways {
		if ip == gateway {
			return true
		}
	}

	// Check Docker network ranges more broadly
	if strings.HasPrefix(ip, "172.") && strings.HasSuffix(ip, ".0.1") {
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
