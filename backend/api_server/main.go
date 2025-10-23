package main

import (
	"log"
	"os"

	"github.com/joho/godotenv"
	_ "github.com/lib/pq"
	"github.com/venndev/vrecommendation/internal/initialize"
	"github.com/venndev/vrecommendation/pkg/utils"
)

func main() {
	// Load environment variables from .env file (optional)
	err := godotenv.Load()
	if err != nil {
		log.Println("Warning: .env file not found, using environment variables")
	}

	// Load Config
	err = initialize.LoadConfig()
	if err != nil {
		panic(err)
	}

	// Initialize Logger
	logger := initialize.InitLogger()
	defer logger.Close()

	// Initialize OAuth
	initialize.InitOAuth()

	// Initialize Redis
	err = initialize.InitRedis()
	if err != nil {
		panic(err)
	}

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
