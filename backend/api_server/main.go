package main

import (
	"log"
	"os"

	"github.com/gofiber/fiber/v3"
	"github.com/gofiber/fiber/v3/middleware/cors"
	"github.com/gofiber/fiber/v3/middleware/logger"
	"github.com/joho/godotenv"
	_ "github.com/lib/pq"
	"github.com/venndev/vrecommendation/pkg/configs"
	lg "github.com/venndev/vrecommendation/pkg/logger"
	"github.com/venndev/vrecommendation/pkg/routes"
	"github.com/venndev/vrecommendation/pkg/utils"
)

func main() {
	err := godotenv.Load()
	if err != nil {
		log.Fatal("Error loading .env file")
	}

	fiber_config := configs.FiberConfig()
	server_config := configs.ServerConfig()

	// Initialize logger
	loggerMngr := &lg.Logger{}
	loggerMngr.Init()
	defer loggerMngr.Close()

	// Initialize App
	app := fiber.New(fiber_config)

	// Set up global middlewares
	app.Use(
		cors.New(),
		logger.New(),
	)

	// Initialize public routes
	publicRoutes := &routes.PublicRoutes{
		Logger: loggerMngr,
	}
	publicRoutes.Init(app)

	// Start the server
	if os.Getenv("STAGE_STATUS") == "dev" {
		utils.StartServer(app, server_config, loggerMngr)
	} else {
		utils.StartServerWithGracefulShutdown(app, server_config, loggerMngr)
	}
}
