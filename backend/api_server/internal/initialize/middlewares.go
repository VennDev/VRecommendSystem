package initialize

import (
	"fmt"
	"os"
	"strconv"

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

	// Build allowed origins list
	allowedOrigins := []string{
		frontendUrl,             // Primary frontend URL from config
		"http://localhost:3000", // Alternative frontend port
		fmt.Sprintf("http://localhost:%d", apiPort),   // API server on localhost
		fmt.Sprintf("http://127.0.0.1:%d", apiPort),   // API server on 127.0.0.1
		fmt.Sprintf("http://%s:%d", apiHost, apiPort), // API server with configured host
	}

	// Configure CORS to allow credentials (cookies)
	app.Use(cors.New(cors.Config{
		AllowOrigins: allowedOrigins,
		AllowMethods: []string{
			"GET",
			"POST",
			"PUT",
			"DELETE",
			"OPTIONS",
		},
		AllowHeaders: []string{
			"Origin",
			"Content-Type",
			"Accept",
			"Authorization",
		},
		AllowCredentials: true,
	}))

	app.Use(logger.New())
}
