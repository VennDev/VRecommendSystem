package kafka

import (
	"context"
	"fmt"
	"go.uber.org/zap"

	"github.com/venndev/vrecommendation/global"
)

type TopicManager struct {
	manager *Manager
}

func NewTopicManager(manager *Manager) *TopicManager {
	return &TopicManager{manager: manager}
}

func (tm *TopicManager) CreateRecommendationTopics(ctx context.Context) error {
	topics := []struct {
		name       string
		partitions int
		retention  int64
	}{
		{"view-events", global.Config.TopicDefaults.Partitions, global.Config.TopicRetention.ViewEvents},
		{"like-events", global.Config.TopicDefaults.Partitions, global.Config.TopicRetention.LikeEvents},
		{"buy-events", global.Config.TopicDefaults.Partitions, global.Config.TopicRetention.BuyEvents},
		{"user-profiles", global.Config.TopicDefaults.Partitions, -1},                        // No retention limit
		{"item-profiles", global.Config.TopicDefaults.Partitions, -1},                        // No retention limit
		{"recommendations", global.Config.TopicDefaults.Partitions, 7 * 24 * 60 * 60 * 1000}, // 7 days
	}

	for _, topic := range topics {
		err := tm.manager.CreateTopic(ctx, topic.name, topic.partitions, global.Config.TopicDefaults.ReplicationFactor)
		if err != nil {
			return fmt.Errorf("failed to create topic %s: %w", topic.name, err)
		}

		global.Logger.Info(
			"Created topic", zap.String("name", topic.name), zap.Int("partitions", topic.partitions),
		)
	}

	return nil
}

// GetRealtimeConsumerGroup trả về consumer group cho realtime processing
func (tm *TopicManager) GetRealtimeConsumerGroup() string {
	return global.Config.ConsumerGroups.Realtime
}

func (tm *TopicManager) GetBatchConsumerGroup() string {
	return global.Config.ConsumerGroups.Batch
}

func (tm *TopicManager) GetAnalyticsConsumerGroup() string {
	return global.Config.ConsumerGroups.Analytics
}
