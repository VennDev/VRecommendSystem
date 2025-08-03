package initialize

import (
	"github.com/venndev/vrecommendation/global"
	"github.com/venndev/vrecommendation/pkg/utils"
)

func InitDataHandler() error {
	// Load Config
	err := LoadConfig()
	if err != nil {
		return err
	}

	// Initialize Logger
	logger := InitLogger()
	defer logger.Close()

	// Initialize Kafka
	_, _, err = InitKafka()
	if err != nil {
		return err
	}

	return nil
}

func Run() {
	// Initialize Data Handler
	err := InitDataHandler()
	if err != nil {
		panic("Failed to initialize data handler: " + err.Error())
		return
	}

	// Ensure Kafka manager is closed on exit
	defer func() {
		if global.KafkaManager == nil {
			global.Logger.Error("Kafka manager is nil, cannot close", nil)
			return
		}
		err := global.KafkaManager.Close()
		if err != nil {
			global.Logger.Error("Failed to close Kafka manager", err)
		} else {
			global.Logger.Info("Kafka manager closed successfully")
		}
	}()

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
