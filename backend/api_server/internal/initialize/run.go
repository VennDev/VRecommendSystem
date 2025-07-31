package initialize

import (
	"github.com/venndev/vrecommendation/global"
	"github.com/venndev/vrecommendation/pkg/utils"
)

func Run() {
	// Load Config
	LoadConfig()

	// Initialize Logger
	InitLogger()

	// Initialize Kafka
	kafka := InitKafka()
	defer kafka.Close()

	// Initialize App
	app := InitApp()

	// Initialize Middlewares
	InitMiddlewares(app)

	// Initialize Router
	InitRouter(app)

	// Start the server
	if global.Config.StatusDev == "dev" {
		utils.StartServer(app)
	} else {
		utils.StartServerWithGracefulShutdown(app)
	}
}
