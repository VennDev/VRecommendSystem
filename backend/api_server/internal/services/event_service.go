package services

import (
	"context"
	"encoding/json"
	"fmt"
	"github.com/venndev/vrecommendation/internal/event"
	"sync"
	"time"

	"github.com/venndev/vrecommendation/global"
	"github.com/venndev/vrecommendation/pkg/messaging/kafka"
	"go.uber.org/zap"
)

var (
	eventServiceInstance *EventService
	eventServiceOnce     sync.Once
)

func GetEventService() *EventService {
	eventServiceOnce.Do(func() {
		manager, err := kafka.NewManager()
		if err != nil {
			global.Logger.Fatal("Failed to create Kafka manager", zap.Error(err))
		}
		eventServiceInstance = &EventService{
			manager:      manager,
			topicManager: kafka.NewTopicManager(manager),
		}
	})
	return eventServiceInstance
}

// EventService handles event-specific operations
type EventService struct {
	manager      *kafka.Manager
	topicManager *kafka.TopicManager
}

func NewEventService(manager *kafka.Manager) *EventService {
	return &EventService{
		manager:      manager,
		topicManager: kafka.NewTopicManager(manager),
	}
}

// SendEvent sends an event message to the appropriate topic
func (es *EventService) SendEvent(ctx context.Context, event event.Message) error {
	// Validate event type
	if !global.Config.EventTypes.IsEventEnabled(event.EventType) {
		return fmt.Errorf("event type %s is not enabled", event.EventType)
	}

	// Set timestamp if not provided
	if event.Timestamp == 0 {
		event.Timestamp = time.Now().Unix()
	}

	// Serialize event
	eventData, err := json.Marshal(event)
	if err != nil {
		return fmt.Errorf("failed to marshal event: %w", err)
	}

	// Get producer
	producer := es.manager.GetProducer()
	if producer == nil {
		return fmt.Errorf("failed to get producer")
	}

	// Send it to a topic
	topicName := es.manager.GetEventTopicName(event.EventType)
	key := []byte(event.UserID) // Partition by user_id

	headers := map[string][]byte{
		"event_type": []byte(event.EventType),
		"user_id":    []byte(event.UserID),
		"weight":     []byte(fmt.Sprintf("%.2f", global.Config.EventTypes.GetEventWeight(event.EventType))),
	}

	if event.SessionID != "" {
		headers["session_id"] = []byte(event.SessionID)
	}

	if event.DeviceID != "" {
		headers["device_id"] = []byte(event.DeviceID)
	}

	err = producer.SendMessageWithHeaders(ctx, topicName, key, eventData, headers)
	if err != nil {
		global.Logger.Error("Failed to send event",
			err,
			zap.String("event_type", event.EventType),
			zap.String("user_id", event.UserID),
			zap.String("topic", topicName),
		)
		return err
	}

	global.Logger.Debug("Event sent successfully",
		zap.String("event_type", event.EventType),
		zap.String("user_id", event.UserID),
		zap.String("topic", topicName),
	)

	return nil
}

// SendBatchEvents sends multiple events in batch
func (es *EventService) SendBatchEvents(ctx context.Context, events []event.Message) error {
	if len(events) == 0 {
		return nil
	}

	producer := es.manager.GetProducer()
	if producer == nil {
		return fmt.Errorf("failed to get producer")
	}

	var errors []error
	successCount := 0

	for _, ev := range events {
		if err := es.SendEvent(ctx, ev); err != nil {
			errors = append(errors, fmt.Errorf("failed to send event %s for user %s: %w",
				ev.EventType, ev.UserID, err))
		} else {
			successCount++
		}
	}

	global.Logger.Info("Batch events processed",
		zap.Int("total", len(events)),
		zap.Int("success", successCount),
		zap.Int("failed", len(errors)),
	)

	if len(errors) > 0 {
		return fmt.Errorf("batch processing completed with %d errors: %v", len(errors), errors)
	}

	return nil
}

