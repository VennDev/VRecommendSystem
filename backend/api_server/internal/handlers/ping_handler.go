package handlers

import (
	"fmt"

	"github.com/gofiber/fiber/v3"
	"github.com/venndev/vrecommendation/global"
)

func PingHandler(c fiber.Ctx) error {
	global.Logger.Info("Received ping request from " + c.IP())
	return c.SendString("pong")
}

func DebugIPHandler(c fiber.Ctx) error {
	clientIP := c.IP()
	host := c.Get("Host")
	userAgent := c.Get("User-Agent")
	xForwardedFor := c.Get("X-Forwarded-For")
	xRealIP := c.Get("X-Real-IP")

	debugInfo := fmt.Sprintf(`Debug IP Information:
- Client IP: %s
- Host Header: %s
- User-Agent: %s
- X-Forwarded-For: %s
- X-Real-IP: %s
- All Headers: %v`,
		clientIP, host, userAgent, xForwardedFor, xRealIP, c.GetReqHeaders())

	global.Logger.Info("Debug IP request: " + debugInfo)

	return c.JSON(fiber.Map{
		"client_ip":       clientIP,
		"host":            host,
		"user_agent":      userAgent,
		"x_forwarded_for": xForwardedFor,
		"x_real_ip":       xRealIP,
		"all_headers":     c.GetReqHeaders(),
		"is_docker":       clientIP == "172.18.0.1" || clientIP == "172.17.0.1",
	})
}
