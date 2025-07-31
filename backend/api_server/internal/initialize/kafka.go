package initialize

import (
	"github.com/venndev/vrecommendation/global"
	"github.com/venndev/vrecommendation/pkg/provider"
	"go.uber.org/zap"
)

func InitKafka() *provider.KafkaManager {
	err := global.Kafka.Initialize()
	if err != nil {
		global.Logger.Fatal("Failed to initialize Kafka", zap.Error(err))
	} else {
		global.Logger.Info("Kafka initialized successfully")
	}

	if err := global.Kafka.ValidateConfig(); err != nil {
		global.Logger.Fatal("Kafka configuration validation failed", zap.Error(err))
	} else {
		global.Logger.Info("Kafka configuration validated successfully")
	}

	// Ensure initialized before creating topics
	if err := global.Kafka.Initialize(); err != nil {
		global.Logger.Fatal("Failed to initialize Kafka manager", zap.Error(err))
	} else {
		global.Logger.Info("Kafka manager initialized successfully")
	}

	err = global.Kafka.CreateAllTopics()
	if err != nil {
		global.Logger.Fatal("Failed to create Kafka topics", zap.Error(err))
	} else {
		global.Logger.Info("Kafka topics created successfully")
	}

	return global.Kafka
}
