package kafka

import (
	"context"
	"fmt"
	"strings"

	"go.uber.org/zap"

	"github.com/venndev/vrecommendation/global"
)

type TopicManager struct {
	manager *Manager
}

func NewTopicManager(manager *Manager) *TopicManager {
	return &TopicManager{manager: manager}
}

// CreateRecommendationTopics creates all enabled event topics based on configuration
func (tm *TopicManager) CreateRecommendationTopics(ctx context.Context) error {
	enabledEvents := global.Config.EventTypes.GetEnabledEvents()

	for _, eventType := range enabledEvents {
		topicName := tm.buildEventTopicName(eventType)
		partitions := global.Config.EventTypes.GetEventPartitions(eventType)

		err := tm.manager.CreateTopic(ctx, topicName, partitions, global.Config.TopicDefaults.ReplicationFactor)
		if err != nil {
			return fmt.Errorf("failed to create topic %s: %w", topicName, err)
		}

		global.Logger.Info("Created event topic",
			zap.String("event_type", eventType),
			zap.String("topic_name", topicName),
			zap.Int("partitions", partitions),
		)
	}

	// Create system topics (user-profiles, item-profiles, recommendations)
	systemTopics := []struct {
		name       string
		partitions int
		retention  int64
	}{
		{"user-profiles", global.Config.TopicDefaults.Partitions, -1},                        // No retention limit
		{"item-profiles", global.Config.TopicDefaults.Partitions, -1},                        // No retention limit
		{"recommendations", global.Config.TopicDefaults.Partitions, 7 * 24 * 60 * 60 * 1000}, // 7 days
	}

	for _, topic := range systemTopics {
		err := tm.manager.CreateTopic(ctx, topic.name, topic.partitions, global.Config.TopicDefaults.ReplicationFactor)
		if err != nil {
			return fmt.Errorf("failed to create system topic %s: %w", topic.name, err)
		}

		global.Logger.Info("Created system topic",
			zap.String("name", topic.name),
			zap.Int("partitions", topic.partitions),
		)
	}

	return nil
}

// CreateEventTopic creates a single event topic
func (tm *TopicManager) CreateEventTopic(ctx context.Context, eventType string) error {
	if !global.Config.EventTypes.IsEventEnabled(eventType) {
		return fmt.Errorf("event type %s is not enabled", eventType)
	}

	topicName := tm.buildEventTopicName(eventType)
	partitions := global.Config.EventTypes.GetEventPartitions(eventType)

	err := tm.manager.CreateTopic(ctx, topicName, partitions, global.Config.TopicDefaults.ReplicationFactor)
	if err != nil {
		return fmt.Errorf("failed to create topic %s: %w", topicName, err)
	}

	global.Logger.Info("Created event topic",
		zap.String("event_type", eventType),
		zap.String("topic_name", topicName),
		zap.Int("partitions", partitions),
	)

	return nil
}

// DeleteEventTopic deletes a single event topic
func (tm *TopicManager) DeleteEventTopic(ctx context.Context, eventType string) error {
	topicName := tm.buildEventTopicName(eventType)

	err := tm.manager.DeleteTopic(ctx, topicName)
	if err != nil {
		return fmt.Errorf("failed to delete topic %s: %w", topicName, err)
	}

	global.Logger.Info("Deleted event topic",
		zap.String("event_type", eventType),
		zap.String("topic_name", topicName),
	)

	return nil
}

// GetEventTopicName returns the full topic name for an event type
func (tm *TopicManager) GetEventTopicName(eventType string) string {
	return tm.buildEventTopicName(eventType)
}

// GetAllEventTopics returns all configured event topic names
func (tm *TopicManager) GetAllEventTopics() []string {
	enabledEvents := global.Config.EventTypes.GetEnabledEvents()
	topics := make([]string, len(enabledEvents))

	for i, eventType := range enabledEvents {
		topics[i] = tm.buildEventTopicName(eventType)
	}

	return topics
}

