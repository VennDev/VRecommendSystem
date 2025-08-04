package main

import (
	"github.com/joho/godotenv"
	_ "github.com/lib/pq"
	"github.com/venndev/vrecommendation/internal/initialize"
	"github.com/venndev/vrecommendation/pkg/utils"
	"log"
	"os"
)

func main() {
	// Load environment variables from .env file
	err := godotenv.Load()
	if err != nil {
		log.Fatal("Error loading .env file")
	}

	// Load Config
	err = initialize.LoadConfig()
	if err != nil {
		panic(err)
	}

	// Initialize Logger
	logger := initialize.InitLogger()
	defer logger.Close()

	// Initialize App
	app := initialize.InitApp()

	// Initialize Middlewares
	initialize.InitMiddlewares(app)

	// Initialize Router
	initialize.InitRouter(app)

	// Start the server
	if os.Getenv("STATUS_DEV") == "dev" {
		utils.StartServer(app)
	} else {
		utils.StartServerWithGracefulShutdown(app)
	}
}
