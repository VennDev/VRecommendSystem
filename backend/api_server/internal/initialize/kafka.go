package initialize

import (
	"context"
	"github.com/venndev/vrecommendation/global"
	"github.com/venndev/vrecommendation/internal/services"
	svcore "github.com/venndev/vrecommendation/internal/services/core"
	kfcore "github.com/venndev/vrecommendation/pkg/messaging/core"
	"github.com/venndev/vrecommendation/pkg/messaging/kafka"
	"go.uber.org/zap"
	"time"
)

func InitKafka() (kfcore.KafkaManager, svcore.EventService) {
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	manager, err := kafka.NewManager()
	if err != nil {
		global.Logger.Fatal("Failed to create Kafka manager", zap.Error(err))
	}

	err = manager.HealthCheck(ctx)
	if err != nil {
		global.Logger.Fatal("Kafka health check failed", zap.Error(err))
	}

	service := services.NewEventService(manager)
	topicManager := kafka.NewTopicManager(manager)

	err = topicManager.ValidateEventTypes()
	if err != nil {
		global.Logger.Fatal("Event types validation failed", zap.Error(err))
	}

	err = service.CreateEventTopics(ctx)
	if err != nil {
		global.Logger.Warn("Failed to create event topics", zap.Error(err))
	}

	enabledEvents := service.GetEnabledEventTypes()
	global.Logger.Info("Kafka initialization completed",
		zap.Strings("enabled_events", enabledEvents),
		zap.Int("total_event_types", len(enabledEvents)),
	)

	global.KafkaManager = manager
	global.EventService = service

	return global.KafkaManager, global.EventService
}