// GetEventTypeFromTopic extracts event type from topic name
func (tm *TopicManager) GetEventTypeFromTopic(topicName string) (string, error) {
	prefix := global.Config.Topics.Prefix
	suffix := global.Config.Topics.Suffix

	// Remove prefix
	if prefix != "" && strings.HasPrefix(topicName, prefix) {
		topicName = strings.TrimPrefix(topicName, prefix)
	}

	// Remove suffix
	if suffix != "" && strings.HasSuffix(topicName, suffix) {
		topicName = strings.TrimSuffix(topicName, suffix)
	}

	// Check if this is a valid event type
	if !global.Config.EventTypes.IsEventEnabled(topicName) {
		return "", fmt.Errorf("unknown or disabled event type: %s", topicName)
	}

	return topicName, nil
}

// ValidateEventTypes validates all configured event types
func (tm *TopicManager) ValidateEventTypes() error {
	var errors []string

	for _, eventType := range global.Config.EventTypes.SupportedEvents {
		config, exists := global.Config.EventTypes.EventConfig[eventType]
		if !exists {
			errors = append(errors, fmt.Sprintf("event type %s has no configuration", eventType))
			continue
		}

		if config.Weight < -10 || config.Weight > 10 {
			errors = append(errors, fmt.Sprintf("event type %s has invalid weight: %f", eventType, config.Weight))
		}

		if config.RetentionMs < 0 {
			errors = append(errors, fmt.Sprintf("event type %s has invalid retention: %d", eventType, config.RetentionMs))
		}

		if config.Enabled && config.Partitions <= 0 {
			errors = append(errors, fmt.Sprintf("enabled event type %s has invalid partitions: %d", eventType, config.Partitions))
		}
	}

	if len(errors) > 0 {
		return fmt.Errorf("event type validation failed: %s", strings.Join(errors, "; "))
	}

	return nil
}

// GetRealtimeConsumerGroup returns the realtime consumer group
func (tm *TopicManager) GetRealtimeConsumerGroup() string {
	return global.Config.ConsumerGroups.Realtime
}

// GetBatchConsumerGroup returns the batch consumer group
func (tm *TopicManager) GetBatchConsumerGroup() string {
	return global.Config.ConsumerGroups.Batch
}

// GetAnalyticsConsumerGroup returns the analytics consumer group
func (tm *TopicManager) GetAnalyticsConsumerGroup() string {
	return global.Config.ConsumerGroups.Analytics
}

// Helper method to build event topic name
func (tm *TopicManager) buildEventTopicName(eventType string) string {
	topicName := eventType
	if global.Config.Topics.Prefix != "" {
		topicName = global.Config.Topics.Prefix + topicName
	}
	if global.Config.Topics.Suffix != "" {
		topicName = topicName + global.Config.Topics.Suffix
	}
	return topicName
}

// GetEventWeights returns a map of all event weights
func (tm *TopicManager) GetEventWeights() map[string]float64 {
	weights := make(map[string]float64)
	for eventType := range global.Config.EventTypes.EventConfig {
		weights[eventType] = global.Config.EventTypes.GetEventWeight(eventType)
	}
	return weights
}

// GetHighValueEvents returns events with weight >= threshold
func (tm *TopicManager) GetHighValueEvents(threshold float64) []string {
	var highValueEvents []string
	for eventType, config := range global.Config.EventTypes.EventConfig {
		if config.Enabled && config.Weight >= threshold {
			highValueEvents = append(highValueEvents, eventType)
		}
	}
	return highValueEvents
}

// GetEventsByRetentionPeriod returns events grouped by retention period
func (tm *TopicManager) GetEventsByRetentionPeriod() map[string][]string {
	retentionGroups := make(map[string][]string)

	for eventType, config := range global.Config.EventTypes.EventConfig {
		if config.Enabled {
			retentionKey := fmt.Sprintf("%d_days", config.RetentionMs/(24*60*60*1000))
			retentionGroups[retentionKey] = append(retentionGroups[retentionKey], eventType)
		}
	}

	return retentionGroups
}

