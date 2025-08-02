package initialize

import (
	"github.com/venndev/vrecommendation/global"
	kfcore "github.com/venndev/vrecommendation/pkg/messaging/types"
	"github.com/venndev/vrecommendation/pkg/utils"
)

func Run() {
	// Load Config
	err := LoadConfig()
	if err != nil {
		panic(err)
	}

	// Initialize Logger
	logger := InitLogger()
	defer logger.Close()

	// Initialize Kafka
	manager, _ := InitKafka()
	defer func(manager kfcore.KafkaManager) {
		err := manager.Close()
		if err != nil {
			global.Logger.Error("Failed to close Kafka manager", err)
		} else {
			global.Logger.Info("Kafka manager closed successfully")
		}
	}(manager)

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