// ConsumeEvents consumes events from specified event types
func (es *EventService) ConsumeEvents(ctx context.Context, eventTypes []string, groupID string) (<-chan event.Message, <-chan error) {
	eventChan := make(chan event.Message, 100)
	errorChan := make(chan error, 10)

	// Validate event types
	var validTopics []string
	for _, eventType := range eventTypes {
		if global.Config.EventTypes.IsEventEnabled(eventType) {
			validTopics = append(validTopics, es.manager.GetEventTopicName(eventType))
		} else {
			global.Logger.Warn("Skipping disabled event type", zap.String("event_type", eventType))
		}
	}

	if len(validTopics) == 0 {
		close(eventChan)
		close(errorChan)
		errorChan <- fmt.Errorf("no valid event types to consume")
		return eventChan, errorChan
	}

	// Get consumer
	consumer := es.manager.GetConsumer(groupID)
	if consumer == nil {
		close(eventChan)
		close(errorChan)
		errorChan <- fmt.Errorf("failed to get consumer")
		return eventChan, errorChan
	}

	// Subscribe to topics
	if err := consumer.Subscribe(validTopics); err != nil {
		close(eventChan)
		close(errorChan)
		errorChan <- fmt.Errorf("failed to subscribe to topics: %w", err)
		return eventChan, errorChan
	}

	// Start consuming
	msgChan, errChan := consumer.Consume(ctx)

	go func() {
		defer close(eventChan)
		defer close(errorChan)

		for {
			select {
			case <-ctx.Done():
				return
			case err := <-errChan:
				if err != nil {
					errorChan <- err
				}
			case msg := <-msgChan:
				if msg.Value == nil {
					continue
				}

				var ev event.Message
				if err := json.Unmarshal(msg.Value, &ev); err != nil {
					errorChan <- fmt.Errorf("failed to unmarshal event: %w", err)
					continue
				}

				select {
				case eventChan <- ev:
				case <-ctx.Done():
					return
				}

				// Auto-commit the message
				if err := consumer.Commit(ctx, msg); err != nil {
					global.Logger.Error("Failed to commit message", err)
				}
			}
		}
	}()

	return eventChan, errorChan
}

// GetEventStats returns statistics for all event types
func (es *EventService) GetEventStats() map[string]event.TypeStats {
	stats := make(map[string]event.TypeStats)

	for eventType, config := range global.Config.EventTypes.EventConfig {
		stats[eventType] = event.TypeStats{
			EventType:   eventType,
			Weight:      config.Weight,
			RetentionMs: config.RetentionMs,
			Partitions:  config.Partitions,
			Enabled:     config.Enabled,
			TopicName:   es.manager.GetEventTopicName(eventType),
		}
	}

	return stats
}

// ValidateEvent validates an event message
func (es *EventService) ValidateEvent(event event.Message) error {
	if event.UserID == "" {
		return fmt.Errorf("user_id is required")
	}

	if event.EventType == "" {
		return fmt.Errorf("event_type is required")
	}

	if !global.Config.EventTypes.IsEventEnabled(event.EventType) {
		return fmt.Errorf("event type %s is not enabled", event.EventType)
	}

	if event.Timestamp < 0 {
		return fmt.Errorf("invalid timestamp: %d", event.Timestamp)
	}

	return nil
}

// CreateEventTopics creates all enabled event topics
func (es *EventService) CreateEventTopics(ctx context.Context) error {
	return es.topicManager.CreateRecommendationTopics(ctx)
}

// GetEnabledEventTypes returns list of enabled event types
func (es *EventService) GetEnabledEventTypes() []string {
	return global.Config.EventTypes.GetEnabledEvents()
}

// GetEventWeight returns the weight for an event type
func (es *EventService) GetEventWeight(eventType string) float64 {
	return global.Config.EventTypes.GetEventWeight(eventType)
}

// GetHighValueEvents returns events with weight >= threshold
func (es *EventService) GetHighValueEvents(threshold float64) []string {
	return es.topicManager.GetHighValueEvents(threshold)
}

// IsEventEnabled checks if an event type is enabled
func (es *EventService) IsEventEnabled(eventType string) bool {
	return global.Config.EventTypes.IsEventEnabled(eventType)
}
